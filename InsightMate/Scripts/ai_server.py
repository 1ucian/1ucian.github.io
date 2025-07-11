import os
from flask import Flask, request, jsonify
import openai
from dotenv import load_dotenv
from assistant_router import route

app = Flask(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def chat_completion(model: str, messages: list[dict]) -> str:
    """Call the OpenAI chat completion API compatible with v1.x or older."""
    if hasattr(openai, "chat") and hasattr(openai.chat, "completions"):
        resp = openai.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content.strip()
    resp = openai.ChatCompletion.create(model=model, messages=messages)
    return resp["choices"][0]["message"]["content"].strip()

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
    reply = chat_completion("gpt-4", [{"role": "user", "content": prompt}])
    return jsonify({'reply': reply})


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    query = data.get('query', '')
    reply = route(query)
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(port=5000)
