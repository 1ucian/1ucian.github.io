from __future__ import print_function
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import base64
import os

from google_auth import get_credentials


def _msg_to_dict(service, msg_id):
    msg = service.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()
    headers = {
        h['name']: str(make_header(decode_header(h['value'])))
        for h in msg['payload']['headers']
    }
    sender = headers.get('From', '')
    subject = headers.get('Subject', '')
    snippet = msg.get('snippet', '')[:250]
    return {'from': sender, 'subject': subject, 'snippet': snippet}


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


def search_emails(query: str, limit: int = 5):
    """Return list of emails matching the Gmail search query."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(
        userId='me', q=query, maxResults=limit
    ).execute()
    messages = results.get('messages', [])
    output = []
    for m in messages:
        output.append(_msg_to_dict(service, m['id']))
    return output


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using the user's Gmail account."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    domain = os.getenv('EMAIL_DOMAIN', '')
    if '@' not in to:
        if domain:
            to = f"{to}@{domain}"
        else:
            raise ValueError('Recipient address missing domain')
    msg = MIMEText(body)
    msg['to'] = to
    msg['subject'] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return 'Email sent.'


if __name__ == '__main__':
    print(fetch_unread_email())

