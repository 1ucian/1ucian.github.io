from __future__ import print_function
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import base64
import os

from google_auth import get_credentials


def _get_body(msg: dict) -> str:
    """Return the plain text body from a Gmail message."""
    payload = msg.get("payload", {})

    def _walk(part):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
        for p in part.get("parts", []):
            text = _walk(p)
            if text:
                return text
        return ""

    return _walk(payload)


def _msg_to_dict(service, msg_id, include_body: bool = False):
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
    data = {'from': sender, 'subject': subject, 'snippet': snippet}
    if include_body:
        data['body'] = _get_body(msg)
    return data


def fetch_unread_email(include_body: bool = False):
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])
    if not messages:
        return None
    msg_id = messages[0]['id']
    data = _msg_to_dict(service, msg_id, include_body=include_body)
    return data


def search_emails(query: str, limit: int = 5, include_body: bool = False):
    """Return list of emails matching the Gmail search query."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(
        userId='me', q=query, maxResults=limit
    ).execute()
    messages = results.get('messages', [])
    output = []
    for m in messages:
        output.append(_msg_to_dict(service, m['id'], include_body=include_body))
    return output


def read_email(query: str) -> dict | None:
    """Return the first email matching ``query`` with full body."""
    results = search_emails(query, limit=1, include_body=True)
    return results[0] if results else None


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

