import os
import sqlite3
from datetime import datetime

CHAT_DB = os.path.expanduser('~/Library/Messages/chat.db')


def read_latest_imessage():
    conn = sqlite3.connect(CHAT_DB)
    c = conn.cursor()
    query = (
        "SELECT handle.id, message.text, message.date \
         FROM message JOIN handle ON message.handle_id = handle.ROWID \
         WHERE message.is_from_me = 0 \
         ORDER BY message.date DESC LIMIT 1"
    )
    row = c.execute(query).fetchone()
    conn.close()
    if not row:
        return None
    sender, text, date = row
    return {"from": sender, "message": text or ""}


if __name__ == '__main__':
    print(read_latest_imessage())
