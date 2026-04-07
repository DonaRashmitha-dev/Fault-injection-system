import threading
import multiprocessing
import time
from supervisor import supervise
from fault_injector import inject_fault
from monitor import monitor
from dashboard import run_dashboard
from logger import log_event
from api import create_app
from multiprocessing import Manager


def run_api(shared_fault):
    print("🌐 Starting API on http://127.0.0.1:5000")
    app = create_app(shared_fault)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def fault_controller(shared_fault):
    while True:
        time.sleep(5)
        fault = inject_fault(shared_fault)
        log_event("FAULT", f"Injected: {fault}")


def main():
    print("🚀 FAULT INJECTION SYSTEM STARTED")

    manager = Manager()
    shared_fault = manager.dict({"type": "none"})

    # Start API as separate process
    api_process = multiprocessing.Process(target=run_api, args=(shared_fault,))
    api_process.start()

    # Start threads
    threads = [
        threading.Thread(target=supervise, daemon=True),
        threading.Thread(target=fault_controller, args=(shared_fault,), daemon=True),
        threading.Thread(target=monitor, daemon=True),
        threading.Thread(target=run_dashboard, daemon=True),
    ]

    for t in threads:
        t.start()

    while True:
        time.sleep(1)


# 🔥 THIS IS THE "BOTTOM" PART
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()