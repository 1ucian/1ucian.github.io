from llm_client import gpt
from user_settings import get_selected_model
import json


def summarize_text(obj):
    """Summarize ``obj`` using the active language model."""
    if obj in (None, "", "\u26a0\ufe0f No previous tool output"):
        return "\u26a0\ufe0f Nothing to summarize."
    if isinstance(obj, list):
        text = "\n".join(
            (item.get("subject") or item.get("title", "")) + " " + item.get("snippet", "")
            for item in obj
        )
    elif isinstance(obj, dict):
        text = json.dumps(obj, indent=2)[:4000]
    else:
        text = str(obj)
    prompt = "Summarize this:\n" + text
    return gpt(prompt, model=get_selected_model())
