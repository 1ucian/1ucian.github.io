import datetime
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build

from google_auth import get_credentials
from dateparser.search import search_dates

CREATE_EVENT_PREFIXES = (
    'add event',
    'create event',
    'new event',
    'schedule event',
    'set appointment',
    'schedule appointment',
    'set meeting',
    'schedule meeting',
)

FILLER_WORDS = (
    'for',
    'at',
    'on',
)

# Use Pacific time for all calendar operations
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def list_events_for_day(day: int | str) -> list[dict]:
    """Return calendar events for the given day.

    ``day`` may be an integer offset from today or an ISO ``YYYY-MM-DD`` string.
    """
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    if isinstance(day, int):
        start = (
            datetime.datetime.now(PACIFIC_TZ)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            + datetime.timedelta(days=day)
        )
    else:
        parsed = parse_date(str(day))
        if not parsed:
            return []
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=PACIFIC_TZ)
        else:
            parsed = parsed.astimezone(PACIFIC_TZ)
        start = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
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
    start = datetime.datetime.now(PACIFIC_TZ)
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
    matches = search_dates(
        text,
        settings={'PREFER_DATES_FROM': 'future'},
        languages=['en'],
    )
    if not matches:
        return 'Could not parse time.'

    phrase, when = matches[0]
    if when.tzinfo is None:
        when = when.replace(tzinfo=PACIFIC_TZ)
    else:
        when = when.astimezone(PACIFIC_TZ)
    start = when
    end = start + datetime.timedelta(hours=1)

    title = text.replace(phrase, '').strip()
    for p in CREATE_EVENT_PREFIXES:
        if title.lower().startswith(p):
            title = title[len(p):].strip()
            break
    for word in FILLER_WORDS:
        if title.lower().startswith(word + ' '):
            title = title[len(word) + 1:].strip()
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

