import os
import subprocess
import datetime
from typing import Optional
import requests
import openai
import json
import difflib
import logging
import time
import re
from dotenv import load_dotenv
from config import load_config, get_api_key, get_llm, get_prompt

from gmail_reader import search_emails
from calendar_reader import (
    list_events_for_day,
    list_events_for_range,
    create_event,
)
from dateparser import parse as parse_date
from date_utils import date_keyword, today_pt
from reminder_scheduler import (
    schedule as schedule_reminder,
    schedule_air_quality,
    schedule_weather,
    schedule_email,
    schedule_calendar,
    list_reminders,
    list_tasks,
)
from action_executor import execute as execute_action
from memory_db import (
    save_message,
    get_recent_messages,
)
from summarizer import summarize_text
from llm_client import chat_completion, gpt
from server_common import _load_model
from user_settings import get_selected_model


def _is_relevant(prior: dict, query: str) -> bool:
    """Return True if user query mentions keywords from prior tool output."""
    if not prior:
        return False
    text = json.dumps(prior).lower()[:800]
    tokens = [w for w in query.lower().split() if len(w) > 3][:4]
    return any(t in text for t in tokens)

FOLLOW_UPS = {
    "titles",
    "summarize",
    "summary",
    "paragraph",
    "readable",
    "all of them",
    "entire week",
    "what about yesterday",
    "yesterday",
}

last_tool_output = {}

TOOL_REGISTRY = {
    "search_email": lambda a: search_emails(a.get("query") or "today"),
    "get_calendar": lambda a: list_events_for_day(
        parse_date(a.get("date", "today")).strftime("%Y-%m-%d")
    ) if parse_date(a.get("date", "today")) else "\u26a0\ufe0f Invalid date",
    "get_calendar_range": lambda a: list_events_for_range(
        a.get("start"), a.get("end")
    ),
    "summarize": lambda a: summarize_text(
        last_tool_output.get(
            a.get("source") or next(iter(last_tool_output), None),
            "\u26a0\ufe0f No previous tool output"
        )
    ),
    "chat": lambda a: gpt(a.get("prompt", ""), a["model"]),
    "schedule_event": lambda a: _schedule(a)
}

def _schedule(a):
    date_str = a.get("date")
    when = a.get("time", "17:00")
    if date_str:
        parsed = parse_date(date_str)
        if parsed:
            date = parsed.date()
        else:
            date = today_pt()
    else:
        date = today_pt()
    title = a.get("title", "Appointment")
    return create_event(f"{title} {date} {when}")

load_dotenv()



def _get_config():
    return load_config()


def plan_actions(user_prompt: str, model: str) -> list[dict]:
    """Map the user's prompt to a list of tool actions."""
    planning_prompt = (
        "You are a tool-planning agent. For the **user message** below, output a VALID JSON list (no commentary) of 1-N actions.\n"
        "Available tools:\n"
        "- search_email  {{ \"query\": \"<keywords>\" }}\n"
        "- get_calendar   {{ \"date\": \"<YYYY-MM-DD|today|yesterday>\" }}\n"
        "- get_calendar_range {{ \"start\": \"<YYYY-MM-DD|today>\", \"end\": \"<YYYY-MM-DD|+7d>\" }}\n"
        "- schedule_event {{ \"title\":\"<text>\", \"time\":\"<HH:MM>\" }}\n"
        "- summarize      {{ \"source\":\"email|calendar\" }}\n"
        "Output JSON **must** use the key \"type\" (not \"tool\" or \"action\").\n"
        "Rules:\n"
        "• If user says “today / yesterday / tomorrow”, map to exact dates in Pacific Time (UTC-07).\n"
        "• If user adds an event like “add 5 pm dinner”, emit **schedule_event**.\n"
        "• If user says “change 5 pm today”, emit get_calendar + schedule_event (update).\n"
        "• If user asks follow-up (“titles”, “summary”, “all of them”), emit summarize.\n"
        "• If user says \"list calendar\" or \"calendar events today\":\n  output [{ \"type\":\"get_calendar\",\"date\":\"today\" }]\n"
        "• If user says \"list emails\" or \"emails today\":\n  output [{ \"type\":\"search_email\", \"query\": \"today\" }]\n\n"
        "Only output the JSON array. No <think> tags.\n"
        "User message:\n{msg}\n"
    ).format(msg=user_prompt.replace('{', '[').replace('}', ']'))

    response = chat_completion(
        model,
        [
            {"role": "system", "content": "You're a smart assistant planner."},
            {"role": "user", "content": planning_prompt},
        ],
    )

    import re, json
    match = re.search(r"\[[\s\S]*?]", response)
    if not match:
        print("\u26a0\ufe0f Planner returned no JSON. Raw:", response[:300])
        return [{"type": "chat", "prompt": "I’m not sure what to do. Can you clarify?"}]

    try:
        plan = json.loads(match.group(0))
    except Exception as e:
        print("\u26a0\ufe0f Failed to parse planner JSON:", e)
        return [{"type": "chat", "prompt": "Planning error."}]

    if isinstance(plan, dict):
        plan = [plan]
    if not isinstance(plan, list):
        return [{"type": "chat"}]

    out = []
    for a in plan:
        if not isinstance(a, dict):
            continue
        a = _normalise(a)
        if "type" in a:
            out.append(a)
    return out


