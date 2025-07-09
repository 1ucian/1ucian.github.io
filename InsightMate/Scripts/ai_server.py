import os
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json() or {}
    imessage = data.get('imessage')
    email = data.get('email')
    calendar = data.get('calendar')
    onedrive = data.get('onedrive')
    user_prompt = data.get('prompt', '')
    prompt = (
        "You are an assistant helping the user with their data.\n"
        f"Latest iMessage: {imessage}\n"
        f"Unread email: {email}\n"
        f"Today's calendar events: {calendar}\n"
        f"Recent OneDrive files: {onedrive}\n"
        f"User question: {user_prompt}\n"
        "Answer appropriately."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    reply = response['choices'][0]['message']['content'].strip()
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(port=5000)
