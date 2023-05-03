import os
from pathlib import Path

DEFAULT_URL = os.getenv("BOTOY_URL") or "http://127.0.0.1:8086"

local_config = Path.cwd() / "botoy.local.json"
if local_config.exists():
    CONFIG_FILE_PATH = local_config
else:
    CONFIG_FILE_PATH = Path.cwd() / "botoy.json"
