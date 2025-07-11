# InsightMate Product Requirements

## Overview
InsightMate is a cross-platform personal assistant bundled within this repository along with the source for the 1ucian.me site. The assistant reads Gmail and Calendar data, searches OneDrive documents, and allows the user to chat with large language models such as GPT‑4o, GPT‑4 or a local Llama 3 model. A lightweight web UI provides reminders, task scheduling and a memory panel for recent conversations.

## Goals
- Provide a local, privacy‑conscious assistant that integrates with existing desktop data (Gmail, Calendar and OneDrive).
- Offer flexible language model choices (OpenAI API or local Llama 3 via Ollama).
- Allow quick interaction through an always‑on UI with optional voice input and system tray control.

## Current Features
- **Python backend** with Flask `chat_server.py` for routing assistant queries and scheduling reminders.
- **Web interface** (`web/index.html`) exposing chat, reminders, tasks and memory.
- **Data connectors** for Gmail/Calendar (`gmail_reader.py`, `calendar_reader.py`), OneDrive document search (`onedrive_reader.py`) and iMessage reading (`imessage_reader.py`).
- **Reminder and task scheduling** implemented with `apscheduler` in `reminder_scheduler.py` for air quality, weather, email and calendar checks.
- **Local SQLite memory** (`memory_db.py`) storing chat transcripts, email summaries, calendar events, reminders and tasks.
- **Email and calendar search** so the assistant can `search email` or `search calendar` for specific information on demand.
- **Sending email** via the `send email` command to compose and dispatch Gmail messages.

## Use Cases
1. Quickly query recent email or calendar events while chatting with GPT‑4o.
2. Search local OneDrive documents and receive summaries from the selected LLM.
3. Schedule reminders or periodic tasks (weather, air quality, email checks) that trigger desktop notifications.

## New Feature Phases
### Phase 1 – Polished Web Experience
- Improve onboarding with a guided setup for API keys and Google credentials.
- Add a unified settings panel to switch LLMs, themes and notification preferences.
- The web interface now includes this panel behind a **Settings** button so users can quickly change models or themes.

### Phase 2 – Expanded Integrations
- Introduce additional data connectors (e.g. Slack or Discord message summaries, local file indexing beyond OneDrive).
- Provide advanced search and filtering of the local memory database.
- Offer improved voice recognition using offline models where available.

### Phase 3 – Sync and Extensibility
- Implement optional cloud sync so reminders and history can roam between devices.
- Design a plugin architecture allowing community contributions for new data sources or automations.
- Publish API documentation and a web portal on 1ucian.me for user guides and updates.
- Leverage the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) platform so all components integrate seamlessly.

## Non‑Goals
- Running the assistant as a hosted web service (the focus remains on local execution).
- Acting as a full email or file client beyond fetching and summarizing data.

