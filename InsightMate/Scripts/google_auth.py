from __future__ import annotations
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    # Allow reading and writing calendar events
    'https://www.googleapis.com/auth/calendar',
]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")
CREDENTIALS_FILE = "credentials.json"

def get_credentials():
    """Return authorized Google credentials for Gmail and Calendar."""
    creds = None
    token_path = TOKEN_FILE
    credentials_path = os.path.join(os.path.dirname(__file__), CREDENTIALS_FILE)
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds
