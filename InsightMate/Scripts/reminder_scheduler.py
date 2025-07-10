from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dateparser import parse

try:
    import win32api
    import win32con
    import win32gui
except Exception:  # not on Windows or pywin32 missing
    win32api = win32con = win32gui = None

scheduler = BackgroundScheduler()
scheduler.start()

def _notify(message: str):
    if win32api and win32con:
        try:
            win32api.MessageBox(0, message, 'InsightMate Reminder', win32con.MB_OK)
        except Exception:
            print(f"Reminder: {message}")
    else:
        print(f"Reminder: {message}")

def schedule(text: str):
    when = parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not when:
        return 'Could not parse time.'
    scheduler.add_job(_notify, 'date', run_date=when, args=[text])
    return f'Reminder set for {when}'
