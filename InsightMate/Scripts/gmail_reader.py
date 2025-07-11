from __future__ import print_function
from email.header import decode_header, make_header
from googleapiclient.discovery import build

from google_auth import get_credentials


def fetch_unread_email():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])
    if not messages:
        return None
    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
    headers = {h['name']: str(make_header(decode_header(h['value']))) for h in msg['payload']['headers']}
    sender = headers.get('From', '')
    subject = headers.get('Subject', '')
    snippet = msg.get('snippet', '')[:250]
    return {'from': sender, 'subject': subject, 'snippet': snippet}


if __name__ == '__main__':
    print(fetch_unread_email())
