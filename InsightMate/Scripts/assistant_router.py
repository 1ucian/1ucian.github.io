import os
import subprocess
import datetime
from typing import Optional
import requests
import openai
import json
from dotenv import load_dotenv
from config import load_config, get_api_key, get_llm, get_prompt

from onedrive_reader import search, list_word_docs
from gmail_reader import (
    fetch_unread_email,
    search_emails,
    send_email,
    read_email,
)
from calendar_reader import (
    list_today_events,
    list_events_for_day,
    search_events,
    create_event,
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
    save_email,
    save_calendar_events,
    get_recent_messages,
)
from summarizer import summarize_text
from llm_client import chat_completion
from llm_client import gpt as simple_gpt
from user_settings import get_selected_model

last_tool_output = {}

TOOL_REGISTRY = {
    "search_email": lambda a: search_emails(a.get("query", "")),
    "get_calendar": lambda a: (
        list_events_for_day(parse_date(a.get("date", "today")).strftime("%Y-%m-%d"))
        if parse_date(a.get("date", "today")) else "\u26a0\ufe0f Invalid date"
    ),
    "summarize": lambda a: summarize_text(
        last_tool_output.get(
            a.get("source") or next(iter(last_tool_output), None),
            "\u26a0\ufe0f No previous tool output"
        )
    ),
    "schedule_event": lambda a: create_event(
        f"{a.get('title', 'Appointment')} {a.get('time', '21:00')}"
    ),
    "chat": lambda a: simple_gpt(a.get("prompt", "Say hello"), a.get("model", "qwen:30b-a3b"))
}

load_dotenv()



def _get_config():
    return load_config()


def plan_actions(user_prompt: str, model: str) -> list[dict]:
    reasoning_mode = False
    if "explain" in user_prompt.lower() or "how did you decide" in user_prompt.lower():
        reasoning_mode = True

    planning_prompt = f"""You are an AI planner. Based on the user's input, decide which tools to use. Output a JSON list.

User prompt:
{user_prompt}

Example response:
[
  {{ "type": "search_email", "query": "abfas" }},
  {{ "type": "get_calendar", "date": "2025-07-10" }}
]
"""

    messages = [
        {"role": "system", "content": "You're a tool planning assistant."},
        {"role": "user", "content": planning_prompt},
    ]
    if reasoning_mode:
        messages.insert(0, {"role": "system", "content": "Think step by step and explain what you are doing and why."})

    response = chat_completion(model, messages)

    # Extract the first JSON block (starting with [ and ending with ])
    import re
    matches = re.findall(r"\[\s*{.*?}\s*\]", response, re.DOTALL)

    if not matches:
        print("\u26a0\ufe0f No valid JSON block found in planner output")
        print("Raw model response:", response)
        return [{"type": "chat", "prompt": "I'm not sure what to do. Can you clarify?"}]

    try:
        plan = json.loads(matches[0])
        if not isinstance(plan, list) or not all("type" in step for step in plan):
            raise ValueError("Invalid plan structure")
        return plan
    except Exception as e:
        print("\u26a0\ufe0f Failed to parse planner JSON:", e)
        print("Raw match:", matches[0])
        return [{"type": "chat", "prompt": "I'm not sure what to do. Can you clarify?"}]

ONEDRIVE_KEYWORDS = {'onedrive', 'search', 'summarize', 'find', 'list'}
EMAIL_KEYWORDS = {'gmail', 'email', 'inbox', 'mail'}
CALENDAR_KEYWORDS = {'calendar', 'event', 'schedule'}
SEARCH_EMAIL_PREFIXES = (
    'search email', 'find email', 'search emails', 'find emails'
)
SEARCH_EVENT_PREFIXES = (
    'search calendar', 'search event', 'find event', 'find events'
)
CREATE_EVENT_PREFIXES = (
    'add event',
    'create event',
    'new event',
    'schedule event',
    'set appointment',
    'schedule appointment',
    'set meeting',
    'schedule meeting',
)
SEND_EMAIL_PREFIXES = ('send email', 'email to', 'compose email')
READ_EMAIL_PREFIXES = ('read email', 'open email', 'view email')

# Track email composition across multiple turns
PENDING_EMAIL: dict[str, str | None] = {
    'step': None,
    'address': None,
    'subject': None,
    'body': None,
}

# Pending calendar event details
PENDING_EVENT: dict[str, str | None] = {
    'step': None,
    'title': None,
    'time': None,
}


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


