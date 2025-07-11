import json
import openai
from dateparser import parse as parse_date

from assistant_router import plan_actions
from gmail_reader import search_emails
from calendar_reader import list_events_for_day
from imessage_reader import read_latest_imessage
from onedrive_reader import list_recent_files
from send_imessage import send_imessage
from summarizer import summarize_text
from memory_db import init_db, save_message, get_recent_messages

OUTPUT_FILE = '/tmp/insight_output.txt'

init_db()

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
            date_str = action.get("date", "today")
            parsed = parse_date(date_str)
            if parsed:
                iso_date = parsed.strftime("%Y-%m-%d")
                data["calendar"] = list_events_for_day(iso_date)
        elif action.get("type") == "read_imessage":
            data["imessage"] = read_latest_imessage()
        elif action.get("type") == "list_drive":
            data["onedrive"] = list_recent_files()
        elif action.get("type") == "summarize":
            source = action.get("source")
            if source and source in data:
                data["summary"] = summarize_text(data[source])

    history = get_recent_messages()
    messages = [{"role": "system", "content": "You are InsightMate, a smart assistant."}]
    for mem in history:
        messages.append({"role": "user", "content": mem["user"]})
        messages.append({"role": "assistant", "content": mem["assistant"]})
    messages.append({"role": "user", "content": prompt})

    print('Contacting model...')
    resp = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    reply = resp.choices[0].message.content.strip()
    print('AI reply:', reply)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(reply)

    save_message(prompt, reply)

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
