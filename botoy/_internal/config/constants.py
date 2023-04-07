import os
from pathlib import Path

DEFAULT_HOST = os.getenv("BOTOY_HOST") or "http://127.0.0.1"
DEFAULT_PORT = int(os.getenv("BOTOY_PORT") or 8086)

CONFIG_FILE_PATH = Path.cwd() / "botoy.json"
