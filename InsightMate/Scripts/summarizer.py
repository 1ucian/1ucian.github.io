from llm_client import gpt
from user_settings import get_selected_model


def summarize_text(text: str) -> str:
    """Return a short summary of the provided text using the configured LLM."""
    prompt = "Summarize the following text:\n\n" + text
    return gpt(prompt, get_selected_model())
