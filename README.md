# 1ucian.me

This repository contains the source for my personal site as well as **InsightMate**, a simple desktop assistant. InsightMate uses local Python scripts to read your Gmail, Calendar and OneDrive data and lets you chat with GPT‑4o, GPT‑4 or Ollama.

## Running InsightMate on Windows

1. Install Python 3.
2. Open `InsightMate/Scripts` in a terminal.
3. Run `windows_setup.ps1` to create a virtual environment and launch the backend server, or run `python windows_gui.py` to open the chat window directly.
4. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want to use
   GPT‑4o or GPT‑4. You can also leave it blank and configure the key later from the
   **Settings** window. Without a key, InsightMate talks to the local Llama 3
   model via [Ollama](https://ollama.ai/).
5. Place your Google API `credentials.json` in `InsightMate/Scripts` and run
   `python gmail_reader.py` once to authorize Gmail and Calendar access. This
   creates `token.json` for future runs.
6. Ensure [`ollama`](https://ollama.ai/) is installed. `windows_setup.ps1`
   automatically downloads the Llama 3 model with `ollama pull llama3`. A 4090
   GPU is used automatically when present.
7. Minimizing the chat window hides it to the system tray so it can run in the
   background. Use the tray icon to restore or quit InsightMate.
8. Open the **Settings** window (via the tray menu or button) to update your API
   key, choose between GPT‑4o, GPT‑4 or Llama 3, and switch themes.
9. Use the **Voice** button to dictate a query if `speech_recognition` and
   `pyaudio` are installed.
10. If the chat window shows connection errors, check
   `InsightMate/Scripts/chat_server.log` for details.
11. Conversation history, unread email summaries and calendar events are stored
    locally in `InsightMate/Scripts/memory.db`. Settings are written to
    `InsightMate/Scripts/config.json`.

See [InsightMate/README.md](InsightMate/README.md) for more details.
