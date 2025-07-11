# 1ucian.me

This repository contains the source for my personal site as well as **InsightMate**, a simple desktop assistant. InsightMate uses local Python scripts to read your Gmail, Calendar and OneDrive data and lets you chat with GPT‑4o, GPT‑4 or Ollama. See [PRD.md](PRD.md) for product requirements and the feature roadmap.

## Running InsightMate on Windows

1. Install **Python 3** and **Node.js** (for the Electron interface).
2. Open the `InsightMate` folder in a terminal.
3. For the full desktop app run `setup.bat`. This sets up a Python environment, installs Node dependencies and launches the Electron UI.
4. If you only want the lightweight Tkinter GUI, open `InsightMate/Scripts` and run `windows_setup.ps1` to create the virtual environment and start the backend server, or run `python windows_gui.py` to open the chat window directly. If the window closes immediately it usually means a required package is missing – run `pip install -r requirements.txt` (or `windows_setup.ps1`) from a terminal so you can see any error messages. If `pip` fails with a `textract` error, downgrade to `pip` 23 (`python -m pip install pip==23.3`) or install `textract==1.6.3` manually.
5. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want to use GPT-4o or GPT-4. You can also leave it blank and configure the key later from the **Settings** window. Without a key, InsightMate talks to the local Llama 3 model via [Ollama](https://ollama.ai/).
6. Place your Google API `credentials.json` in `InsightMate/Scripts` and run `python gmail_reader.py` once to authorize Gmail and Calendar access. This creates `token.json` for future runs.
7. Ensure [`ollama`](https://ollama.ai/) is installed. `windows_setup.ps1` automatically downloads the Llama 3 model with `ollama pull llama3`. A 4090 GPU is used automatically when present.
8. Minimizing the chat window hides it to the system tray so it can run in the background. Use the tray icon to restore or quit InsightMate.
9. Open the **Settings** window (via the tray menu or the new button at the top of the chat window) to update your API key, choose between GPT-4o, GPT-4, **o4-mini**, **o4-mini-high** or Llama 3, and toggle between light and dark themes. Your last selections are remembered for the next run.
10. Use the **Voice** button to dictate a query if `speech_recognition` and `pyaudio` are installed.
11. If the chat window shows connection errors, check `InsightMate/Scripts/chat_server.log` for details.
12. Conversation history, unread email summaries and calendar events are stored locally in `InsightMate/Scripts/memory.db`. Settings are written to `InsightMate/Scripts/config.json`.
13. To launch the Electron interface manually after the chat server is running, change to `InsightMate/electron` and run `npm start`. `setup.bat` performs this automatically when you run it.
14. The Electron UI now shows **Reminders**, **Tasks** and a **Memory** panel so you can review scheduled jobs and recent conversations.

See [InsightMate/README.md](InsightMate/README.md) for more details.

## MCP Integration
InsightMate leverages the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) platform to centralize configuration and neatly integrate all components.
