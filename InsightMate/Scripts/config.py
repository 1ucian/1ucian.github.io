import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_CONFIG = {
    'api_key': '',
    'llm': 'llama3',
    'theme': 'dark'
}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                cfg = {**DEFAULT_CONFIG, **data}
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f)


def get_api_key(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = load_config()
    return os.getenv('OPENAI_API_KEY') or cfg.get('api_key', '')


def get_llm(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = load_config()
    return cfg.get('llm', DEFAULT_CONFIG['llm'])


def get_theme(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = load_config()
    return cfg.get('theme', DEFAULT_CONFIG['theme'])
