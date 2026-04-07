from datetime import datetime
import json

def log_event(event_type, message):
    log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "message": message
    }

    with open("logs.txt", "a") as f:
        f.write(json.dumps(log) + "\n")