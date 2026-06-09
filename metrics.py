from datetime import datetime, timezone
import threading

lock = threading.Lock()

_shared_metrics = None
_shared_history = None
_HISTORY_MAX = 100


def init_metrics(shared_metrics, shared_history):
    global _shared_metrics, _shared_history
    _shared_metrics = shared_metrics
    _shared_history = shared_history


def update_metric(key):
    with lock:
        if _shared_metrics is not None and key in _shared_metrics:
            _shared_metrics[key] = _shared_metrics[key] + 1


def get_metrics():
    with lock:
        if _shared_metrics is None:
            return {"total_faults": 0, "crashes": 0, "recoveries": 0}
        return dict(_shared_metrics)


def record_event(fault_type, outcome):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fault_type": fault_type,
        "outcome": outcome,
    }
    with lock:
        if _shared_history is not None:
            _shared_history.append(entry)
            while len(_shared_history) > _HISTORY_MAX:
                _shared_history.pop(0)


def get_history():
    with lock:
        if _shared_history is None:
            return []
        return list(_shared_history)


def clear_history():
    with lock:
        if _shared_history is not None:
            del _shared_history[:]