import os
from flask import Flask, request, jsonify
from assistant_router import route

app = Flask(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message') or data.get('query') or ''
    reply = route(message)
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(port=5000)
