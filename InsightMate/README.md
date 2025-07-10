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

Copy `.env.example` to `.env`. Set `OPENAI_API_KEY` only if you want to use
GPT‑4o, GPT‑4, **o4-mini** or **o4-mini-high**; leaving it blank will route chat requests to the local Llama 3 model via
[Ollama](https://ollama.ai/).

`windows_setup.ps1` will automatically download the Llama 3 model with
`ollama pull llama3` as long as Ollama is installed.

Place your Google API `credentials.json` in this directory and run
`python gmail_reader.py` once to authorize Gmail and Calendar access. The
resulting `token.json` is reused for future sessions.

Minimizing the window hides it to the system tray so InsightMate can keep
running in the background. Right‑click the tray icon to quit or open the
chat window again.

There is also a **Voice** button in the GUI. If you install `SpeechRecognition`
and `pyaudio`, you can dictate commands instead of typing them.

InsightMate keeps a local SQLite database named `memory.db` in the `Scripts`
folder. It records your chat history as well as any emails or calendar events
that were read during a session.
The desktop UI now includes a **Memory** column to view recent messages along
with sections for reminders and scheduled tasks.

