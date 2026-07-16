"""App settings (BUILD_PLAN.md GD5.3): provider choice + local endpoint.

Stored as JSON in ~/.config/comrade-eq/config.json. API keys are NEVER
written here — they go to the OS keyring (service "comrade-eq"), with a
warning surfaced in the UI when keyring is unavailable.

Schema: {"provider": "auto"|"anthropic"|"openai",
         "base_url": str, "model": str}
Env vars (COMRADE_AI_PROVIDER, COMRADE_AI_BASE_URL, COMRADE_AI_MODEL,
ANTHROPIC_API_KEY, OPENAI_API_KEY) always win over this file.
"""

import json
import os

CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "comrade-eq",
)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "provider": "auto",  # auto: anthropic when a key exists, else local
    "base_url": "http://localhost:11434/v1",
    "model": "qwen2.5:7b",
}

KEYRING_SERVICE = "comrade-eq"


def load(path: str = CONFIG_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS and v})
    return merged


def save(config: dict, path: str = CONFIG_PATH) -> str:
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in config.items() if k in DEFAULTS and v})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2)
    os.replace(tmp, path)
    return path


def get(key: str, path: str = CONFIG_PATH):
    return load(path).get(key, DEFAULTS.get(key))


def set_api_key(username: str, key: str) -> bool:
    """Stores an API key in the OS keyring; returns False when unavailable."""
    try:
        import keyring

        keyring.set_password(KEYRING_SERVICE, username, key)
        return True
    except Exception:
        return False


def has_api_key(username: str) -> bool:
    try:
        import keyring

        return bool(keyring.get_password(KEYRING_SERVICE, username))
    except Exception:
        return False
