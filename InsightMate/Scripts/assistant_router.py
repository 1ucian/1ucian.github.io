import os
import subprocess
from typing import Optional
import openai
from dotenv import load_dotenv
from config import load_config, get_api_key, get_llm

from onedrive_reader import search, list_word_docs
from gmail_reader import fetch_unread_email
from calendar_reader import list_today_events
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
)

load_dotenv()

def _get_config():
    return load_config()

ONEDRIVE_KEYWORDS = {'onedrive', 'search', 'summarize', 'find', 'list'}
EMAIL_KEYWORDS = {'gmail', 'email', 'inbox', 'mail'}
CALENDAR_KEYWORDS = {'calendar', 'event', 'schedule'}


def gpt(prompt: str) -> str:
    cfg = _get_config()
    llm = get_llm(cfg).lower()
    api_key = get_api_key(cfg)
    if llm in {'gpt-4', 'gpt-4o'}:
        if not api_key:
            return 'OpenAI API key missing.'
        openai.api_key = api_key
        model = 'gpt-4o' if llm == 'gpt-4o' else 'gpt-4'
        resp = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}])
        return resp['choices'][0]['message']['content'].strip()
    model = llm if llm else 'llama3'
    out = subprocess.check_output(['ollama', 'run', model, prompt])
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
    if any(k in q for k in EMAIL_KEYWORDS):
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
    elif 'open' in q or 'launch' in q or 'play' in q:
        reply = execute_action(query)
    else:
        reply = gpt(query)
    save_message('assistant', reply)
    return reply
