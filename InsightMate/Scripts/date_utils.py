from datetime import datetime, timedelta, timezone

PT = timezone(timedelta(hours=-7))  # Pacific Time

def today_pt():
    return datetime.now(PT).date()

def date_keyword(word: str):
    base = today_pt()
    if word == "today":
        return base
    if word == "yesterday":
        return base - timedelta(days=1)
    if word == "tomorrow":
        return base + timedelta(days=1)
    return None
