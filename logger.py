import json
import os
import threading
from datetime import datetime, timezone

_LOG_FILE = "logs.jsonl"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_lock = threading.Lock()


def log_event(event_type: str, message: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "message": message,
    }
    line = json.dumps(entry) + "\n"
    with _lock:
        # Rotate at 5 MB — rename to logs.jsonl.bak, start fresh
        if os.path.exists(_LOG_FILE) and os.path.getsize(_LOG_FILE) >= _MAX_BYTES:
            os.replace(_LOG_FILE, _LOG_FILE + ".bak")
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
