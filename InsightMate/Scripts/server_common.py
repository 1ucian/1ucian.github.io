import os
from flask import Blueprint, jsonify, request, current_app

from assistant_router import route
from user_settings import set_selected_model
from reminder_scheduler import list_reminders, list_tasks
from memory_db import get_recent_messages, clear_memory

WEB_DIR = os.path.join(os.path.dirname(__file__), '..', 'web')

common_bp = Blueprint('common', __name__)

@common_bp.route('/')
def index():
    """Serve the web interface."""
    return current_app.send_static_file('index.html')

@common_bp.route('/chat', methods=['POST'])
def chat_route():
    """Process a chat message and return the assistant's reply as JSON."""
    try:
        data = request.get_json() or {}
        message = data.get('message') or data.get('query') or ''
        model = data.get('model')
        if model:
            set_selected_model(model)
        reply = route(message)
        return jsonify({'reply': reply})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@common_bp.route('/reminders', methods=['GET'])
def reminders_route():
    rems = list_reminders()
    data = [{'id': r[0], 'text': r[1], 'time': r[2]} for r in rems]
    return jsonify({'reminders': data})

@common_bp.route('/tasks', methods=['GET'])
def tasks_route():
    tasks = list_tasks()
    data = [{'id': t[0], 'type': t[1], 'description': t[2], 'schedule': t[3]} for t in tasks]
    return jsonify({'tasks': data})

@common_bp.route('/memory', methods=['GET'])
def memory_route():
    messages = get_recent_messages()
    return jsonify(messages)


@common_bp.route('/memory/reset', methods=['POST'])
def memory_reset_route():
    clear_memory()
    return jsonify({'status': 'ok'})

def register_common(app):
    """Register common routes and static file handling on the given app."""
    app.register_blueprint(common_bp)

