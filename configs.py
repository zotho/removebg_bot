"""Config example:
{
  "service_url": "https://www.remove.bg/upload",
  "proxy_host": "PROXY HOSTNAME",
  "proxy_port": "PROXY PORT",
  "image_server_port": "YOUR SERVER PORT",
  "image_server_host": "YOUR SERVER HOSTNAME",
  "image_server_folder_path": "imgs",
  "image_server_processed_folder_path": "processed",
  "image_server_temp_path": "temp",
  "tg_token": "YOUR CONFIG"
}
"""

import json
from pathlib import Path


CONFIG_PATH: Path = Path("config.json")
with CONFIG_PATH.open() as config_file:
    CONFIG = json.load(config_file)

# Validate json
assert all(isinstance(value, str) for value in CONFIG.values()), "JSON is invalid (all values must be string)"

SERVICE_URL = CONFIG["service_url"]
PROXY_HOST = CONFIG["proxy_host"]
PROXY_PORT = CONFIG["proxy_port"]
IMAGE_SERVER_HOST = CONFIG["image_server_host"]
IMAGE_SERVER_PORT = CONFIG["image_server_port"]
IMAGE_SERVER_FOLDER_PATH = CONFIG["image_server_folder_path"]
IMAGE_SERVER_PROCESSED_FOLDER_PATH = CONFIG["image_server_processed_folder_path"]
IMAGE_SERVER_TEMP_PATH = CONFIG["image_server_temp_path"]
TG_TOKEN = CONFIG["tg_token"]
