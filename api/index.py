from __future__ import annotations

import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq

from .service import BackendError, ConfigurationError, TaskService, ValidationError, build_service

app = Flask(__name__)
CORS(app)


def _groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key) if api_key else None


def _service() -> TaskService:
    return build_service()


def _success(payload, status=200):
    return jsonify(payload), status


def _failure(error: Exception, status: int = 500):
    return jsonify({"ok": False, "error": {"type": error.__class__.__name__, "message": str(error)}}), status


@app.route("/api/health", methods=["GET"])
def health_check():
    return _success({"ok": True, "status": "online", "service": "Dynamic Daily Task Engine"})


@app.route("/api/readiness", methods=["GET"])
def readiness_check():
    try:
        service = _service()
        payload = service.readiness_report()
        payload["ok"] = payload["ready"]
        return _success(payload, 200 if payload["ready"] else 503)
    except Exception as exc:
        return _failure(exc, 503)


@app.route("/api/intake", methods=["POST"])
def intake():
    body = request.get_json(silent=True) or {}
    text = body.get("text")
    if not text:
        return _failure(ValidationError("text is required"), 400)

    try:
        groq_client = _groq_client()
        if groq_client is None:
            raise ConfigurationError("GROQ_API_KEY is required")
        plan = _service().generate_plan_from_text(text, groq_client)
        result = _service().create_goal_plan(plan, source=body.get("source", "intake"))
        return _success({"ok": True, "status": "success", "plan": result}, 201)
    except ValidationError as exc:
        return _failure(exc, 400)
    except ConfigurationError as exc:
        return _failure(exc, 503)
    except BackendError as exc:
        return _failure(exc, 502)
    except Exception as exc:
        return _failure(exc, 500)


@app.route("/api/plan", methods=["POST"])
def create_plan():
    body = request.get_json(silent=True) or {}
    try:
        result = _service().create_goal_plan(body, source=body.get("source", "api"))
        return _success({"ok": True, "status": "success", "plan": result}, 201)
    except ValidationError as exc:
        return _failure(exc, 400)
    except BackendError as exc:
        return _failure(exc, 502)


@app.route("/api/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    body = request.get_json(silent=True) or {}
    try:
        result = _service().update_task(task_id, body)
        return _success({"ok": True, "status": "success", "task": result})
    except ValidationError as exc:
        return _failure(exc, 400)
    except BackendError as exc:
        return _failure(exc, 502)


@app.route("/api/review", methods=["GET", "POST"])
def review():
    service = _service()
    if request.method == "GET":
        return _success({"ok": True, "status": "success", "review": service.review_snapshot()})

    body = request.get_json(silent=True) or {}
    try:
        updates = body.get("updates") or []
        result = service.apply_review_updates(updates)
        return _success({"ok": True, "status": "success", "review": result})
    except ValidationError as exc:
        return _failure(exc, 400)
    except BackendError as exc:
        return _failure(exc, 502)


@app.route("/api/status", methods=["GET"])
def status_review():
    service = _service()
    return _success({"ok": True, "status": "success", "review": service.review_snapshot()})


@app.route("/api/schedule", methods=["POST"])
def schedule():
    try:
        body = request.get_json(silent=True) or {}
        from google_auth import get_calendar_service

        start_hour = int(body.get("start_hour", 7))
        buffer_minutes = int(body.get("buffer_minutes", 15))

        result = _service().schedule_pending_tasks(
            get_calendar_service(),
            start_hour=start_hour,
            buffer_minutes=buffer_minutes,
            timezone_name=body.get("time_zone"),
        )
        return _success({"ok": True, "status": "success", "schedule": result})
    except ValueError as exc:
        return _failure(ValidationError(str(exc)), 400)
    except ValidationError as exc:
        return _failure(exc, 400)
    except ConfigurationError as exc:
        return _failure(exc, 503)
    except BackendError as exc:
        return _failure(exc, 502)


@app.route("/api/process-brain-dump", methods=["POST"])
def process_brain_dump():
    return intake()


@app.errorhandler(404)
def not_found(_):
    return _failure(ValidationError("Route not found"), 404)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))