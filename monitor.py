import psutil
import time
from logger import log_event

def monitor():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent

        msg = f"CPU={cpu}% MEM={memory}%"
        print(f"📊 {msg}")
        log_event("MONITOR", msg)

        time.sleep(2)