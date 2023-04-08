import os
from pathlib import Path

DEFAULT_URL = os.getenv("BOTOY_URL") or "http://127.0.0.1:8086"

CONFIG_FILE_PATH = Path.cwd() / "botoy.json"
