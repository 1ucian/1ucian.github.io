import os
import subprocess
from typing import Optional
import openai
from dotenv import load_dotenv
from config import load_config, get_api_key, get_llm, get_prompt

from onedrive_reader import search, list_word_docs
from gmail_reader import fetch_unread_email, search_emails
from calendar_reader import list_today_events, search_events
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

load_dotenv()


def chat_completion(model: str, messages: list[dict]) -> str:
    """Call the OpenAI chat completion API compatible with v1.x or older."""
    if hasattr(openai, "chat") and hasattr(openai.chat, "completions"):
        resp = openai.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content.strip()
    resp = openai.ChatCompletion.create(model=model, messages=messages)
    return resp["choices"][0]["message"]["content"].strip()

def _get_config():
    return load_config()

ONEDRIVE_KEYWORDS = {'onedrive', 'search', 'summarize', 'find', 'list'}
EMAIL_KEYWORDS = {'gmail', 'email', 'inbox', 'mail'}
CALENDAR_KEYWORDS = {'calendar', 'event', 'schedule'}
SEARCH_EMAIL_PREFIXES = ('search email', 'find email', 'search emails', 'find emails')
SEARCH_EVENT_PREFIXES = ('search calendar', 'search event', 'find event', 'find events')


def gpt(prompt: str) -> str:
    cfg = _get_config()
    llm = get_llm(cfg).lower()
    api_key = get_api_key(cfg)
    system_prompt = get_prompt(cfg)
    history = get_recent_messages(10)
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m[1], "content": m[2]} for m in history]
    messages.append({"role": "user", "content": prompt})
    if llm in {"gpt-4", "gpt-4o", "o4-mini", "o4-mini-high"}:
        if not api_key:
            return "OpenAI API key missing."
        openai.api_key = api_key
        if llm == "gpt-4o":
            model = "gpt-4o"
        elif llm == "gpt-4":
            model = "gpt-4"
        else:
            model = llm
        return chat_completion(model, messages)
    model = llm if llm else "qwen3:30b-a3b"
    text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}" for m in messages
    )
    out = subprocess.check_output(["ollama", "run", model, text])
    return out.decode().strip()


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
    save_message('user', query)
    q = query.lower()
    reply = ''
    if any(q.startswith(p) for p in SEARCH_EMAIL_PREFIXES):
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
    elif any(k in q for k in EMAIL_KEYWORDS):
        email = fetch_unread_email()
        save_email(email)
        if not email:
            reply = 'No unread email.'
        else:
            reply = f"From {email['from']}: {email['subject']} - {email['snippet']}"
    elif any(k in q for k in CALENDAR_KEYWORDS):
        events = list_today_events()
        save_calendar_events(events)
        if not events:
            reply = 'No calendar events today.'
        else:
            lines = [f"{e['start']} {e['title']}" for e in events]
            reply = '\n'.join(lines)
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
            lines = [f"{m[0]} {m[1]}: {m[2]}" for m in mem]
            reply = '\n'.join(lines)
    elif 'open' in q or 'launch' in q or 'play' in q:
        reply = execute_action(query)
    else:
        reply = gpt(query)
    save_message('assistant', reply)
    return reply
