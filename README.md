# 1ucian.me

This repository contains the source for my personal site as well as **InsightMate**, a web‑based personal assistant. InsightMate uses local Python scripts to read your Gmail, Calendar and OneDrive data and lets you chat with GPT‑4o, GPT‑4 or Ollama. See [PRD.md](PRD.md) for product requirements and the feature roadmap.

## Running InsightMate

1. Install **Python 3** and ensure [`ollama`](https://ollama.ai/) is available if you want to use the local Qwen3 model.
2. Open the `InsightMate/Scripts` folder in a terminal and install the requirements:

   ```bash
   python -m venv venv
   venv/bin/pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set the environment values:
   - `OPENAI_API_KEY` for GPT‑4o or GPT‑4 (leave blank for Qwen3)
   - `EMAIL_DOMAIN` for recipient addresses without a domain
   - `LATITUDE` and `LONGITUDE` for weather and air‑quality checks
4. Place your Google API `credentials.json` in the `Scripts` directory and run `python gmail_reader.py` once to authorize Gmail and Calendar access. This creates `token.json` for future runs.
5. Start the server:

   ```bash
   python chat_server.py
   ```

6. Open `http://<host>:5000/` in your browser (replace `<host>` with your computer's address). The server listens on all network interfaces so it can be reached from other devices on the same network.

By default InsightMate uses the local **qwen3:30b-a3b** model. You can switch models from the Settings panel in the web UI.

Conversation history, unread email summaries and calendar events are stored locally in `memory.db`. Settings are written to `config.json`.

### Recent Updates
- Email and calendar actions support multi-turn conversations. If you start composing an email or event without all the details, the assistant will ask follow-up questions.
- Older chat history is pruned and summarized automatically so the database stays small.
- You can ask "what time is it" or "where am I" for current context.
- A `run python <code>` command lets you quickly execute snippets.
- Complex or ambiguous requests are handled with multi-step thinking and processing. The assistant now
  generates a short bullet plan, runs a brief analysis loop to refine it, then replies with both the plan,
  notes from that analysis and the final answer.

InsightMate understands commands like `search email <keywords>`, `read email <keywords>`, `search calendar <keywords>`, `add event <title> <time>` (you can also say `set appointment for 9pm sleep`) and `send email <address> <subject> <message>`.

Calendar events are scheduled in **Pacific Time** regardless of the host system's timezone.

See [InsightMate/README.md](InsightMate/README.md) for more details.

## MCP Integration
InsightMate leverages the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) platform to centralize configuration and neatly integrate all components.
