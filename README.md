# Fault Injection & Self-Healing System

A real-time fault injection and monitoring dashboard built with Python and Flask. Inject faults into a running system process, watch live metrics, track recovery time, and export history — all from a browser UI.

---

## Why This Project

Real systems fail. Most developers never simulate failure intentionally — they wait for production to break. This project creates a controlled environment to inject crashes, memory spikes, and delays, then measures how fast the system recovers. The same patterns power Netflix Chaos Monkey and Google's DiRT testing.

---

## Architecture

```
         target_system.py
               │
               ▼
    supervisor.py ──► metrics.py ──► api.py (Flask)
          │                               │
    fault_injector.py              static/index.html (Dashboard UI)
          │
    monitor.py (psutil)
```

**Data flow:** `target_system` runs as a child process. `supervisor` watches it — on crash, restarts and records MTTR. `fault_injector` terminates / stalls / spikes the target on demand. `monitor` polls CPU + memory every second. All state flows into `metrics`, served by Flask to the dashboard.

---

## Features

- **Live Metrics** — CPU, memory, crash count, recovery count, MTTR updated every second
- **Fault Injection** — Manually trigger crash, delay, memory spike, or random faults
- **MTTR Tracking** — Measures last, average, and minimum Mean Time To Recovery
- **Fault Scheduling** — Auto-inject faults on a timer (e.g. crash every 30s)
- **Event History** — Timestamped log of every injected fault with outcomes
- **Export CSV** — Download full fault history as `.csv`
- **Process Supervision** — Crashed processes auto-detected and restarted

---

## Tech Stack

- **Backend** — Python 3.8+, Flask, Flask-CORS
- **Frontend** — Vanilla HTML/CSS/JS (no framework)
- **Process Management** — `multiprocessing`, `threading`
- **Monitoring** — `psutil`

---

## Project Structure

```
fault-injection-system/
├── main.py              # Entry point — starts all threads and processes
├── api.py               # Flask REST API (full routes + validation)
├── supervisor.py        # Watches target process, restarts on crash, tracks MTTR
├── fault_injector.py    # Applies faults — crash/delay/memory, all non-blocking
├── monitor.py           # Polls CPU and memory via psutil every second
├── metrics.py           # Shared state: counters, history, MTTR stats
├── logger.py            # Thread-safe JSON line logging with 5MB rotation
├── target_system.py     # Simulated workload (the process being injected)
├── requirements.txt
├── tests/
│   └── test_all.py      # pytest suite covering all modules
└── static/
    └── index.html       # Dashboard UI
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

Open: `http://127.0.0.1:5000`

### Run tests

```bash
pytest tests/ -v
```

---

## API Endpoints

| Method | Endpoint           | Description                                    |
| ------ | ------------------ | ---------------------------------------------- |
| GET    | `/`                | Dashboard UI                                   |
| GET    | `/metrics`         | CPU, memory, crash/recovery counts, MTTR stats |
| POST   | `/inject`          | Inject a fault `{ "fault": "crash" }`          |
| GET    | `/history`         | Full event history                             |
| POST   | `/clear-history`   | Clear event history                            |
| GET    | `/export`          | Download fault history as CSV                  |
| GET    | `/status`          | Process status + MTTR                          |
| POST   | `/schedule`        | Start/stop fault scheduler                     |
| GET    | `/schedule/status` | Current scheduler state                        |

### Fault types

`crash` · `delay` · `memory` · `random` · `none`

---

## Fault Scheduling

- Pick fault type + interval in seconds (minimum 5s)
- POST `{ "action": "start", "fault": "crash", "interval": 30 }` to `/schedule`
- POST `{ "action": "stop" }` to stop

---

## MTTR

After each crash the supervisor records how long restart took. Three values exposed on `/metrics`:

| Field       | Meaning                        |
| ----------- | ------------------------------ |
| `last_mttr` | Most recent recovery time (s)  |
| `avg_mttr`  | Average across all recoveries  |
| `min_mttr`  | Fastest recovery observed      |

---

## Observed Metrics (Sample Run)

Results from a 5-minute scheduled chaos run (crash fault every 30s):

| Metric              | Value       |
| ------------------- | ----------- |
| Faults injected     | 12          |
| Average MTTR        | 1.3 seconds |
| Fastest recovery    | 0.8 seconds |
| Crash survival rate | 100%        |

> Replace with real values after running. Use `GET /export` to download raw data.

---

## Connected Projects

This fault injector is the data source for **LOG.INTEL** — an AI-powered log intelligence platform that ingests these fault events, detects anomalies statistically, and answers questions about system health in plain English.

> Fault Injection System generates the chaos → LOG.INTEL interprets it.

---

## Screenshots

[![Dashboard](https://github.com/DonaRashmitha-dev/Fault-injection-system/raw/main/assets/dashboard.png)](https://github.com/DonaRashmitha-dev/Fault-injection-system/blob/main/assets/dashboard.png)

---

## License

MIT
