import os
import json
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("LLM_MODEL", "qwen3:72b-a14b")

try:
    requests.get(BASE_URL, timeout=3)
except Exception:
    print(
        f"\u26a0\ufe0f Ollama not reachable at {BASE_URL}. Start with:  ollama serve && ollama run {MODEL_NAME}"
    )

# Backwards compatibility
OLLAMA_URL = BASE_URL


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

    payload = {"model": model, "messages": messages, "stream": False}
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat", json=payload, stream=True, timeout=120
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        logging.error("LLM %s", e)
        return f"\u26a0\ufe0f LLM error: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        logging.error("LLM call failed: %s", e)
        if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code == 404:
            return (
                f"\u26a0\ufe0f Model '{model}' not found. "
                f"Run `ollama pull {model}` or choose another model in Settings."
            )
        return f"\u26a0\ufe0f LLM error: {e}"
    return response.json()["message"]["content"].strip()
