# InsightMate

InsightMate is a Windows tray assistant with a floating chat window built using Electron and Python. It connects to GPT‑4 (or Ollama if `OPENAI_API_KEY` is not set) and can search your OneDrive files, manage reminders and execute local actions. Optional Gmail and Calendar access is provided via Google OAuth.

## Project Layout
- `Scripts/` – Python backend modules
- `electron/` – Electron tray application
- `setup.bat` – installs dependencies and launches the app

## Prerequisites
- Windows 10 or later with Python 3 and Node.js
- OpenAI API key exported as `OPENAI_API_KEY` (optional if using Ollama)
- `credentials.json` in `Scripts/` for Gmail and Calendar features

## Usage
From the `InsightMate` directory run:

```cmd
setup.bat
```

This installs Python and Node dependencies, starts `chat_server.py` and opens the tray chat window. Conversations are logged to `%USERPROFILE%\InsightMate\logs\chatlog.txt`.

## OneDrive Local Access

`onedrive_reader.py` automatically locates your OneDrive folder and indexes text, Markdown, Word and PDF documents. Queries about your files are handled locally and results appear in the chat.
