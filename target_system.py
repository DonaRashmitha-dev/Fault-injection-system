import time
import math
import signal
import sys


def run_system():
    # Graceful SIGTERM handling so supervisor join() doesn't hang
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    counter = 0
    while True:
        _ = sum(math.sqrt(i) for i in range(20000))
        print(f"🟢 System tick {counter}")
        counter += 1
        time.sleep(1)
