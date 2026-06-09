import threading
from datetime import datetime, timezone

import psutil
import time
from logger import log_event

lock = threading.Lock()
_shared_monitor = None


def init_monitor(shared_monitor):
    global _shared_monitor
    _shared_monitor = shared_monitor


def get_latest_metrics():
    with lock:
        if _shared_monitor is None:
            return {"cpu": 0.0, "memory": 0.0, "timestamp": ""}
        return dict(_shared_monitor)


def monitor():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        snapshot = {
            "cpu": cpu,
            "memory": memory,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with lock:
            if _shared_monitor is not None:
                _shared_monitor.update(snapshot)

        msg = f"CPU={cpu}% MEM={memory}%"
        print(f"📊 {msg}")
        log_event("MONITOR", msg)

        time.sleep(2)
