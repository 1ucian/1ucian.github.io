# 1ucian.me

This repository contains the source for my personal site as well as **InsightMate**, a simple desktop assistant. InsightMate uses local Python scripts to read your Gmail, Calendar and OneDrive data and lets you chat with GPT‑4 or Ollama.

## Running InsightMate on Windows

1. Install Python 3.
2. Open `InsightMate/Scripts` in a terminal.
3. Run `windows_setup.ps1` to create a virtual environment and launch the backend server, or run `python windows_gui.py` to open the chat window directly.
4. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
5. If the chat window shows connection errors, check `InsightMate/Scripts/chat_server.log` for details.

See [InsightMate/README.md](InsightMate/README.md) for more details.
