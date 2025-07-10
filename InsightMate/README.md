# InsightMate

## Windows GUI

Run the simple chat interface on Windows using Python and Tkinter. Install
the required packages first using `pip install -r requirements.txt` (or run
`windows_setup.ps1` which creates a virtual environment and installs the
dependencies for you). This requirements file now includes `apscheduler` and
`pywin32`, so make sure it completes successfully:

```powershell
cd Scripts
python windows_gui.py
```

The GUI automatically starts the backend chat server and lets you send
queries to it. If you see connection errors, the server may have failed to
start. Check `Scripts/chat_server.log` for any errors.

Copy `.env.example` to `.env` and fill in your `OPENAI_API_KEY` so the
assistant can access GPT‑4.

