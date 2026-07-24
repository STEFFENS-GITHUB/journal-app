import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".journal-cli.conf"

def save_tokens(access_token: str, refresh_token: str) -> None:
    CONFIG_PATH.write_text(json.dumps({"access_token": access_token, "refresh_token": refresh_token}))
    os.chmod(CONFIG_PATH, 0o600)

def load_tokens() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def clear_tokens() -> None:
    CONFIG_PATH.unlink(missing_ok=True)