def _needs_unread_email(query: str) -> bool:
    """Return True if the user is likely requesting unread email."""
    q = query.lower()
    if 'email' not in q:
        return False
    triggers = ['check', 'unread', 'new', 'any', 'view', 'show', 'recent', 'inbox']
    return any(t in q for t in triggers)


def _needs_calendar_events(query: str) -> bool:
    """Return True if the user is asking about calendar events."""
    q = query.lower()
    if 'calendar' not in q and 'event' not in q and 'schedule' not in q:
        return False
    triggers = ['check', 'what', 'show', 'view', 'list', 'any', 'today', 'tomorrow', 'yesterday', 'upcoming']
    return any(t in q for t in triggers)


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
    llm_name = llm if llm else "qwen3:30b-a3b"
    text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    out = subprocess.check_output(["ollama", "run", llm_name, text])
    return out.decode().strip()


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



def plan_then_answer(user_prompt: str):
    selected_model = get_selected_model()
    prompt_clean = user_prompt.lower().strip()

    # Handle small talk or casual prompts
    if prompt_clean in ["hi", "hello", "hey", "how are you", "yo", "what's up", "sup", "good morning", "good evening"]:
        return chat_completion(selected_model, [{"role": "user", "content": user_prompt}])

    # Attempt to plan actions
    try:
        actions = plan_actions(user_prompt, selected_model)
    except Exception as e:
        return "\u26a0\ufe0f Planning failed: " + str(e)

    # Fallback if no actions returned
    if not actions or len(actions) == 0:
        return "\u26a0\ufe0f I couldn't determine what action to take."

    results = {}

    # Dynamically execute actions using TOOL_REGISTRY
    for action in actions:
        if action.get("type") == "chat":
            action["prompt"] = user_prompt
        action["model"] = selected_model
        action_type = action.get("type")
        if action_type in TOOL_REGISTRY:
            try:
                result = TOOL_REGISTRY[action_type](action)
                results[action_type] = result
            except Exception as e:
                results[action_type] = f"\u26a0\ufe0f Tool error: {str(e)}"
        else:
            results[action_type] = "\u26a0\ufe0f Unknown action type"

    # Save results for follow-up summarization
    for key, val in results.items():
        last_tool_output[key] = val

    return format_results(results)