def _normalise(action: dict) -> dict:
    """Ensure planner actions use the 'type' key and clean stray quotes."""
    cleaned = {}
    for k, v in action.items():
        key = k.strip().strip('"').strip("'")
        cleaned[key] = v
    action = cleaned
    if "type" in action:
        return action
    if "tool" in action:
        action["type"] = action.pop("tool")
    elif "action" in action:
        action["type"] = action.pop("action")
    return action




def _get_location() -> str:
    lat = os.getenv('LATITUDE')
    lon = os.getenv('LONGITUDE')
    if lat and lon:
        return f'{lat}, {lon}'
    try:
        resp = requests.get('https://ipapi.co/json', timeout=5)
        data = resp.json()
        city = data.get('city', '')
        region = data.get('region', '')
        country = data.get('country_name', '')
        coords = f"{data.get('latitude')},{data.get('longitude')}" if data.get('latitude') and data.get('longitude') else ''
        loc = ', '.join(filter(None, [city, region, country]))
        return f"{loc} ({coords})" if coords else loc
    except Exception:
        return 'Location not available.'


def _run_python(code: str) -> str:
    try:
        out = subprocess.check_output(['python', '-c', code], stderr=subprocess.STDOUT, timeout=10)
        return out.decode().strip() or 'Done.'
    except subprocess.CalledProcessError as e:
        return e.output.decode().strip()
    except Exception as e:
        return str(e)




def gpt(prompt: str, model: str | None = None, cot_mode: bool = False) -> str:
    """Return an LLM reply using ``model`` or the configured default."""
    cfg = _get_config()
    llm = (model or get_llm(cfg)).lower()
    api_key = get_api_key(cfg)
    if cot_mode:
        system_prompt = (
            "You are InsightMate. Think step by step, plan your actions, then "
            "execute them. Do not repeat your reasoning. Only respond once. "
            "Keep response short unless told otherwise."
        )
    else:
        system_prompt = "You are InsightMate. Respond concisely and act immediately."
    history = get_recent_messages(10)
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["assistant"]})
    messages.append({"role": "user", "content": prompt})
    if llm in {"gpt-4", "gpt-4o", "o4-mini", "o4-mini-high"}:
        if not api_key:
            return "OpenAI API key missing."
        openai.api_key = api_key
        if llm == "gpt-4o":
            llm_name = "gpt-4o"
        elif llm == "gpt-4":
            llm_name = "gpt-4"
        else:
            llm_name = llm
        return chat_completion(llm_name, messages)
    llm_name = llm if llm else _load_model()
    return chat_completion(llm_name, messages)


