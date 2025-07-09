# InsightMate

InsightMate is a macOS menu bar assistant that summarizes your recent iMessage, Gmail, Calendar and OneDrive activity using a local Python backend and GPT‑4. It also provides a small chat window for interactive questions.

## Project Layout

- `InsightMateApp/` – SwiftUI menu bar application
- `Scripts/` – same Python sources for running outside the app

The Xcode target embeds the Python files from `InsightMateApp/Resources/py/` so they
run using the system `/usr/bin/python3`.

## Prerequisites

- macOS with Xcode 14 or later
- Python 3 (already available at `/usr/bin/python3` on macOS)
- An OpenAI API key exported as `OPENAI_API_KEY`
- Google OAuth `credentials.json` placed inside the `Scripts/` folder (used for Gmail and Calendar)
- Full Disk Access for Terminal or the built app so iMessage can be read

## Build & Run

1. Open `InsightMateApp/InsightMateApp.xcodeproj` in Xcode.
2. Build and run the `InsightMateApp` target.
   - On first launch the app starts `ai_server.py` in the background if it's not running.
   - It then executes `main.py` which collects iMessage, Gmail, Calendar and OneDrive data and posts it to the local server.
3. After the Python script finishes, a notification appears with the response
   (also written to `/tmp/insight_output.txt`).

## Running the Backend Manually

You can run the Python components without the SwiftUI app:

```bash
cd InsightMate/Scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python ai_server.py &
python main.py "What's new?"
```

The Flask server listens on `http://localhost:5000` and `main.py` writes the assistant reply to `/tmp/insight_output.txt`.

