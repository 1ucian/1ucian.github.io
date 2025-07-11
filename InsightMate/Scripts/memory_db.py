import os
import sqlite3
from typing import List, Tuple, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize the SQLite database if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            assistant TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
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
    c.execute(
        'CREATE TABLE IF NOT EXISTS reminders ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'ts DATETIME DEFAULT CURRENT_TIMESTAMP,'
        'text TEXT,'
        'run_time TEXT'
        ')'
    )
    c.execute(
        'CREATE TABLE IF NOT EXISTS tasks ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'ts DATETIME DEFAULT CURRENT_TIMESTAMP,'
        'type TEXT,'
        'description TEXT,'
        'schedule TEXT'
        ')'
    )
    conn.commit()
    conn.close()


def save_message(user_input: str, ai_reply: str, limit: int = 100) -> None:
    """Save a user/assistant message pair and prune old history."""
    conn = _connect()
    conn.execute(
        'INSERT INTO messages(user, assistant) VALUES (?, ?)',
        (user_input, ai_reply),
    )
    conn.commit()
    _prune(conn, limit)
    conn.close()

def _prune(conn: sqlite3.Connection, limit: int) -> None:
    """Keep only the most recent ``limit`` message pairs."""
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM messages')
    count = cur.fetchone()[0]
    if count <= limit:
        return
    cur.execute(
        'DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages ORDER BY id DESC LIMIT ?)',
        (limit,),
    )
    conn.commit()


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


def get_recent_messages(limit: int = 5) -> List[Dict[str, str]]:
    """Return the most recent message pairs in chronological order."""
    conn = _connect()
    c = conn.cursor()
    c.execute('SELECT user, assistant FROM messages ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    rows.reverse()
    return [{'user': r[0], 'assistant': r[1]} for r in rows]


def save_reminder(text: str, run_time: str) -> None:
    conn = _connect()
    conn.execute('INSERT INTO reminders(text, run_time) VALUES (?, ?)', (text, run_time))
    conn.commit()
    conn.close()


def list_reminders() -> List[Tuple[int, str, str]]:
    conn = _connect()
    c = conn.cursor()
    c.execute('SELECT id, text, run_time FROM reminders ORDER BY run_time')
    rows = c.fetchall()
    conn.close()
    return rows


def save_task(task_type: str, description: str, schedule: str) -> None:
    conn = _connect()
    conn.execute(
        'INSERT INTO tasks(type, description, schedule) VALUES (?, ?, ?)',
        (task_type, description, schedule)
    )
    conn.commit()
    conn.close()


def list_tasks() -> List[Tuple[int, str, str, str]]:
    conn = _connect()
    c = conn.cursor()
    c.execute('SELECT id, type, description, schedule FROM tasks ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return rows


def clear_memory() -> None:
    """Delete all chat messages from the local memory database."""
    conn = _connect()
    conn.execute('DELETE FROM messages')
    conn.commit()
    conn.close()
