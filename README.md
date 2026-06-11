# ⚡ Fault Injection & Self-Healing System

A production-grade chaos engineering platform built in Python. Injects real failures into a running process — crashes, memory spikes, CPU floods, disk I/O storms, network exhaustion — then measures how fast the system recovers. The same pattern powers Netflix Chaos Monkey and Google's DiRT testing framework.

> **Why this exists:** Most developers never intentionally break their systems. They wait for production to do it for them. This project flips that — controlled failure, measurable recovery, observable behaviour.

![Dashboard](dashboard%201.png)
![Event History](dashboard%202.png)

---

## 📊 Real Metrics (live run)

| Metric | Value |
|---|---|
| Total faults injected | 22 |
| Process crashes | 6 |
| Auto-recoveries | 6 |
| Crash survival rate | **100%** |
| Fault types tested | crash, memory, cpu_spike, disk_flood, network_block, delay |
| Scheduler interval | 5s (stress test mode) |

6 crashes. 6 recoveries. Zero manual intervention.

---

## 🏗️ Architecture
                ┌─────────────────┐
                │   main.py       │  Entry point — spawns all threads + processes
                └────────┬────────┘
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌───────────────┐
│ supervisor.py │  │ fault_       │  │  monitor.py   │
│               │  │ injector.py  │  │  (psutil)     │
│ Watches proc  │  │              │  │               │
│ RLock restart │  │ 6 fault types│  │ CPU + memory  │
│ Measures MTTR │  │ Non-blocking │  │ 1s polling    │
└───────┬───────┘  └──────┬───────┘  └───────┬───────┘
│                 │                  │
▼                 ▼                  ▼
┌───────────────────────────────────────────────────┐
│              api.py  (Flask REST)                  │
│  /inject  /metrics  /history  /export  /schedule  │
│  Auth: X-API-Token header on all write endpoints  │
└───────────────────────┬───────────────────────────┘
│
▼
┌───────────────────────┐
│  static/index.html    │
│  Live dashboard       │
│  Sparkline charts     │
│  Scheduler UI         │
│  CSV export           │
└───────────────────────┘

---

## 🔧 Fault Types

| Fault | What it does | Duration |
|---|---|---|
| `crash` | Terminates the target process | Instant |
| `delay` | Simulates latency spike (background thread) | 10s |
| `memory` | Allocates 100MB bytearray | 5s then released |
| `cpu_spike` | Burns 2 CPU cores at 100% | 8s |
| `network_block` | Opens 200 sockets, proper SO_LINGER cleanup | 5s |
| `disk_flood` | Writes 50MB to disk, holds, deletes | 5s |
| `random` | Picks any of the above randomly | — |

---

## 🐛 Bugs Fixed

### 1. Deadlock — threading.Lock → threading.RLock
supervisor.py acquired process_lock to check liveness, then tried to acquire it again in the same thread to restart. threading.Lock is not reentrant — guaranteed deadlock on first crash. Fixed with RLock.

### 2. delay fault blocked the API thread
time.sleep(10) was called directly in the injector, freezing Flask response. Moved to background daemon thread.

### 3. Memory fault was 4MB not a real spike
Original: list of 500K ints (~4MB). Replaced with bytearray(100 * 1024 * 1024) — actual 100MB visible in charts.

### 4. Socket leak in network_block
Sockets closed with s.close() only — left in TIME_WAIT, exhausting OS socket table. Fixed with SO_LINGER + shutdown(SHUT_RDWR) before close.

### 5. No authentication on write endpoints
Any process on local network could inject faults. Added X-API-Token header validation on /inject, /schedule, /clear-history.

### 6. Hardcoded configuration
Port, host, token, intervals all hardcoded. Moved to .env + config.py via python-dotenv.

---

## 🚀 Quick Start

```bash
git clone https://github.com/DonaRashmitha-dev/Fault-injection-system.git
cd Fault-injection-system
pip install -r requirements.txt
python main.py
```

Open `http://localhost:5000` — enter API token from `.env` — inject faults.

### Docker

```bash
docker compose up
```

---

## 🔌 REST API

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | — | Dashboard |
| GET | `/metrics` | — | Fault counts, MTTR, CPU, memory |
| GET | `/status` | — | Process alive/dead, current fault |
| GET | `/history` | — | Full event log |
| GET | `/export` | — | Download history as CSV |
| POST | `/inject` | ✓ | Inject a fault {"fault": "crash"} |
| POST | `/schedule` | ✓ | Start/stop scheduled injection |
| POST | `/clear-history` | ✓ | Clear event log |

Auth: X-API-Token header. Token set in .env.

---

## ⚙️ Configuration

```env
PORT=5000
HOST=127.0.0.1
API_TOKEN=changeme123
MONITOR_INTERVAL=1
SCHEDULER_MIN_INTERVAL=5
```

---

## 🔗 Related Projects

**[LOG.INTEL](https://github.com/DonaRashmitha-dev/log-intelligence-platform)** — This system is the data source for LOG.INTEL, an AI-powered log intelligence platform. Fault events generated here are ingested by LOG.INTEL, which detects anomalies statistically and answers questions about system health in plain English.

---

## 🛠️ Tech Stack

`Python 3.11` · `Flask` · `psutil` · `threading` · `multiprocessing` · `Docker`
