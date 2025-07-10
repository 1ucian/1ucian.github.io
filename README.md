# 1ucian.me

This repository contains the source for my personal site as well as **InsightMate**, a simple desktop assistant. InsightMate uses local Python scripts to read your Gmail, Calendar and OneDrive data and lets you chat with GPT‑4 or Ollama.

## Running InsightMate on Windows

1. Install Python 3.
2. Open `InsightMate/Scripts` in a terminal.
3. Run `windows_setup.ps1` to create a virtual environment and launch the backend server, or run `python windows_gui.py` to open the chat window directly.
4. Copy `.env.example` to `.env` and, if you want to use GPT‑4, set
   `OPENAI_API_KEY`. Leave it empty to run the local Llama 3 model via
   [Ollama](https://ollama.ai/).
5. Place your Google API `credentials.json` in `InsightMate/Scripts` and run
   `python gmail_reader.py` once to authorize Gmail and Calendar access. This
   creates `token.json` for future runs.
6. Ensure [`ollama`](https://ollama.ai/) is installed. `windows_setup.ps1`
   automatically downloads the Llama 3 model with `ollama pull llama3`. A 4090
   GPU is used automatically when present.
7. Minimizing the chat window hides it to the system tray so it can run in the
   background. Use the tray icon to restore or quit InsightMate.
8. If the chat window shows connection errors, check
   `InsightMate/Scripts/chat_server.log` for details.
9. Conversation history, unread email summaries and calendar events are stored
   locally in `InsightMate/Scripts/memory.db`.

See [InsightMate/README.md](InsightMate/README.md) for more details.
