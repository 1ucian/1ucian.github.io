"""Minimal Flask server for the InsightMate web app."""

import os
import requests

from flask import Flask
from dotenv import load_dotenv

from server_common import register_common, WEB_DIR
from memory_db import init_db


load_dotenv()
init_db()

# Serve files from the shared web directory.  ``static_url_path`` is set to
# ``''`` so URLs match ``/index.html`` rather than ``/static/index.html``.
app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")

# Register routes such as ``/chat`` and ``/reminders`` defined in
# ``server_common.py``.
register_common(app)


if __name__ == "__main__":
    from llm_client import OLLAMA_URL
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    except Exception:
        print("\u26a0\ufe0f Ollama server not reachable. Start it with `ollama serve`." )
    # Listen on all interfaces so the web client can connect locally.
    app.run(host="0.0.0.0", port=5000)
