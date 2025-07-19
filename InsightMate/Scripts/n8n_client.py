import os
import requests
import logging

BASE_URL = os.getenv("N8N_URL", "http://localhost:5678")
API_KEY = os.getenv("N8N_API_KEY", "")


def _post(path: str, payload: dict | None = None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    try:
        resp = requests.post(url, json=payload or {}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data") or data
    except Exception as e:
        logging.error("n8n request failed: %s", e)
        raise


USE_N8N = bool(os.getenv("N8N_URL"))


def search_emails(query: str):
    """Return emails from the configured n8n workflow."""
    workflow = os.getenv("N8N_SEARCH_EMAIL_ID", "search_email")
    return _post(f"/api/v1/workflows/{workflow}/execute", {"query": query})


def list_events_for_day(date: str):
    workflow = os.getenv("N8N_GET_CALENDAR_ID", "get_calendar")
    return _post(f"/api/v1/workflows/{workflow}/execute", {"date": date})


def list_events_for_range(start: str, end: str):
    workflow = os.getenv("N8N_RANGE_CAL_ID", "get_calendar_range")
    return _post(
        f"/api/v1/workflows/{workflow}/execute", {"start": start, "end": end}
    )


def create_event(text: str):
    workflow = os.getenv("N8N_CREATE_EVENT_ID", "create_event")
    return _post(f"/api/v1/workflows/{workflow}/execute", {"text": text})
