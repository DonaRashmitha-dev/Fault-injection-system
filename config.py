import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "127.0.0.1")
API_TOKEN = os.getenv("API_TOKEN", "changeme123")
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 1))
SCHEDULER_MIN_INTERVAL = int(os.getenv("SCHEDULER_MIN_INTERVAL", 5))
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5242880))
HISTORY_MAX = int(os.getenv("HISTORY_MAX", 200))
