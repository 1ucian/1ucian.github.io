_selected_model = None

from config import load_config, get_llm

def set_selected_model(model: str) -> None:
    """Store the currently selected LLM model."""
    global _selected_model
    if model:
        _selected_model = model


def get_selected_model() -> str:
    """Return the selected LLM model, falling back to config."""
    if _selected_model:
        return _selected_model
    cfg = load_config()
    return get_llm(cfg)
