import multiprocessing
import time
import threading
from target_system import run_system
from logger import log_event
from metrics import update_metric

# Shared process reference + lock
process_lock = threading.Lock()
process_ref = {"process": None}


def start_system():
    p = multiprocessing.Process(target=run_system)
    p.start()
    return p


def supervise():
    # Start system first time
    with process_lock:
        process_ref["process"] = start_system()

    while True:
        with process_lock:
            p = process_ref["process"]

        # Detect crash
        if p is not None and not p.is_alive():
            log_event("CRASH", "System process crashed")
            update_metric("crashes")

            print("\n🚨 SYSTEM CRASH DETECTED")
            print("🔄 Restarting system...\n")

            # Restart system
            new_p = start_system()

            with process_lock:
                process_ref["process"] = new_p

            # Track recovery
            update_metric("recoveries")

        time.sleep(1)