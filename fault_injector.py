import os
import time
import random
import socket
import threading
from metrics import update_metric, record_event
from supervisor import process_ref, process_lock

VALID_FAULTS = {
    "crash", "delay", "memory", "cpu_spike",
    "network_block", "disk_flood", "none", "random",
}

_RANDOM_POOL = [f for f in VALID_FAULTS if f not in ("none", "random")]

# Track open sockets so cleanup is guaranteed even if thread crashes
_active_sockets = []
_socket_lock = threading.Lock()


def inject_fault(shared_fault):
    fault = shared_fault.get("type", "none")

    if fault not in VALID_FAULTS:
        raise ValueError(f"Unknown fault type: {fault!r}. Valid: {sorted(VALID_FAULTS)}")

    if fault == "random":
        fault = random.choice(_RANDOM_POOL)

    print(f"\n💉 Fault requested: {fault}")

    # ── crash ──────────────────────────────────────────────────────────
    if fault == "crash":
        with process_lock:
            process = process_ref.get("process")
        if process and process.is_alive():
            _announce("CRASH")
            update_metric("total_faults")
            record_event(fault, "terminated")
            process.terminate()
            process.join()
            print("💥 PROCESS TERMINATED\n")
        else:
            print("❌ Process not alive — skipping crash")
            shared_fault["type"] = "none"
            return "none"

    # ── delay ──────────────────────────────────────────────────────────
    elif fault == "delay":
        _announce("DELAY (10s, background)")
        update_metric("total_faults")
        record_event(fault, "delay_started")
        def _delay():
            time.sleep(10)
            print("✅ Delay cleared\n")
        threading.Thread(target=_delay, daemon=True).start()

    # ── memory spike ───────────────────────────────────────────────────
    elif fault == "memory":
        _announce("MEMORY SPIKE (100MB, 5s)")
        update_metric("total_faults")
        record_event(fault, "memory_spike")
        def _mem():
            blob = bytearray(100 * 1024 * 1024)
            print(f"🧠 Allocated {len(blob) // (1024*1024)}MB\n")
            time.sleep(5)
            del blob
            print("✅ Memory released\n")
        threading.Thread(target=_mem, daemon=True).start()

    # ── cpu spike ──────────────────────────────────────────────────────
    elif fault == "cpu_spike":
        _announce("CPU SPIKE (100% x2 cores for 8s)")
        update_metric("total_faults")
        record_event(fault, "cpu_spike_started")
        def _cpu():
            deadline = time.time() + 8
            while time.time() < deadline:
                _ = sum(i * i for i in range(50_000))
            print("✅ CPU spike done\n")
        for _ in range(2):
            threading.Thread(target=_cpu, daemon=True).start()

    # ── network block ──────────────────────────────────────────────────
    elif fault == "network_block":
        _announce("NETWORK BLOCK (200 sockets for 5s)")
        update_metric("total_faults")
        record_event(fault, "network_block_started")
        def _net():
            sockets = []
            try:
                for _ in range(200):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                     __import__('struct').pack('ii', 1, 0))  # hard close, no TIME_WAIT
                        s.setblocking(False)
                        s.connect_ex(("127.0.0.1", 1))
                        sockets.append(s)
                        with _socket_lock:
                            _active_sockets.append(s)
                    except OSError:
                        break
                print(f"🌐 Opened {len(sockets)} sockets\n")
                time.sleep(5)
            finally:
                for s in sockets:
                    try:
                        s.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    try:
                        s.close()
                    except OSError:
                        pass
                with _socket_lock:
                    for s in sockets:
                        try:
                            _active_sockets.remove(s)
                        except ValueError:
                            pass
                print("✅ Network sockets released\n")
        threading.Thread(target=_net, daemon=True).start()

    # ── disk flood ─────────────────────────────────────────────────────
    elif fault == "disk_flood":
        _announce("DISK FLOOD (50MB write, 5s hold, delete)")
        update_metric("total_faults")
        record_event(fault, "disk_flood_started")
        def _disk():
            path = "_fault_disk_flood.tmp"
            try:
                chunk = b"x" * (1024 * 1024)
                with open(path, "wb") as f:
                    for _ in range(50):
                        f.write(chunk)
                        f.flush()
                print(f"💾 Wrote 50MB to {path}\n")
                time.sleep(5)
            finally:
                try:
                    os.remove(path)
                    print("✅ Disk flood file removed\n")
                except FileNotFoundError:
                    pass
        threading.Thread(target=_disk, daemon=True).start()

    else:
        print("✅ No fault\n")

    shared_fault["type"] = "none"
    return fault


def _announce(label: str) -> None:
    print(f"\n{'='*30}")
    print(f"⚠️  Injecting {label}")
    print(f"{'='*30}\n")