def format_results(results):
    reply = []
    for k, v in results.items():
        if isinstance(v, list):
            reply.append(f"{k}:\n" + "\n".join(str(i) for i in v))
        else:
            reply.append(f"{k}: {v}")
    return "\n\n".join(reply)


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
    selected_model = get_selected_model()
    cot_mode = False
    q = query.lower()
    if "/think" in q:
        cot_mode = True
        query = query.replace("/think", "").strip()
        q = query.lower()
    reply = ''
    global PENDING_EMAIL, PENDING_EVENT

    if PENDING_EMAIL['step']:
        if PENDING_EMAIL['step'] == 'address':
            PENDING_EMAIL['address'] = query.strip()
            PENDING_EMAIL['step'] = 'subject'
            reply = 'What is the subject?'
            save_message(query, reply)
            return reply
        if PENDING_EMAIL['step'] == 'subject':
            PENDING_EMAIL['subject'] = query.strip()
            PENDING_EMAIL['step'] = 'body'
            reply = 'What should the email say?'
            save_message(query, reply)
            return reply
        if PENDING_EMAIL['step'] == 'body':
            PENDING_EMAIL['body'] = query.strip()
            send_email(PENDING_EMAIL['address'], PENDING_EMAIL['subject'], PENDING_EMAIL['body'])
            reply = 'Email sent.'
            PENDING_EMAIL = {'step': None, 'address': None, 'subject': None, 'body': None}
            save_message(query, reply)
            return reply
    if PENDING_EVENT['step']:
        if PENDING_EVENT['step'] == 'time':
            text = f"add event {PENDING_EVENT['title']} {query}" if PENDING_EVENT['title'] else f"add event {query}"
            reply = create_event(text)
            if reply == 'Could not parse time.':
                reply = 'Sorry, I could not understand the time. Please try again.'
                save_message(query, reply)
                return reply
            PENDING_EVENT = {'step': None, 'title': None, 'time': None}
            save_message(query, reply)
            return reply
    if any(q.startswith(p) for p in READ_EMAIL_PREFIXES):
        parts = query.split(' ', 2)
        if len(parts) < 3:
            reply = 'Please provide email search terms.'
        else:
            term = parts[2]
            email = read_email(term)
            if not email:
                reply = 'No matching email found.'
            else:
                save_email(email)
                body = email.get('body', '')
                reply = f"From {email['from']}: {email['subject']}\n{body}"
    elif any(q.startswith(p) for p in SEARCH_EMAIL_PREFIXES):
        parts = query.split(' ', 2)
        if len(parts) < 3:
            reply = 'Please provide email search terms.'
        else:
            term = parts[2]
            emails = search_emails(term)
            for e in emails:
                save_email(e)
            if not emails:
                reply = 'No matching emails found.'
            else:
                lines = [f"From {e['from']}: {e['subject']} - {e['snippet']}" for e in emails]
                reply = '\n'.join(lines)
    elif any(q.startswith(p) for p in SEARCH_EVENT_PREFIXES):
        parts = query.split(' ', 2)
        if len(parts) < 3:
            reply = 'Please provide calendar search terms.'
        else:
            term = parts[2]
            events = search_events(term)
            save_calendar_events(events)
            if not events:
                reply = 'No matching events found.'
            else:
                lines = [f"{e['start']} {e['title']}" for e in events]
                reply = '\n'.join(lines)
    elif any(q.startswith(p) for p in SEND_EMAIL_PREFIXES):
        parts = query.split(' ', 3)
        if len(parts) < 2:
            PENDING_EMAIL = {'step': 'address', 'address': None, 'subject': None, 'body': None}
            reply = 'Who is the recipient?'
        elif len(parts) < 4:
            addr = parts[2] if len(parts) > 2 else None
            PENDING_EMAIL = {'step': 'subject', 'address': addr, 'subject': None, 'body': None}
            if addr is None:
                PENDING_EMAIL['step'] = 'address'
                reply = 'Who is the recipient?'
            else:
                reply = 'What is the subject?'
        else:
            addr = parts[2]
            subject_body = parts[3]
            if '"' in subject_body:
                try:
                    subject, body = subject_body.split('"', 2)[1::2]
                except ValueError:
                    reply = 'Usage: send email <address> "<subject>" <message>'
                    subject = body = None
            else:
                sub_parts = subject_body.split(' ', 1)
                subject = sub_parts[0]
                body = sub_parts[1] if len(sub_parts) > 1 else ''
            if subject is not None:
                send_email(addr, subject, body)
                reply = 'Email sent.'
    elif any(q.startswith(p) for p in CREATE_EVENT_PREFIXES):
        reply = create_event(query)
        if reply == 'Could not parse time.':
            title = query
            for p in CREATE_EVENT_PREFIXES:
                if title.lower().startswith(p):
                    title = title[len(p):].strip()
                    break
            PENDING_EVENT = {'step': 'time', 'title': title, 'time': None}
            reply = 'When should this event occur?'
    elif any(k in q for k in EMAIL_KEYWORDS):
        if _needs_unread_email(query):
            email = fetch_unread_email()
            save_email(email)
            if not email:
                reply = 'No unread email.'
            else:
                reply = f"From {email['from']}: {email['subject']} - {email['snippet']}"
        else:
            reply = plan_then_answer(query)
    elif any(k in q for k in CALENDAR_KEYWORDS):
        if _needs_calendar_events(query):
            offset = 0
            if 'yesterday' in q:
                offset = -1
            elif 'tomorrow' in q:
                offset = 1
            else:
                dt = parse_date(query, settings={'RELATIVE_BASE': datetime.datetime.utcnow()})
                if dt:
                    offset = (dt.date() - datetime.datetime.utcnow().date()).days
            events = list_events_for_day(offset)
            save_calendar_events(events)
            if not events:
                reply = 'No calendar events today.' if offset == 0 else 'No calendar events.'
            else:
                lines = [f"{e['start']} {e['title']}" for e in events]
                reply = '\n'.join(lines)
        else:
            reply = plan_then_answer(query)
    elif any(k in q for k in ONEDRIVE_KEYWORDS):
        if 'list' in q and 'word' in q:
            docs = list_word_docs()
            reply = 'Word docs:\n' + '\n'.join(docs)
        else:
            results = search(query)
            if not results:
                reply = 'No matching documents found.'
            else:
                lines = []
                for r in results:
                    snippet = f" - {r['snippet']}" if r.get('snippet') else ''
                    lines.append(f"{r['name']}{snippet}")
                reply = '\n'.join(lines)
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
        reply = plan_then_answer(query)
    save_message(query, reply)
    return reply
