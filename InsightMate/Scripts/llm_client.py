import os
import json
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def gpt(prompt: str, model: str) -> str:
    """Return a chat completion for ``prompt`` using ``model``."""
    return chat_completion(model, [{"role": "user", "content": prompt}])


def chat_completion(model: str, messages: list[dict]) -> str:
    """Return a chat completion from Ollama or OpenAI."""
    if model.startswith("gpt-"):
        import openai
        client = openai.OpenAI()
        resp = client.chat.completions.create(model=model, messages=messages)
        return resp.choices[0].message.content.strip()

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return (
                f"\u26a0\ufe0f Model '{model}' not found. "
                f"Run `ollama pull {model}` or choose another model in Settings."
            )
        return f"\u26a0\ufe0f Qwen API error: {str(e)}"
    except Exception as e:
        return f"\u26a0\ufe0f Qwen API error: {str(e)}"
