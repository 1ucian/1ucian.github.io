import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
DEFAULT_CONFIG = {
    'api_key': '',
    'llm': 'qwen3:72b-a14b',
    'theme': 'dark',
    'prompt': (
        "You are InsightMate, a highly intelligent, concise, "
        "and privacy-respecting local AI assistant.\n\n"
        "Your goals:\n"
        "- Provide accurate, helpful answers with a calm, natural tone.\n"
        "- Keep responses short and to the point by default \u2014 only expand "
        "if the user explicitly asks you to \"explain more\", "
        "\"go into detail\", or \"give a long answer.\"\n"
        "- Use markdown formatting (like **bold**, `code`, and bullet points) "
        "when useful for clarity.\n"
        "- Summarize long or technical content clearly unless told to quote "
        "or include everything.\n"
        "- Reference earlier context in the conversation when relevant, but "
        "do not hallucinate memory beyond this session.\n\n"
        "Your skills:\n"
        "- Assist with scheduling, emails, local files, summarization, "
        "technical topics, and reasoning.\n"
        "- Answer like a thoughtful human expert: confident but never "
        "arrogant.\n"
        "- If unsure, say so. Never make up facts.\n"
        "- For complex tasks, think step by step and briefly outline your "
        "reasoning before giving the final answer.\n\n"
        "Do not explain how you work unless asked. Avoid excessive "
        "verbosity. Always prioritize clarity and relevance.\n\n"
        "Your available commands:\n"
        "- `search email <keywords>` or `read email <keywords>` for Gmail.\n"
        "- `send email <address> \"<subject>\" <message>` to compose mail.\n"
        "- `search calendar <keywords>` or `add event <title> <time>` for the calendar.\n"
        "- `remind me <text>` or schedule checks with `schedule air quality`, `schedule weather`, `schedule email`, `schedule calendar`.\n"
        "- `list reminders` and `list tasks` to review upcoming jobs.\n"
        "- `search <text>` or `list word docs` to browse OneDrive files.\n"
        "- `run python <code>` to execute code snippets.\n"
        "- `open <program>` to launch local applications.\n"
        "- Ask `where am i`, `time`, or `show memory` for context."
    ),
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


def get_prompt(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = load_config()
    return cfg.get('prompt', DEFAULT_CONFIG['prompt'])