def _analysis_loop(prompt: str, plan: str, rounds: int = 3, model: str | None = None) -> str:
    """Run a brief recurring analysis loop to refine the plan."""
    notes: list[str] = []
    for _ in range(rounds):
        context = "\n".join(notes)
        step = gpt(
            "You are analyzing the user's request. "
            "Consider the plan and any notes so far, then provide a short "
            "update in 1-3 sentences. If you are satisfied with the reasoning, "
            "start your reply with 'DONE:'.\n\n" +
            f"Plan:\n{plan}\n\nNotes:\n{context}\n\nQuestion: {prompt}",
            model=model
        )
        notes.append(step)
        if step.strip().upper().startswith("DONE:"):
            break
    return "\n".join(notes)


def generate_response(user_prompt: str, data: dict, cot_mode: bool) -> str:
    """Create the final reply using the gathered ``data``."""
    prompt = (
        f"User request: {user_prompt}\n\nResults:\n{json.dumps(data, indent=2)}\n\n"
        "Provide a helpful answer summarizing any important information."
    )
    return gpt(prompt, cot_mode=cot_mode)



def plan_then_answer(user_prompt: str, model: str | None = None):
    """Plan actions for ``user_prompt`` then execute them."""
    global last_tool_output
    selected_model = get_selected_model()
    prompt_clean = user_prompt.lower().strip()


    FOLLOW = prompt_clean
    if last_tool_output and FOLLOW in {"titles", "all of them", "entire week"}:
        if "email" in last_tool_output:
            emails = last_tool_output["email"]
            if "titles" in FOLLOW:
                return "\n".join(e["subject"] for e in emails)
            return summarize_text(emails)
        if "calendar" in last_tool_output:
            events = last_tool_output["calendar"]
            return summarize_text(events)

    if last_tool_output and prompt_clean.startswith(("summarize", "summary")):
        for key in ("email", "search_email", "calendar", "get_calendar"):
            if key in last_tool_output:
                return summarize_text(last_tool_output[key])
        return "\u26a0\ufe0f Nothing to summarize."

    # Casual conversation fallback
    if prompt_clean in ["hi", "hello", "hey", "how are you", "yo", "what's up", "good afternoon"]:
        return chat_completion(selected_model, [{"role": "user", "content": user_prompt}])

    # ---- THINK stage ---------------------------------------------------
    thought = chat_completion(
        selected_model,
        [
            {"role": "system", "content": "You are reasoning internally. Explain (in ONE short sentence) what you will do next."},
            {"role": "user", "content": user_prompt},
        ],
    )
    logging.info("THOUGHT %s", thought)

    # Clean context if irrelevant
    if not _is_relevant(last_tool_output, user_prompt):
        last_tool_output = {}

    context_hint = ""
    if last_tool_output:
        context_hint = f"\n\nLast tool result:\n{json.dumps(last_tool_output)[:1000]}"

    try:
        actions = plan_actions(user_prompt + context_hint, selected_model)
    except Exception as e:
        return f"\u26a0\ufe0f Planning failed: {e}"
    logging.info("PLAN %s", actions)
    actions = [_normalise(a) for a in actions]

    for a in actions:
        if "type" not in a:
            return "\u26a0\ufe0f Planner output lacked 'type'. Please retry."

    if actions == [{"type": "chat"}]:
        return "\u26a0\ufe0f I couldn't find any relevant action. Try rephrasing."

    reflection = chat_completion(
        selected_model,
        [
            {
                "role": "system",
                "content": "You are an assistant thinking about whether the planned actions make sense.",
            },
            {
                "role": "user",
                "content": f"User: {user_prompt}\nPlanned actions: {actions}\nRespond with either 'PROCEED' or suggest a better plan.",
            },
        ],
    )
    if reflection.lower().startswith("<think"):
        reflection = "PROCEED"
    if "suggest" in reflection.lower():
        revised = plan_actions(reflection, selected_model)
        if revised:
            actions = revised

    if not actions:
        return "\u26a0\ufe0f I couldn't determine what action to take."

    results = {}

    for action in actions:
        if action.get("type") == "chat":
            action.setdefault("prompt", user_prompt)
        t = action.get("type")
        action["model"] = selected_model
        if t not in TOOL_REGISTRY:
            results[t] = f"\u26a0\ufe0f Unknown tool '{t}'"
            continue
        try:
            out = TOOL_REGISTRY[t](action)
            results[t] = out

            # store unified aliases for follow-ups
            if t == "search_email":
                results["email"] = out
            if t in {"get_calendar", "get_calendar_range"}:
                results["calendar"] = out
        except Exception as e:
            results[t] = f"\u26a0\ufe0f {t} error: {e}"

    logging.info("RESULT KEYS %s", list(results.keys()))

    last_tool_output = results
    reply_text = format_results(results)
    if not reply_text:
        reply_text = "\u2139\ufe0f No data returned."
    return reply_text


