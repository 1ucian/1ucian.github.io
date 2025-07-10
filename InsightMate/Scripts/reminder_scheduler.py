from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from dateparser import parse
from typing import List, Tuple
import os
import requests

from memory_db import (
    save_reminder,
    list_reminders as db_list_reminders,
    save_task,
    list_tasks as db_list_tasks,
)
from gmail_reader import fetch_unread_email
from calendar_reader import list_today_events

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

def schedule(text: str) -> str:
    when = parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not when:
        return 'Could not parse time.'
    scheduler.add_job(_notify, 'date', run_date=when, args=[text])
    save_reminder(text, when.isoformat())
    return f'Reminder set for {when}'


def _air_quality_job():
    lat = os.getenv('LATITUDE', '52.52')
    lon = os.getenv('LONGITUDE', '13.41')
    url = (
        'https://air-quality-api.open-meteo.com/v1/air-quality'
        f'?latitude={lat}&longitude={lon}&hourly=pm2_5'
    )
    try:
        data = requests.get(url, timeout=10).json()
        value = data.get('hourly', {}).get('pm2_5', [None])[0]
        if value is None:
            msg = 'Could not fetch air quality data.'
        elif value > 35:
            msg = f'PM2.5 is {value} µg/m³. Close the windows.'
        else:
            msg = f'PM2.5 is {value} µg/m³. You can open the windows.'
    except Exception as e:
        msg = f'Error checking air quality: {e}'
    _notify(msg)


def _weather_job():
    lat = os.getenv('LATITUDE', '52.52')
    lon = os.getenv('LONGITUDE', '13.41')
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}&current_weather=true'
    )
    try:
        data = requests.get(url, timeout=10).json()
        weather = data.get('current_weather', {})
        temp = weather.get('temperature')
        code = weather.get('weathercode')
        msg = f'Weather {temp}°C, code {code}' if temp is not None else 'Could not fetch weather.'
    except Exception as e:
        msg = f'Error checking weather: {e}'
    _notify(msg)


def _email_job():
    email = fetch_unread_email()
    if email:
        msg = f"Email from {email['from']}: {email['subject']}"
    else:
        msg = 'No unread email.'
    _notify(msg)


def _calendar_job():
    events = list_today_events()
    if events:
        lines = [f"{e['start']} {e['title']}" for e in events]
        msg = '\n'.join(lines)
    else:
        msg = 'No events today.'
    _notify(msg)


def schedule_air_quality(text: str) -> str:
    when = parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if not when:
        return 'Could not parse time.'
    scheduler.add_job(_air_quality_job, 'date', run_date=when)
    save_reminder(f'Air quality check at {when}', when.isoformat())
    return f'Air quality check scheduled for {when}'


def schedule_weather(interval_minutes: int) -> str:
    scheduler.add_job(_weather_job, 'interval', minutes=interval_minutes)
    save_task('weather', 'Weather update', f'every {interval_minutes}m')
    return f'Weather checks every {interval_minutes} minutes scheduled'


def schedule_email(interval_minutes: int) -> str:
    scheduler.add_job(_email_job, 'interval', minutes=interval_minutes)
    save_task('email', 'Email check', f'every {interval_minutes}m')
    return f'Email checks every {interval_minutes} minutes scheduled'


def schedule_calendar(interval_minutes: int) -> str:
    scheduler.add_job(_calendar_job, 'interval', minutes=interval_minutes)
    save_task('calendar', 'Calendar check', f'every {interval_minutes}m')
    return f'Calendar checks every {interval_minutes} minutes scheduled'


def list_reminders() -> List[Tuple[int, str, str]]:
    return db_list_reminders()


def list_tasks() -> List[Tuple[int, str, str, str]]:
    return db_list_tasks()
