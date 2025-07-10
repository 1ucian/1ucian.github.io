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
    q = query.lower()
    if any(k in q for k in EMAIL_KEYWORDS):
        email = fetch_unread_email()
        if not email:
            return 'No unread email.'
        return f"From {email['from']}: {email['subject']} - {email['snippet']}"
    if any(k in q for k in CALENDAR_KEYWORDS):
        events = list_today_events()
        if not events:
            return 'No calendar events today.'
        lines = [f"{e['start']} {e['title']}" for e in events]
        return '\n'.join(lines)
    if any(k in q for k in ONEDRIVE_KEYWORDS):
        if 'list' in q and 'word' in q:
            docs = list_word_docs()
            return 'Word docs:\n' + '\n'.join(docs)
        results = search(query)
        if not results:
            return 'No matching documents found.'
        lines = []
        for r in results:
            snippet = f" - {r['snippet']}" if r.get('snippet') else ''
            lines.append(f"{r['name']}{snippet}")
        return '\n'.join(lines)
    if 'remind me' in q or q.startswith('remind'):
        return schedule_reminder(query)
    if 'open' in q or 'launch' in q or 'play' in q:
        return execute_action(query)
    return gpt(query)
