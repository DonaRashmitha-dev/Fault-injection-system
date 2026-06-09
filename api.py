from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from metrics import get_metrics, get_history, clear_history
from monitor import get_latest_metrics
import os

ALLOWED_FAULTS = ["crash", "delay", "memory", "random", "none"]


def create_app(shared_fault, shared_status=None, shared_schedule=None):
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app = Flask(__name__, static_folder=static_folder)
    CORS(app)

    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(static_folder, "index.html")

    @app.route("/inject", methods=["POST"])
    def inject():
        data = request.json or {}
        fault = data.get("fault", "none")
        if fault not in ALLOWED_FAULTS:
            return jsonify({"error": "invalid fault type", "allowed": ALLOWED_FAULTS}), 400
        shared_fault["type"] = fault
        return jsonify({"status": "ok", "fault": fault})

    @app.route("/metrics", methods=["GET"])
    def metrics():
        return jsonify({**get_metrics(), **get_latest_metrics()})

    @app.route("/history", methods=["GET"])
    def history():
        return jsonify(get_history())

    @app.route("/clear-history", methods=["POST"])
    def clear_hist():
        clear_history()
        return jsonify({"status": "ok"})

    @app.route("/status", methods=["GET"])
    def status():
        result = dict(shared_fault)
        if shared_status is not None:
            result.update(dict(shared_status))
        return jsonify(result)

    @app.route("/schedule", methods=["POST"])
    def schedule():
        if shared_schedule is None:
            return jsonify({"error": "scheduling not available"}), 500
        data = request.json or {}
        action = data.get("action")
        if action == "start":
            fault = data.get("fault", "random")
            interval = int(data.get("interval", 30))
            if fault not in ALLOWED_FAULTS:
                return jsonify({"error": "invalid fault"}), 400
            if interval < 5:
                return jsonify({"error": "interval must be >= 5s"}), 400
            shared_schedule["active"] = True
            shared_schedule["fault"] = fault
            shared_schedule["interval"] = interval
            return jsonify({"status": "started", "fault": fault, "interval": interval})
        elif action == "stop":
            shared_schedule["active"] = False
            return jsonify({"status": "stopped"})
        return jsonify({"error": "unknown action"}), 400

    @app.route("/schedule/status", methods=["GET"])
    def schedule_status():
        if shared_schedule is None:
            return jsonify({"active": False})
        return jsonify(dict(shared_schedule))

    return app