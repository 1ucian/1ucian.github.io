import os
import sqlite3
from typing import List, Tuple, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), 'memory.db')


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS messages ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'ts DATETIME DEFAULT CURRENT_TIMESTAMP,'
        'sender TEXT,'
        'text TEXT'
        ')'
    )
    c.execute(
        'CREATE TABLE IF NOT EXISTS emails ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'ts DATETIME DEFAULT CURRENT_TIMESTAMP,'
        'sender TEXT,'
        'subject TEXT,'
        'snippet TEXT'
        ')'
    )
    c.execute(
        'CREATE TABLE IF NOT EXISTS calendar_events ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'ts DATETIME DEFAULT CURRENT_TIMESTAMP,'
        'title TEXT,'
        'start TEXT,'
        'end TEXT'
        ')'
    )
    conn.commit()
    conn.close()


init_db()


def save_message(sender: str, text: str) -> None:
    conn = _connect()
    conn.execute('INSERT INTO messages(sender, text) VALUES (?, ?)', (sender, text))
    conn.commit()
    conn.close()


def save_email(email: Dict[str, str]) -> None:
    if not email:
        return
    conn = _connect()
    conn.execute(
        'INSERT INTO emails(sender, subject, snippet) VALUES (?, ?, ?)',
        (email.get('from', ''), email.get('subject', ''), email.get('snippet', ''))
    )
    conn.commit()
    conn.close()


def save_calendar_events(events: List[Dict[str, str]]) -> None:
    if not events:
        return
    conn = _connect()
    for e in events:
        conn.execute(
            'INSERT INTO calendar_events(title, start, end) VALUES (?, ?, ?)',
            (e.get('title', ''), e.get('start', ''), e.get('end', ''))
        )
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 20) -> List[Tuple[str, str, str]]:
    conn = _connect()
    c = conn.cursor()
    c.execute('SELECT ts, sender, text FROM messages ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
