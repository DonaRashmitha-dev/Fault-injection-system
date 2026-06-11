import csv
import io
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from metrics import get_metrics, get_history, clear_history
from monitor import get_latest_metrics
from config import API_TOKEN

VALID_FAULTS = {"crash", "delay", "memory", "random", "none", "disk_flood", "cpu_spike", "network_block"}


def _check_auth():
    """Return True if request carries valid token."""
    token = request.headers.get("X-API-Token") or request.args.get("token")
    return token == API_TOKEN


def create_app(shared_fault, shared_status, shared_schedule):
    app = Flask(__name__, static_folder="static", static_url_path="")
    CORS(app)

    # ── Dashboard ──────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # ── Metrics (public — read only) ───────────────────────────────────
    @app.route("/metrics", methods=["GET"])
    def metrics():
        data = get_metrics()
        data.update(get_latest_metrics())
        return jsonify(data)

    # ── Inject fault (AUTH REQUIRED) ───────────────────────────────────
    @app.route("/inject", methods=["POST"])
    def inject():
        if not _check_auth():
            return jsonify({"error": "Unauthorized. Pass X-API-Token header."}), 401
        data = request.get_json(silent=True) or {}
        fault = data.get("fault", "none")
        if fault not in VALID_FAULTS:
            return jsonify({"error": f"Invalid fault '{fault}'. Valid: {sorted(VALID_FAULTS)}"}), 400
        shared_fault["type"] = fault
        return jsonify({"status": "ok", "fault": fault})

    # ── Status (public) ────────────────────────────────────────────────
    @app.route("/status", methods=["GET"])
    def status():
        payload = dict(shared_status) if shared_status else {}
        payload["current_fault"] = shared_fault.get("type", "none")
        return jsonify(payload)

    # ── History (public) ───────────────────────────────────────────────
    @app.route("/history", methods=["GET"])
    def history():
        return jsonify(get_history())

    @app.route("/clear-history", methods=["POST"])
    def clear():
        if not _check_auth():
            return jsonify({"error": "Unauthorized. Pass X-API-Token header."}), 401
        clear_history()
        return jsonify({"status": "cleared"})

    # ── CSV export (public) ────────────────────────────────────────────
    @app.route("/export", methods=["GET"])
    def export():
        rows = get_history()
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["timestamp", "fault_type", "outcome"])
        writer.writeheader()
        writer.writerows(rows)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=fault_history.csv"},
        )

    # ── Scheduler (AUTH REQUIRED) ──────────────────────────────────────
    @app.route("/schedule", methods=["POST"])
    def schedule():
        if not _check_auth():
            return jsonify({"error": "Unauthorized. Pass X-API-Token header."}), 401
        data = request.get_json(silent=True) or {}
        action = data.get("action")
        if action == "start":
            fault = data.get("fault", "random")
            interval = int(data.get("interval", 30))
            if interval < 5:
                return jsonify({"error": "Minimum interval is 5 seconds"}), 400
            if fault not in VALID_FAULTS:
                return jsonify({"error": f"Invalid fault '{fault}'"}), 400
            shared_schedule["active"] = True
            shared_schedule["fault"] = fault
            shared_schedule["interval"] = interval
            shared_schedule["last_fired"] = 0
            return jsonify({"status": "scheduler started", "fault": fault, "interval": interval})
        elif action == "stop":
            shared_schedule["active"] = False
            return jsonify({"status": "scheduler stopped"})
        return jsonify({"error": "action must be 'start' or 'stop'"}), 400

    @app.route("/schedule/status", methods=["GET"])
    def schedule_status():
        return jsonify(dict(shared_schedule))

    return app
