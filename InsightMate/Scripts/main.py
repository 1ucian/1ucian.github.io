import json
import os
import requests

from assistant_router import plan_actions
from gmail_reader import search_emails
from calendar_reader import list_events_for_day
from imessage_reader import read_latest_imessage
from onedrive_reader import list_recent_files
from send_imessage import send_imessage

SERVER_URL = 'http://localhost:5000/process'
OUTPUT_FILE = '/tmp/insight_output.txt'

def main(prompt: str = "Summarize recent activity."):
    print("Planning...")
    try:
        actions = plan_actions(prompt)
    except Exception as e:
        print("Planner failed, defaulting to email + calendar")
        actions = [
            {"type": "search_email", "query": ""},
            {"type": "get_calendar", "date": "today"},
        ]

    data = {}
    for action in actions:
        if action.get("type") == "search_email":
            data["email"] = search_emails(action.get("query", ""))
        elif action.get("type") == "get_calendar":
            data["calendar"] = list_events_for_day(action.get("date", "today"))
        elif action.get("type") == "read_imessage":
            data["imessage"] = read_latest_imessage()
        elif action.get("type") == "list_drive":
            data["onedrive"] = list_recent_files()

    payload = {"prompt": prompt, **data}

    print('Sending to AI server...')
    resp = requests.post(SERVER_URL, json=payload)
    reply = resp.json().get('reply', '')
    print('AI reply:', reply)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(reply)

    imsg_data = data.get('imessage')
    if imsg_data:
        try:
            send_imessage(imsg_data['from'], reply)
        except Exception as e:
            print('Failed to send iMessage:', e)


if __name__ == '__main__':
    import sys
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Summarize recent activity."
    main(user_prompt)
