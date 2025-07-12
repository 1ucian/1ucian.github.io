from llm_client import gpt
from user_settings import get_selected_model


def summarize_text(text_or_list):
    """Summarize a string or list of items using Qwen."""
    if isinstance(text_or_list, list):
        text = "\n".join(str(item) for item in text_or_list)
    else:
        text = str(text_or_list)
    prompt = "Summarize this:\n" + text
    model = get_selected_model()
    return gpt(prompt, model=model)
