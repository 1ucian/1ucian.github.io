import datetime
from googleapiclient.discovery import build

from google_auth import get_credentials
from dateparser.search import search_dates


def list_events_for_day(offset_days: int) -> list[dict]:
    """Return calendar events for today plus ``offset_days`` days."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    tz = datetime.datetime.now().astimezone().tzinfo
    start = (
        datetime.datetime.now(tz)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        + datetime.timedelta(days=offset_days)
    )
    end = start + datetime.timedelta(days=1)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    output = []
    for e in events:
        start_time = e["start"].get("dateTime", e["start"].get("date"))
        end_time = e["end"].get("dateTime", e["end"].get("date"))
        output.append({"title": e.get("summary", ""), "start": start_time, "end": end_time})
    return output


def list_today_events() -> list[dict]:
    """Return calendar events for today."""
    return list_events_for_day(0)


def search_events(query: str, days: int = 30, limit: int = 10):
    """Search upcoming calendar events for the given text."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    tz = datetime.datetime.now().astimezone().tzinfo
    start = datetime.datetime.now(tz)
    end = start + datetime.timedelta(days=days)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime',
        q=query,
        maxResults=limit,
    ).execute()
    events = events_result.get('items', [])
    output = []
    for e in events:
        start_time = e['start'].get('dateTime', e['start'].get('date'))
        end_time = e['end'].get('dateTime', e['end'].get('date'))
        output.append({'title': e.get('summary', ''), 'start': start_time, 'end': end_time})
    return output


def create_event(text: str) -> str:
    """Create a calendar event from ``text``.

    The first recognizable date in ``text`` is used as the start time and the
    remainder becomes the title. A one hour duration is assumed.
    """
    matches = search_dates(text, settings={'PREFER_DATES_FROM': 'future'})
    if not matches:
        return 'Could not parse time.'

    phrase, when = matches[0]
    tz = datetime.datetime.now().astimezone().tzinfo
    if when.tzinfo is None:
        when = when.replace(tzinfo=tz)
    start = when
    end = start + datetime.timedelta(hours=1)

    title = text.replace(phrase, '').strip()
    for p in ('add event', 'create event', 'new event', 'schedule event'):
        if title.lower().startswith(p):
            title = title[len(p):].strip()
            break
    if not title:
        title = 'New Event'

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    body = {
        'summary': title,
        'start': {'dateTime': start.isoformat()},
        'end': {'dateTime': end.isoformat()},
    }
    service.events().insert(calendarId='primary', body=body).execute()
    return f"Event '{title}' added for {start.isoformat()}"


if __name__ == '__main__':
    print(list_today_events())

