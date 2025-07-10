# InsightMate

## Windows GUI

Run the simple chat interface on Windows using Python and Tkinter. Install
the required packages first using `pip install -r requirements.txt` (or run
`windows_setup.ps1` which creates a virtual environment and installs the
dependencies for you):

```powershell
cd Scripts
python windows_gui.py
```

The GUI automatically starts the backend chat server and lets you send
queries to it. If you see connection errors, the server likely failed to
start because the dependencies were missing. Set `OPENAI_API_KEY` in your
environment or in a `.env` file so the assistant can access GPT-4.

