from llm_client import gpt
from server_common import _load_model


def summarize_text(text_or_list):
    """Summarize a string or list of items using Qwen."""
    if isinstance(text_or_list, list):
        text = "\n".join(str(item) for item in text_or_list)
    else:
        text = str(text_or_list)
    prompt = "Summarize this:\n" + text
    return gpt(prompt, model=_load_model())
