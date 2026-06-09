import threading
import multiprocessing
import time
from datetime import datetime, timezone
from supervisor import supervise
from fault_injector import inject_fault
from monitor import monitor, init_monitor
from logger import log_event
from api import create_app
from metrics import init_metrics
from multiprocessing import Manager


def run_api(shared_fault, shared_metrics, shared_monitor, shared_history, shared_status, shared_schedule):
    print("?? Starting API on http://127.0.0.1:5000")
    init_metrics(shared_metrics, shared_history)
    init_monitor(shared_monitor)
    app = create_app(shared_fault, shared_status, shared_schedule)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def fault_controller(shared_fault):
    while True:
        time.sleep(1)
        if shared_fault.get("type", "none") == "none":
            continue
        try:
            fault = inject_fault(shared_fault)
            log_event("FAULT", f"Injected: {fault}")
        except ValueError as e:
            log_event("FAULT", f"Invalid fault: {e}")
            shared_fault["type"] = "none"


def scheduler_thread(shared_fault, shared_schedule):
    while True:
        time.sleep(1)
        if not shared_schedule.get("active", False):
            continue
        interval = shared_schedule.get("interval", 30)
        fault = shared_schedule.get("fault", "random")
        last = shared_schedule.get("last_fired", 0)
        now = time.time()
        if now - last >= interval:
            shared_fault["type"] = fault
            shared_schedule["last_fired"] = now
            print(f"? Scheduler fired: {fault}")


def monitor_thread(shared_monitor):
    init_monitor(shared_monitor)
    monitor()


def main():
    print("?? FAULT INJECTION SYSTEM STARTED")
    print("?? Dashboard: http://127.0.0.1:5000")

    manager = Manager()
    shared_fault = manager.dict({"type": "none"})
    shared_metrics = manager.dict({
        "total_faults": 0,
        "crashes": 0,
        "recoveries": 0,
    })
    shared_monitor = manager.dict({
        "cpu": 0.0,
        "memory": 0.0,
        "timestamp": "",
    })
    shared_history = manager.list()
    shared_status = manager.dict({
        "alive": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
    shared_schedule = manager.dict({
        "active": False,
        "fault": "random",
        "interval": 30,
        "last_fired": 0,
    })

    init_metrics(shared_metrics, shared_history)

    api_process = multiprocessing.Process(
        target=run_api,
        args=(shared_fault, shared_metrics, shared_monitor, shared_history, shared_status, shared_schedule),
    )
    api_process.start()

    threads = [
        threading.Thread(target=supervise, args=(shared_status,), daemon=True),
        threading.Thread(target=fault_controller, args=(shared_fault,), daemon=True),
        threading.Thread(target=monitor_thread, args=(shared_monitor,), daemon=True),
        threading.Thread(target=scheduler_thread, args=(shared_fault, shared_schedule), daemon=True),
    ]

    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n?? Shutting down...")
        api_process.terminate()
        api_process.join()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()