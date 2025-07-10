import os
import subprocess
from typing import Optional
import openai
from dotenv import load_dotenv

from onedrive_reader import search, list_word_docs
from gmail_reader import fetch_unread_email
from calendar_reader import list_today_events
from reminder_scheduler import schedule as schedule_reminder
from action_executor import execute as execute_action
from memory_db import (
    save_message,
    save_email,
    save_calendar_events,
)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

ONEDRIVE_KEYWORDS = {'onedrive', 'search', 'summarize', 'find', 'list'}
EMAIL_KEYWORDS = {'gmail', 'email', 'inbox', 'mail'}
CALENDAR_KEYWORDS = {'calendar', 'event', 'schedule'}


def gpt(prompt: str) -> str:
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(model='gpt-4', messages=[{"role": "user", "content": prompt}])
        return resp['choices'][0]['message']['content'].strip()
    out = subprocess.check_output(['ollama', 'run', 'llama3', prompt])
    return out.decode().strip()


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
    elif 'open' in q or 'launch' in q or 'play' in q:
        reply = execute_action(query)
    else:
        reply = gpt(query)
    save_message('assistant', reply)
    return reply
