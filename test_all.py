"""
Tests for Fault Injection System
Run: pytest tests/ -v
"""
import time
import threading
import multiprocessing
import pytest

# ── metrics tests ────────────────────────────────────────────────────────────

def make_shared():
    """Return fresh in-memory metrics/history without multiprocessing.Manager."""
    from unittest.mock import MagicMock
    import sys, types

    # Patch metrics module with plain dicts for unit tests
    import importlib
    import metrics as m

    shared_metrics = {
        "total_faults": 0, "crashes": 0, "recoveries": 0,
        "last_mttr": None, "avg_mttr": None, "min_mttr": None,
    }
    shared_history = []
    m.init_metrics(shared_metrics, shared_history)
    return shared_metrics, shared_history


def test_update_metric_increments():
    from metrics import update_metric, get_metrics
    sm, sh = make_shared()
    update_metric("total_faults")
    update_metric("total_faults")
    assert sm["total_faults"] == 2


def test_update_metric_unknown_key_is_noop():
    from metrics import update_metric
    sm, sh = make_shared()
    update_metric("nonexistent_key")  # must not raise


def test_record_event_appends():
    from metrics import record_event, get_history
    sm, sh = make_shared()
    record_event("crash", "terminated")
    history = get_history()
    assert len(history) == 1
    assert history[0]["fault_type"] == "crash"
    assert history[0]["outcome"] == "terminated"


def test_clear_history():
    from metrics import record_event, clear_history, get_history
    sm, sh = make_shared()
    record_event("delay", "delay_started")
    clear_history()
    assert get_history() == []


def test_record_mttr_updates_avg():
    from metrics import record_mttr, get_metrics
    sm, sh = make_shared()
    record_mttr(1.0)
    record_mttr(3.0)
    m = get_metrics()
    assert m["avg_mttr"] == 2.0
    assert m["min_mttr"] == 1.0
    assert m["last_mttr"] == 3.0


def test_history_max_enforced():
    from metrics import record_event, get_history
    import metrics as m
    sm, sh = make_shared()
    original_max = m._HISTORY_MAX
    m._HISTORY_MAX = 5
    for i in range(10):
        record_event("crash", f"event_{i}")
    assert len(get_history()) == 5
    m._HISTORY_MAX = original_max


# ── logger tests ─────────────────────────────────────────────────────────────

def test_log_event_writes_json(tmp_path, monkeypatch):
    import logger
    log_path = str(tmp_path / "test_logs.jsonl")
    monkeypatch.setattr(logger, "_LOG_FILE", log_path)
    logger.log_event("TEST", "hello world")
    import json
    with open(log_path) as f:
        entry = json.loads(f.readline())
    assert entry["type"] == "TEST"
    assert entry["message"] == "hello world"
    assert "timestamp" in entry


def test_log_event_thread_safe(tmp_path, monkeypatch):
    import logger
    log_path = str(tmp_path / "concurrent_logs.jsonl")
    monkeypatch.setattr(logger, "_LOG_FILE", log_path)
    threads = [
        threading.Thread(target=logger.log_event, args=("T", f"msg{i}"))
        for i in range(50)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) == 50


# ── fault_injector tests ──────────────────────────────────────────────────────

def test_inject_fault_invalid_raises():
    from fault_injector import inject_fault
    shared = {"type": "explode"}
    with pytest.raises(ValueError, match="Unknown fault type"):
        inject_fault(shared)


def test_inject_fault_none_returns_none():
    from fault_injector import inject_fault
    shared = {"type": "none"}
    result = inject_fault(shared)
    assert result == "none"


def test_inject_fault_resets_shared():
    """After injection, shared_fault type must be 'none'."""
    from fault_injector import inject_fault
    shared = {"type": "none"}
    inject_fault(shared)
    assert shared["type"] == "none"


def test_inject_delay_nonblocking():
    """Delay fault must return quickly (background thread)."""
    from fault_injector import inject_fault
    import metrics
    sm, sh = make_shared()

    # Patch process_ref so crash path not hit
    import fault_injector as fi
    fi.process_ref["process"] = None

    shared = {"type": "delay"}
    start = time.time()
    inject_fault(shared)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Delay fault blocked for {elapsed:.2f}s — should be < 1s"


# ── api tests ─────────────────────────────────────────────────────────────────

@pytest.fixture
def app_client():
    from api import create_app
    shared_fault = {"type": "none"}
    shared_status = {"alive": True, "started_at": "2025-01-01T00:00:00+00:00", "last_mttr": None}
    shared_schedule = {"active": False, "fault": "random", "interval": 30, "last_fired": 0}

    import metrics, monitor
    sm, sh = make_shared()
    monitor.init_monitor({"cpu": 0.0, "memory": 0.0, "timestamp": ""})

    app = create_app(shared_fault, shared_status, shared_schedule)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, shared_fault


def test_inject_valid_fault(app_client):
    client, shared_fault = app_client
    resp = client.post("/inject", json={"fault": "crash"})
    assert resp.status_code == 200
    assert resp.get_json()["fault"] == "crash"
    assert shared_fault["type"] == "crash"


def test_inject_invalid_fault_returns_400(app_client):
    client, _ = app_client
    resp = client.post("/inject", json={"fault": "nuke"})
    assert resp.status_code == 400


def test_metrics_endpoint(app_client):
    client, _ = app_client
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_faults" in data
    assert "cpu" in data


def test_status_endpoint(app_client):
    client, _ = app_client
    resp = client.get("/status")
    assert resp.status_code == 200
    assert "alive" in resp.get_json()


def test_schedule_start_stop(app_client):
    client, _ = app_client
    resp = client.post("/schedule", json={"action": "start", "fault": "crash", "interval": 10})
    assert resp.status_code == 200
    resp = client.post("/schedule", json={"action": "stop"})
    assert resp.status_code == 200


def test_schedule_interval_too_short(app_client):
    client, _ = app_client
    resp = client.post("/schedule", json={"action": "start", "fault": "crash", "interval": 2})
    assert resp.status_code == 400


def test_history_and_clear(app_client):
    client, _ = app_client
    from metrics import record_event
    record_event("memory", "memory_spike")
    resp = client.get("/history")
    assert resp.status_code == 200
    client.post("/clear-history")
    resp = client.get("/history")
    assert resp.get_json() == []


def test_export_csv(app_client):
    client, _ = app_client
    from metrics import record_event
    record_event("crash", "terminated")
    resp = client.get("/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type
    assert b"fault_type" in resp.data
