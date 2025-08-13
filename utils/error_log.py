from db import db
from flask import Blueprint, request, jsonify
from db import db
from datetime import datetime,timezone
import traceback

error_bp = Blueprint("error", __name__)

def log_error_to_db(level, message, stack_trace,time,path,method,ip):
    try:
        error_doc = {
            "level": level,
            "message": message,
            "stack_trace": stack_trace,
            "timestamp": time,
            "path": path,
            "method": method,
            "client_ip": ip
        }
        result = db['error_logs_Backend'].insert_one(error_doc)
        print(f" Logged error: {result.inserted_id}")
    except Exception as e:
        print(f" Failed to log error: {e}")
    

@error_bp.route("/api/error", methods=["POST"])
def log_frontend_error():
    try:
        data = request.json

        error_doc = {
            "id": data.get("id"),
            "emp_id": data.get("emp_id"),
            "name": data.get("name"),
            "email": data.get("email"),
            "message": data.get("message", "Unknown error"),
            "stack_trace": data.get("stack", "No stack trace"),
            "timestamp": datetime.now(timezone.utc),
            "os": data.get("os"),
            "browser": data.get("browser"),
            "url": data.get("url"),
            "pathname": data.get("pathname"),
            "referrer": data.get("referrer"),
            "language": data.get("language"),
            "screen": data.get("screen"),
            "project": "Aapmor-Trainings"
        }

        result = db["error_logs_frontend"].insert_one(error_doc)
        print(f" Frontend error logged: {result.inserted_id}")

        return jsonify({"message": "Frontend error logged"}), 200

    except Exception as e:
        print(f" Failed to log frontend error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to log error"}), 500