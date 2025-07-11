import datetime
from googleapiclient.discovery import build

from google_auth import get_credentials


def list_today_events():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    tz = datetime.datetime.now().astimezone().tzinfo
    start = datetime.datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=1)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
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
