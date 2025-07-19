# InsightMate

This folder contains the backend scripts and web assets for the InsightMate assistant. The assistant now delegates Gmail, Calendar and OneDrive access to an **n8n** workflow server. After installing the dependencies you can run `chat_server.py` to launch the web interface.

```bash
cd Scripts
python -m venv venv
venv/bin/pip install -r requirements.txt
python chat_server.py
```
Set `N8N_URL` and `N8N_API_KEY` in your `.env` so the scripts can reach your n8n instance. Then open `http://<host>:5000/` in your browser to start chatting.
