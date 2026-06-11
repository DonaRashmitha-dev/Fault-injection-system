from datetime import datetime, timezone
import threading

lock = threading.Lock()

_shared_metrics = None
_shared_history = None
_HISTORY_MAX = 200  # bumped from 100

_mttr_samples = []  # local list — for avg MTTR calc


def init_metrics(shared_metrics, shared_history):
    global _shared_metrics, _shared_history
    _shared_metrics = shared_metrics
    _shared_history = shared_history


def update_metric(key: str) -> None:
    with lock:
        if _shared_metrics is not None and key in _shared_metrics:
            _shared_metrics[key] = _shared_metrics[key] + 1


def record_mttr(seconds: float) -> None:
    """Call from supervisor after each recovery with measured MTTR."""
    with lock:
        _mttr_samples.append(seconds)
        if _shared_metrics is not None:
            _shared_metrics["last_mttr"] = seconds
            _shared_metrics["avg_mttr"] = round(
                sum(_mttr_samples) / len(_mttr_samples), 3
            )
            _shared_metrics["min_mttr"] = round(min(_mttr_samples), 3)


def get_metrics() -> dict:
    with lock:
        if _shared_metrics is None:
            return {
                "total_faults": 0,
                "crashes": 0,
                "recoveries": 0,
                "last_mttr": None,
                "avg_mttr": None,
                "min_mttr": None,
            }
        return dict(_shared_metrics)


def record_event(fault_type: str, outcome: str) -> None:
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


def get_history() -> list:
    with lock:
        if _shared_history is None:
            return []
        return list(_shared_history)


def clear_history() -> None:
    with lock:
        if _shared_history is not None:
            del _shared_history[:]
