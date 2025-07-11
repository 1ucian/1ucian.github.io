from llm_client import gpt


def summarize_text(text: str) -> str:
    """Return a short summary of the provided text using the configured LLM."""
    prompt = "Summarize the following text:\n\n" + text
    return gpt(prompt)
