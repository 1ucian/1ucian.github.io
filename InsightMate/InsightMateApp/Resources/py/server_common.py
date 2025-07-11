import os
from flask import Blueprint, jsonify, request, current_app

from assistant_router import route_query

# Static files live three directories up in InsightMate/web
WEB_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web')

common_bp = Blueprint('common', __name__)

@common_bp.route('/')
def index():
    """Serve the web interface."""
    return current_app.send_static_file('index.html')

@common_bp.route('/chat', methods=['POST'])
def chat_route():
    data = request.get_json() or {}
    query = data.get('query', '')
    routed = route_query(query)
    if routed is not None:
        return jsonify({'reply': routed})
    return jsonify({'reply': ''})

def register_common(app):
    """Register common routes and static file handling on the given app."""
    app.register_blueprint(common_bp)
