import threading

lock = threading.Lock()

metrics = {
    "total_faults": 0,
    "crashes": 0,
    "recoveries": 0
}

def update_metric(key):
    with lock:
        if key in metrics:
            metrics[key] += 1

def get_metrics():
    with lock:
        return dict(metrics)