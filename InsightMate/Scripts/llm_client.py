import os
import requests
import json

BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def gpt(prompt: str, model: str) -> str:
    """Return a chat completion for ``prompt`` using ``model``."""
    return chat_completion(model, [{"role": "user", "content": prompt}])


def chat_completion(model: str, messages: list[dict]) -> str:
    if model.startswith("gpt-"):
        import openai
        return openai.ChatCompletion.create(
            model=model,
            messages=messages
        )["choices"][0]["message"]["content"].strip()

    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": True},
            stream=True
        )
        response.raise_for_status()
    except Exception as e:
        if "404" in str(e):
            return "\u26a0\ufe0f Qwen API endpoint not found. Is Ollama running?"
        raise

    full_reply = ""
    for line in response.iter_lines():
        if not line:
            continue
        if line.startswith(b'data: '):
            line = line[6:]
        try:
            chunk = line.decode("utf-8").strip()
            if chunk == "[DONE]":
                break
            content = json.loads(chunk).get("message", {}).get("content", "")
            full_reply += content
        except Exception as e:
            full_reply += f"\n\u26a0\ufe0f Stream decode error: {e}"
            break

    return full_reply.strip()
