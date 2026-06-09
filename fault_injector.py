import time
import random
from metrics import update_metric, record_event
from supervisor import process_ref, process_lock

ALLOWED_FAULTS = frozenset(["crash", "delay", "memory", "random", "none"])


def inject_fault(shared_fault):
    fault = shared_fault.get("type", "none")

    if fault not in ALLOWED_FAULTS:
        raise ValueError(
            f"Invalid fault type '{fault}'. Allowed: {sorted(ALLOWED_FAULTS)}"
        )

    if fault == "random":
        fault = random.choice(["crash", "delay", "memory", "none"])

    with process_lock:
        process = process_ref.get("process")

    print(f"\n?? Current fault: {fault}")

    outcome = "none"

    if fault == "crash":
        if process and process.is_alive():
            print("\n==========================")
            print("?? Injecting CRASH NOW")
            print("==========================\n")
            update_metric("total_faults")
            process.terminate()
            process.join()
            outcome = "terminated"
            print("?? PROCESS TERMINATED\n")
        else:
            outcome = "skipped_not_alive"
            print("? Process not alive, cannot crash")

    elif fault == "delay":
        print("\n==========================")
        print("?? Injecting DELAY")
        print("==========================\n")
        update_metric("total_faults")
        time.sleep(10)
        outcome = "delayed"

    elif fault == "memory":
        print("\n==========================")
        print("?? Injecting MEMORY SPIKE")
        print("==========================\n")
        update_metric("total_faults")
        data = bytearray(200 * 1024 * 1024)
        time.sleep(5)
        del data
        outcome = "memory_spike"

    else:
        print("? No fault")

    if fault != "none":
        record_event(fault, outcome)

    shared_fault["type"] = "none"
    return fault