import datetime
from googleapiclient.discovery import build

from google_auth import get_credentials


def list_events_for_day(offset_days: int) -> list[dict]:
    """Return calendar events for today plus ``offset_days`` days."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    start = (
        datetime.datetime.utcnow()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        + datetime.timedelta(days=offset_days)
    )
    end = start + datetime.timedelta(days=1)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat() + "Z",
            timeMax=end.isoformat() + "Z",
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
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(days=days)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat() + 'Z',
        timeMax=end.isoformat() + 'Z',
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


if __name__ == '__main__':
    print(list_today_events())

