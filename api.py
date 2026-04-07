from flask import Flask, request, jsonify

def create_app(shared_fault):
    app = Flask(__name__)

    @app.route("/inject", methods=["POST"])
    def inject():
        data = request.json or {}
        fault = data.get("fault", "none")

        shared_fault["type"] = fault

        return jsonify({"status": "ok", "fault": fault})

    @app.route("/status", methods=["GET"])
    def status():
        return jsonify(dict(shared_fault))

    return app