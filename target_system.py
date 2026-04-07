import time
import math

def run_system():
    counter = 0
    while True:
        _ = sum(math.sqrt(i) for i in range(20000))
        print(f"🟢 System running... {counter}")
        counter += 1
        time.sleep(1)
        