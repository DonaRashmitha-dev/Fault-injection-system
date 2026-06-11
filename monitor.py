import threading
from datetime import datetime, timezone

import psutil
import time

from logger import log_event

_lock = threading.Lock()
_shared_monitor = None


def init_monitor(shared_monitor) -> None:
    global _shared_monitor
    _shared_monitor = shared_monitor


def get_latest_metrics() -> dict:
    with _lock:
        if _shared_monitor is None:
            return {"cpu": 0.0, "memory": 0.0, "timestamp": ""}
        return dict(_shared_monitor)


def monitor() -> None:
    """Polling loop — run in a dedicated daemon thread."""
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        snapshot = {
            "cpu": cpu,
            "memory": memory,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with _lock:
            if _shared_monitor is not None:
                _shared_monitor.update(snapshot)

        log_event("MONITOR", f"CPU={cpu}% MEM={memory}%")
        time.sleep(1)  # FIX: was 2s — now 1s for tighter dashboard updates
