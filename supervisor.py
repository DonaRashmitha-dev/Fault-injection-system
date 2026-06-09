import multiprocessing
import time
import threading
from datetime import datetime, timezone
from target_system import run_system
from logger import log_event
from metrics import update_metric

process_lock = threading.Lock()
process_ref = {"process": None}


def start_system():
    p = multiprocessing.Process(target=run_system)
    p.start()
    return p


def supervise(shared_status=None):
    with process_lock:
        process_ref["process"] = start_system()

    while True:
        with process_lock:
            p = process_ref["process"]
            alive = p is not None and p.is_alive()
            if shared_status is not None:
                shared_status["alive"] = alive

            if p is not None and not p.is_alive():
                crash_time = datetime.now(timezone.utc)
                log_event("CRASH", "System process crashed")
                update_metric("crashes")

                print("\n?? SYSTEM CRASH DETECTED")
                print("?? Restarting system...\n")

                process_ref["process"] = start_system()
                recovery_time = datetime.now(timezone.utc)
                mttr_seconds = round((recovery_time - crash_time).total_seconds(), 2)
                update_metric("recoveries")

                if shared_status is not None:
                    shared_status["alive"] = True
                    shared_status["mttr_last"] = mttr_seconds
                    shared_status["mttr_total"] = shared_status.get("mttr_total", 0.0) + mttr_seconds
                    shared_status["mttr_count"] = shared_status.get("mttr_count", 0) + 1

                print(f"? Recovered in {mttr_seconds}s\n")

        time.sleep(1)