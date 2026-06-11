import multiprocessing
import time
import threading
from target_system import run_system
from logger import log_event
from metrics import update_metric

# FIX: RLock instead of Lock — supervisor re-acquires lock inside same thread
process_lock = threading.RLock()
process_ref = {"process": None}


def start_system():
    p = multiprocessing.Process(target=run_system)
    p.start()
    return p


def supervise(shared_status=None):
    with process_lock:
        process_ref["process"] = start_system()

    while True:
        time.sleep(1)
        with process_lock:
            p = process_ref["process"]

            if p is not None and not p.is_alive():
                crash_time = time.time()
                log_event("CRASH", "System process crashed")
                update_metric("crashes")
                print("\n🚨 SYSTEM CRASH DETECTED")
                print("🔄 Restarting system...\n")

                new_p = start_system()
                process_ref["process"] = new_p  # no nested lock needed — RLock reentrant

                recovery_time = time.time()
                mttr = round(recovery_time - crash_time, 3)
                update_metric("recoveries")
                log_event("RECOVERY", f"Restarted in {mttr}s")
                print(f"✅ Restarted. MTTR={mttr}s\n")

                # Push MTTR into shared_status if provided
                if shared_status is not None:
                    shared_status["last_mttr"] = mttr
                    shared_status["alive"] = True
