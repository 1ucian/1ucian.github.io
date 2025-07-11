"""Minimal Flask server for the InsightMate Electron app."""

import os

from flask import Flask
from dotenv import load_dotenv

from server_common import register_common, WEB_DIR


load_dotenv()

# Serve files from the shared web directory.  ``static_url_path`` is set to
# ``''`` so URLs match ``/index.html`` rather than ``/static/index.html``.
app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")

# Register routes such as ``/chat`` and ``/reminders`` defined in
# ``server_common.py``.
register_common(app)


if __name__ == "__main__":
    # Listen on all interfaces so the Electron client can connect locally.
    app.run(host="0.0.0.0", port=5000)