def format_results(res):
    out = []
    for k, v in res.items():
        if isinstance(v, list):
            for item in v:
                subj = item.get("subject") or item.get("title", "")
                when = item.get("start", "")[:16]
                out.append(f"\u2022 {subj} {when}")
        elif isinstance(v, dict):
            subj = v.get("subject") or v.get("title", "")
            when = v.get("start", "")[:16]
            out.append(f"\u2022 {subj} {when}")
        else:
            out.append(str(v))
    return "\n".join(out)


def _extract_minutes(text: str) -> Optional[int]:
    import re
    match = re.search(r'(\d+)\s*(minute|hour)', text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        return value * 60 if unit.startswith('hour') else value
    if 'hour' in text:
        return 60
    if 'day' in text:
        return 60 * 24
    return None


def route(query: str) -> str:
    selected_model = _load_model()
    cot_mode = False
    q = query.lower()
    if "/think" in q:
        cot_mode = True
        query = query.replace("/think", "").strip()
        q = query.lower()
    reply = ''

    if q in ["hi", "hello", "hey", "how are you", "yo", "what's up", "good afternoon"]:
        reply = chat_completion(selected_model, [{"role": "user", "content": query}])
    elif 'remind me' in q or q.startswith('remind'):
        reply = schedule_reminder(query)
    elif 'air quality' in q:
        reply = schedule_air_quality(query)
    elif 'schedule weather' in q or 'weather every' in q:
        mins = _extract_minutes(q)
        if mins:
            reply = schedule_weather(mins)
        else:
            reply = 'Could not parse interval.'
    elif 'schedule email' in q or 'email every' in q:
        mins = _extract_minutes(q)
        if mins:
            reply = schedule_email(mins)
        else:
            reply = 'Could not parse interval.'
    elif 'schedule calendar' in q or 'calendar every' in q:
        mins = _extract_minutes(q)
        if mins:
            reply = schedule_calendar(mins)
        else:
            reply = 'Could not parse interval.'
    elif 'list reminders' in q or 'show reminders' in q:
        rems = list_reminders()
        if not rems:
            reply = 'No reminders set.'
        else:
            lines = [f"{r[2]} - {r[1]}" for r in rems]
            reply = '\n'.join(lines)
    elif 'list tasks' in q or 'show tasks' in q:
        tasks = list_tasks()
        if not tasks:
            reply = 'No tasks scheduled.'
        else:
            lines = [f"{t[3]} - {t[1]}" for t in tasks]
            reply = '\n'.join(lines)
    elif 'show memory' in q or 'view memory' in q or 'show history' in q:
        mem = get_recent_messages()
        if not mem:
            reply = 'No memory.'
        else:
            lines = [f"User: {m['user']}\nAssistant: {m['assistant']}" for m in mem]
            reply = '\n'.join(lines)
    elif 'where am i' in q or 'my location' in q or q.startswith('location'):
        reply = _get_location()
    elif 'current time' in q or q.startswith('what time') or q == 'time':
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reply = f'The current time is {now}'
    elif q.startswith('run python'):
        code = query[len('run python'):].strip()
        if not code:
            reply = 'Please provide Python code to run.'
        else:
            reply = _run_python(code)
    elif 'open' in q or 'launch' in q or 'play' in q:
        reply = execute_action(query)
    else:
        if q.startswith(("search email", "get calendar", "list events")):
            reply = (
                "\u2139\ufe0f Please phrase your request naturally (e.g. "
                "\"Show me today's emails\" or "
                "\"What's on my calendar this week?\")"
            )
        else:
            reply = plan_then_answer(query)
    save_message(query, reply)
    return reply
