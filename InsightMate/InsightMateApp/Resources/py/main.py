import json
import os
import requests

from imessage_reader import read_latest_imessage
from gmail_reader import fetch_unread_email
from calendar_reader import list_today_events
from onedrive_reader import list_recent_files
from send_imessage import send_imessage

SERVER_URL = 'http://localhost:5000/process'
OUTPUT_FILE = '/tmp/insight_output.txt'

def main(prompt: str = "Summarize recent activity."):
    print('Reading data...')
    imsg = read_latest_imessage()
    email = fetch_unread_email()
    cal = list_today_events()
    drive = list_recent_files()
    payload = {
        'imessage': imsg,
        'email': email,
        'calendar': cal,
        'onedrive': drive,
        'prompt': prompt,
    }
    print('Sending to AI server...')
    resp = requests.post(SERVER_URL, json=payload)
    reply = resp.json().get('reply', '')
    print('AI reply:', reply)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(reply)
    if imsg:
        try:
            send_imessage(imsg['from'], reply)
        except Exception as e:
            print('Failed to send iMessage:', e)


if __name__ == '__main__':
    import sys
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Summarize recent activity."
    main(user_prompt)
