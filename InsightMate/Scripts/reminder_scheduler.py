from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dateparser import parse
import win32api
import win32con
import win32gui

scheduler = BackgroundScheduler()
scheduler.start()

def _notify(message: str):
    try:
        win32api.MessageBox(0, message, 'InsightMate Reminder', win32con.MB_OK)
    except Exception:
        pass

def schedule(text: str):
    when = parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not when:
        return 'Could not parse time.'
    scheduler.add_job(_notify, 'date', run_date=when, args=[text])
    return f'Reminder set for {when}'
