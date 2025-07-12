from llm_client import gpt
from server_common import _load_model
import json


def summarize_text(obj):
    """Summarize ``obj`` using Qwen. Lists are converted to text."""
    if obj in (None, "", "\u26a0\ufe0f No previous tool output"):
        return "\u26a0\ufe0f Nothing to summarize."
    if isinstance(obj, list):
        text = "\n".join(
            (it.get("subject") or it.get("title", "")) + " " + it.get("snippet", "")
            for it in obj
        )
    elif isinstance(obj, dict):
        text = json.dumps(obj, indent=2)[:4000]
    else:
        text = str(obj)
    prompt = "Write a single coherent paragraph summarising this:\n" + text
    return gpt(prompt, model="qwen3:30b")
