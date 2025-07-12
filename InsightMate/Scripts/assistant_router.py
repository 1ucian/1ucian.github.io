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
from dotenv import load_dotenv
from config import load_config, get_api_key, get_llm, get_prompt

from gmail_reader import search_emails
from calendar_reader import (
    list_events_for_day,
    list_events_for_range,
)
from dateparser import parse as parse_date
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


def _is_relevant(prior: dict, query: str) -> bool:
    """Return True if user query mentions keywords from prior tool output."""
    if not prior:
        return False
    text = json.dumps(prior).lower()[:800]
    tokens = [w for w in query.lower().split() if len(w) > 3][:4]
    return any(t in text for t in tokens)

FOLLOW_UP_KEYWORDS = {"all of them", "entire week", "titles", "summarize", "readable"}

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
    "chat": lambda a: gpt(a.get("prompt", "Say hello"), a.get("model", _load_model()))
}

load_dotenv()



def _get_config():
    return load_config()


def plan_actions(user_prompt: str, model: str) -> list[dict]:
    """Map the user's prompt to a list of tool actions."""
    planning_prompt = (
        "You are a planner. Convert the user’s message into a JSON list of tools.\n"
        "\n"
        "Available tools:\n"
        "- search_email        { \"type\": \"search_email\", \"query\": \"<keywords>\" }\n"
        "- get_calendar        { \"type\": \"get_calendar\", \"date\": \"<date>\" }\n"
        "- get_calendar_range  { \"type\": \"get_calendar_range\", \"start\": \"<start>\", \"end\": \"<end>\" }\n"
        "- summarize           { \"type\": \"summarize\" }\n"
        "- chat                { \"type\": \"chat\" }\n"
        "\n"
        "RULES:\n"
        "1. Think from the user text only; no hard-coded commands.\n"
        "2. Return 1-3 tools. If nothing fits, return [ {\"type\":\"chat\"} ].\n"
        "3. Output **only** the JSON list, no commentary.\n"
        "- If user says \"today's emails\": {\"type\":\"search_email\",\"query\":\"today\"}\n"
        "- If user says \"emails from <keyword>\": use that exact keyword.\n"
        "- If user asks \"calendar this week\": {\"type\":\"get_calendar_range\",\"start\":\"today\",\"end\":\"+7d\"}\n"
        "\n"
        "User message:\n"
        f"{user_prompt}"
    )

    response = chat_completion(
        model,
        [
            {"role": "system", "content": "You're a smart assistant planner."},
            {"role": "user", "content": planning_prompt},
        ],
    )

    import re, json
    match = re.search(r"\[[\s\S]+?]", response)
    if not match:
        log_path = os.path.join("logs", f"planner_{int(time.time())}.txt")
        try:
            os.makedirs("logs", exist_ok=True)
            with open(log_path, "w") as f:
                f.write(response)
        except Exception:
            pass
        logging.error("No JSON block found in planner output. Saved to %s", log_path)
        if response.strip().startswith("\u26a0\ufe0f"):
            return [{"type": "chat", "prompt": response}]
        return [{"type": "chat", "prompt": "I'm not sure what to do. Can you clarify?"}]

    try:
        return json.loads(match.group(0))
    except Exception as e:
        log_path = os.path.join("logs", f"planner_{int(time.time())}.txt")
        try:
            os.makedirs("logs", exist_ok=True)
            with open(log_path, "w") as f:
                f.write(match.group(0))
        except Exception:
            pass
        logging.error("Failed to parse planner JSON: %s. Saved to %s", e, log_path)
        return [{"type": "chat", "prompt": "Invalid plan format."}]




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
    selected_model = model or _load_model()
    prompt_clean = user_prompt.lower().strip()

    # Casual conversation fallback
    if prompt_clean in ["hi", "hello", "hey", "how are you", "yo", "what's up", "good afternoon"]:
        return chat_completion(selected_model, [{"role": "user", "content": user_prompt}])

    if last_tool_output and prompt_clean in FOLLOW_UP_KEYWORDS:
        if "email" in last_tool_output:
            emails = last_tool_output["email"]
            if "titles" in prompt_clean:
                return "\n".join(e.get("subject", "") for e in emails)
            if "summarize" in prompt_clean or "readable" in prompt_clean:
                return summarize_text(emails)
            return format_results({"email": emails})
        if "calendar" in last_tool_output:
            events = last_tool_output["calendar"]
            if "summarize" in prompt_clean:
                return summarize_text(events)
            return format_results({"calendar": events})

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
    if "suggest" in reflection.lower():
        revised = plan_actions(reflection, selected_model)
        if revised:
            actions = revised

    if not actions:
        return "\u26a0\ufe0f I couldn't determine what action to take."

    results = {}

    for action in actions:
        action_type = action.get("type")
        action["model"] = selected_model
        if action_type in TOOL_REGISTRY:
            try:
                results[action_type] = TOOL_REGISTRY[action_type](action)
            except Exception as e:
                results[action_type] = f"\u26a0\ufe0f Tool error: {str(e)}"
        else:
            results[action_type] = "\u26a0\ufe0f Unknown action type"

    last_tool_output.update(results)
    reply = format_results(results)
    if reply.lower().startswith("chat:"):
        reply = reply.split(":", 1)[1].lstrip()
    return reply


def format_results(results):
    lines = []
    for t, v in results.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    title = item.get("subject") or item.get("title")
                    when = item.get("start") or ""
                    snippet = item.get("snippet", "")[:120]
                    lines.append(f"\u2022 {title} {when} — {snippet}")
                else:
                    lines.append(f"\u2022 {item}")
        elif isinstance(v, dict):
            title = v.get("title") or v.get("subject")
            when = v.get("start") or ""
            lines.append(f"\u2022 {title} {when}")
        else:
            lines.append(str(v))
    return "\n".join(lines)


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
