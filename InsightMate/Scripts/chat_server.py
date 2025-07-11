import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from assistant_router import route
from reminder_scheduler import list_reminders, list_tasks
from memory_db import get_recent_messages

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, '../web')
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message') or data.get('query') or ''
    reply = route(message)
    return jsonify({'reply': reply})


@app.route('/reminders', methods=['GET'])
def reminders():
    rems = list_reminders()
    data = [{'id': r[0], 'text': r[1], 'time': r[2]} for r in rems]
    return jsonify({'reminders': data})


@app.route('/tasks', methods=['GET'])
def tasks():
    tasks = list_tasks()
    data = [{'id': t[0], 'type': t[1], 'description': t[2], 'schedule': t[3]} for t in tasks]
    return jsonify({'tasks': data})


@app.route('/memory', methods=['GET'])
def memory():
    messages = get_recent_messages()
    data = [
        {'ts': m[0], 'sender': m[1], 'text': m[2]}
        for m in messages
    ]
    return jsonify({'messages': data})


@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
