from llm_client import gpt
from server_common import _load_model


def summarize_text(obj):
    """Summarize ``obj`` using Qwen. Lists are converted to bullet text."""
    if isinstance(obj, list):
        bulk = "\n".join(
            (it.get("subject") or it.get("title", "")) + " "
            + (it.get("snippet", "")[:120])
            for it in obj
            if isinstance(it, dict)
        )
        text = bulk
    else:
        text = str(obj)
    prompt = "Write one coherent paragraph summarizing:\n" + text
    return gpt(prompt, model="qwen3:30b-a3b")
