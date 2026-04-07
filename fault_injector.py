import time
import random
from metrics import update_metric
from supervisor import process_ref, process_lock


def inject_fault(shared_fault):
    fault = shared_fault.get("type", "none")

    # Allow random mode
    if fault == "random":
        fault = random.choice(["crash", "delay", "memory", "none"])

    with process_lock:
        process = process_ref.get("process")

    # 🔍 Show current fault clearly
    print(f"\n👉 Current fault: {fault}")

    if fault == "crash":
        if process and process.is_alive():
            print("\n==========================")
            print("⚠️ Injecting CRASH NOW")
            print("==========================\n")

            update_metric("total_faults")

            process.terminate()
            process.join()

            print("💥 PROCESS TERMINATED\n")

        else:
            print("❌ Process not alive, cannot crash")

    elif fault == "delay":
        print("\n==========================")
        print("⚠️ Injecting DELAY")
        print("==========================\n")

        update_metric("total_faults")
        time.sleep(10)

    elif fault == "memory":
        print("\n==========================")
        print("⚠️ Injecting MEMORY SPIKE")
        print("==========================\n")

        update_metric("total_faults")
        _ = [i for i in range(5 * 10**5)]

    else:
        print("✅ No fault")

    # ✅ Reset fault after execution (VERY IMPORTANT)
    shared_fault["type"] = "none"

    return fault