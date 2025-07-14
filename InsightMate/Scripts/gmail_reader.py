from __future__ import print_function
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import base64
import os

from google_auth import get_credentials

# ------------- NEW HELPERS -------------
from datetime import datetime, timedelta, timezone
import re
from dateparser import parse as parse_date

# Always translate user keywords in Pacific Time (InsightMate standard)
PT = timezone(timedelta(hours=-7))

def _date_filter(text: str) -> str:
    """Return Gmail after/before filters for natural-language date expressions."""
    text = text.strip().lower()
    today = datetime.now(PT).date()

    # last N days / past N days
    m = re.search(r"(?:last|past)\s+(\d+)\s+days?", text)
    if m:
        n = int(m.group(1))
        start = today - timedelta(days=n)
        end = today + timedelta(days=1)
        return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    # next N days
    m = re.search(r"next\s+(\d+)\s+days?", text)
    if m:
        n = int(m.group(1))
        start = today
        end = today + timedelta(days=n + 1)
        return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    if "last week" in text or "past week" in text:
        start = today - timedelta(days=7)
        end = today + timedelta(days=1)
        return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    if "next week" in text:
        start = today + timedelta(days=1)
        end = today + timedelta(days=8)
        return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    # range expressions "from X to Y" / "between X and Y"
    range_match = re.search(
        r"(?:from|between)\s+([^\n]+?)\s+(?:to|and)\s+([^\n]+)",
        text,
    )
    if range_match:
        start_str, end_str = range_match.groups()
        start_dt = parse_date(start_str, settings={"RELATIVE_BASE": datetime.now(PT)})
        end_dt = parse_date(end_str, settings={"RELATIVE_BASE": datetime.now(PT)})
        if start_dt and end_dt:
            start = start_dt.date()
            end = end_dt.date() + timedelta(days=1)
            return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    # single date
    parsed = parse_date(text, settings={"RELATIVE_BASE": datetime.now(PT)})
    if parsed:
        start = parsed.date()
        end = start + timedelta(days=1)
        return f"after:{start:%Y/%m/%d} before:{end:%Y/%m/%d}"

    return text
# ---------------------------------------


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
    # 🔄 Normalise "today", "yesterday", etc.
    query = _date_filter(query.strip().lower())

    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = (
        service.users()
        .messages()
        .list(userId='me', q=query, maxResults=limit)
        .execute()
    )
    messages = results.get('messages', [])

    output = []
    seen: set[str] = set()
    for m in messages:
        msg_id = m.get('id')
        if not msg_id or msg_id in seen:
            continue
        seen.add(msg_id)
        output.append(_msg_to_dict(service, msg_id, include_body=include_body))

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

