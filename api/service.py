from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .database import get_db_connection

PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}
PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}
DEFAULT_TIMEFRAME = "Daily"
DEFAULT_TIME_ZONE = os.environ.get("DEFAULT_TIME_ZONE", "Asia/Kolkata")

CANONICAL_MODEL = {
    "goals": {
        "table": "goals",
        "fields": ["id", "title", "timeframe", "status", "source", "created_at", "updated_at"],
    },
    "tasks": {
        "table": "tasks",
        "fields": [
            "id",
            "goal_id",
            "parent_task_id",
            "task_kind",
            "content",
            "level",
            "estimated_minutes",
            "remaining_minutes",
            "execution_order",
            "priority",
            "priority_rank",
            "status",
            "scheduled_start_at",
            "scheduled_end_at",
            "calendar_event_id",
            "previous_calendar_event_id",
            "rollover_count",
            "source",
            "created_at",
            "updated_at",
        ],
        "status": ["Pending", "Scheduled", "Completed", "Archived"],
    },
    "ideas": {
        "table": "ideas",
        "fields": ["id", "content", "status", "source", "created_at", "updated_at"],
    },
    "scheduling": {
        "fields": ["scheduled_start_at", "scheduled_end_at", "calendar_event_id", "previous_calendar_event_id"],
    },
    "rollover": {
        "fields": ["remaining_minutes", "rollover_count", "previous_calendar_event_id"],
    },
}


class BackendError(Exception):
    pass


class ValidationError(BackendError):
    pass


class ConfigurationError(BackendError):
    pass


class ExternalServiceError(BackendError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(payload: Any, *, name: str) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError(f"{name} must be a JSON object")
    return payload


def _clean_text(value: Any, *, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def _clean_int(value: Any, *, fallback: int) -> int:
    if value in (None, ""):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Expected an integer value, got {value!r}") from exc


def normalize_priority(value: Any) -> Dict[str, Any]:
    if isinstance(value, int):
        rank = min(3, max(1, value))
        return {"rank": rank, "label": PRIORITY_LABELS[rank]}

    label = _clean_text(value, fallback="Medium").title()
    rank = PRIORITY_MAP.get(label, 2)
    return {"rank": rank, "label": PRIORITY_LABELS[rank]}


def parse_time_zone(value: Optional[str] = None):
    zone_name = value or DEFAULT_TIME_ZONE
    try:
        return ZoneInfo(zone_name), zone_name
    except ZoneInfoNotFoundError:
        return timezone.utc, "UTC"


def _ordered_tasks(rows: List[Dict[str, Any]], *, status: Optional[str] = None) -> List[Dict[str, Any]]:
    filtered = [row for row in rows if not row.get("parent_task_id")]
    if status:
        filtered = [row for row in filtered if row.get("status") == status]
    return sorted(
        filtered,
        key=lambda row: (
            row.get("priority_rank", 2),
            row.get("execution_order", 999),
            row.get("id", 0),
        ),
    )


class TaskService:
    def __init__(self, client=None):
        self.client = client or get_db_connection()

    def readiness_report(self) -> Dict[str, Any]:
        missing_env = [name for name in ("SUPABASE_URL", "SUPABASE_KEY") if not os.environ.get(name)]
        table_status: Dict[str, str] = {}
        for table_name in ("goals", "tasks", "ideas"):
            try:
                self.client.table(table_name).select("id").limit(1).execute()
                table_status[table_name] = "ok"
            except Exception as exc:
                table_status[table_name] = f"error: {exc}"

        ready = not missing_env and all(status == "ok" for status in table_status.values())
        return {
            "ready": ready,
            "missing_env": missing_env,
            "tables": table_status,
            "model": CANONICAL_MODEL,
        }

    def health_report(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "service": "Dynamic Daily Task Engine",
            "timestamp": utc_now_iso(),
            "model": CANONICAL_MODEL,
        }

    def _table_rows(self, table_name: str) -> List[Dict[str, Any]]:
        result = self.client.table(table_name).select("*").execute()
        return list(result.data or [])

    def _insert_goal(self, title: str, timeframe: str, source: str) -> Dict[str, Any]:
        record = {
            "title": title,
            "timeframe": timeframe,
            "status": "Planned",
            "source": source,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        result = self.client.table("goals").insert(record).execute()
        rows = result.data or []
        if not rows:
            raise ExternalServiceError("Supabase did not return a goal record")
        return rows[0]

    def _insert_task(
        self,
        *,
        goal_id: Any,
        task_payload: Dict[str, Any],
        source: str,
        parent_task_id: Any = None,
        task_kind: str = "task",
        default_order: int = 1,
    ) -> Dict[str, Any]:
        priority = normalize_priority(task_payload.get("priority"))
        estimated_minutes = _clean_int(task_payload.get("estimated_minutes") or task_payload.get("duration_minutes"), fallback=30)
        remaining_minutes = _clean_int(task_payload.get("remaining_minutes"), fallback=estimated_minutes)
        record = {
            "goal_id": goal_id,
            "parent_task_id": parent_task_id,
            "task_kind": task_kind,
            "content": _clean_text(task_payload.get("content") or task_payload.get("title"), fallback="Untitled Task"),
            "level": _clean_int(task_payload.get("level"), fallback=2 if parent_task_id else 1),
            "estimated_minutes": estimated_minutes,
            "remaining_minutes": remaining_minutes,
            "execution_order": _clean_int(task_payload.get("execution_order"), fallback=default_order),
            "priority": priority["label"],
            "priority_rank": priority["rank"],
            "status": _clean_text(task_payload.get("status"), fallback="Pending"),
            "scheduled_start_at": task_payload.get("scheduled_start_at"),
            "scheduled_end_at": task_payload.get("scheduled_end_at"),
            "calendar_event_id": task_payload.get("calendar_event_id"),
            "previous_calendar_event_id": task_payload.get("previous_calendar_event_id"),
            "rollover_count": _clean_int(task_payload.get("rollover_count"), fallback=0),
            "source": source,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        result = self.client.table("tasks").insert(record).execute()
        rows = result.data or []
        if not rows:
            raise ExternalServiceError("Supabase did not return a task record")
        return rows[0]

    def _task_children(self, task_id: Any) -> List[Dict[str, Any]]:
        rows = self._table_rows("tasks")
        children = [row for row in rows if row.get("parent_task_id") == task_id]
        return sorted(children, key=lambda row: (row.get("execution_order", 999), row.get("id", 0)))

    def create_goal_plan(self, payload: Dict[str, Any], *, source: str = "api") -> Dict[str, Any]:
        data = _as_dict(payload, name="plan payload")
        goal_payload = _as_dict(data.get("goal") or {}, name="goal")
        title = _clean_text(goal_payload.get("title"), fallback="Brain Dump Goal")
        timeframe = _clean_text(goal_payload.get("timeframe"), fallback=DEFAULT_TIMEFRAME)
        tasks_payload = data.get("tasks") or []
        if not isinstance(tasks_payload, list):
            raise ValidationError("tasks must be a list")

        goal_row = self._insert_goal(title, timeframe, source)
        inserted_tasks: List[Dict[str, Any]] = []

        for index, task_payload in enumerate(tasks_payload, start=1):
            if not isinstance(task_payload, dict):
                raise ValidationError("Each task must be a JSON object")
            parent_task = self._insert_task(
                goal_id=goal_row["id"],
                task_payload=task_payload,
                source=source,
                parent_task_id=None,
                task_kind="task",
                default_order=index,
            )
            inserted_tasks.append(parent_task)

            for child_index, child_payload in enumerate(task_payload.get("sub_tasks") or [], start=1):
                if not isinstance(child_payload, dict):
                    raise ValidationError("Each sub-task must be a JSON object")
                inserted_tasks.append(
                    self._insert_task(
                        goal_id=goal_row["id"],
                        task_payload=child_payload,
                        source=source,
                        parent_task_id=parent_task["id"],
                        task_kind="subtask",
                        default_order=child_index,
                    )
                )

        return {
            "goal": goal_row,
            "tasks": inserted_tasks,
            "counts": {
                "tasks": len([task for task in inserted_tasks if task.get("task_kind") == "task"]),
                "sub_tasks": len([task for task in inserted_tasks if task.get("task_kind") == "subtask"]),
            },
        }

    def generate_plan_from_text(self, text: str, groq_client, model: str = "llama-3.3-70b-versatile") -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValidationError("text is required")
        if groq_client is None:
            raise ConfigurationError("GROQ_API_KEY is required for plan generation")

        system_prompt = """
You are the Dynamic Daily Task Engine.
Convert the user's raw intake into JSON only.
Output this structure:
{
  "goal": { "title": "String", "timeframe": "Daily" },
  "tasks": [
    {
      "content": "String",
      "level": 1,
      "estimated_minutes": 60,
      "execution_order": 1,
      "priority": "High",
      "sub_tasks": [
        {
          "content": "String",
          "level": 2,
          "estimated_minutes": 30,
          "execution_order": 1,
          "priority": "High"
        }
      ]
    }
  ]
}
""".strip()

        completion = groq_client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        )
        raw_content = completion.choices[0].message.content
        if not raw_content:
            raise ExternalServiceError("Groq returned an empty plan")
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ExternalServiceError(f"Groq returned invalid JSON: {exc}") from exc

    def log_idea(self, idea_text: str, *, source: str = "manual") -> Dict[str, Any]:
        content = _clean_text(idea_text, fallback="")
        if not content:
            raise ValidationError("idea text is required")

        record = {
            "content": content,
            "status": "Unread",
            "source": source,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        result = self.client.table("ideas").insert(record).execute()
        rows = result.data or []
        if not rows:
            raise ExternalServiceError("Supabase did not return an idea record")
        return rows[0]

    def list_unread_ideas(self) -> List[Dict[str, Any]]:
        rows = self._table_rows("ideas")
        return sorted(
            [row for row in rows if row.get("status") == "Unread"],
            key=lambda row: row.get("created_at") or "",
            reverse=True,
        )

    def list_pending_parent_tasks(self) -> List[Dict[str, Any]]:
        return _ordered_tasks(self._table_rows("tasks"), status="Pending")

    def list_scheduled_parent_tasks(self) -> List[Dict[str, Any]]:
        return _ordered_tasks(self._table_rows("tasks"), status="Scheduled")

    def get_task(self, task_id: Any) -> Optional[Dict[str, Any]]:
        for row in self._table_rows("tasks"):
            if str(row.get("id")) == str(task_id):
                return row
        return None

    def update_task(self, task_id: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValidationError(f"Task {task_id} was not found")

        updates = {"updated_at": utc_now_iso()}
        if "content" in payload or "title" in payload:
            updates["content"] = _clean_text(payload.get("content") or payload.get("title"), fallback=task.get("content", "Untitled Task"))
        if "status" in payload:
            updates["status"] = _clean_text(payload.get("status"), fallback=task.get("status", "Pending"))
        if "remaining_minutes" in payload:
            updates["remaining_minutes"] = _clean_int(payload.get("remaining_minutes"), fallback=int(task.get("remaining_minutes") or task.get("estimated_minutes") or 0))
        if "priority" in payload:
            priority = normalize_priority(payload.get("priority"))
            updates["priority"] = priority["label"]
            updates["priority_rank"] = priority["rank"]
        if "scheduled_start_at" in payload:
            updates["scheduled_start_at"] = payload.get("scheduled_start_at")
        if "scheduled_end_at" in payload:
            updates["scheduled_end_at"] = payload.get("scheduled_end_at")
        if "calendar_event_id" in payload:
            updates["calendar_event_id"] = payload.get("calendar_event_id")

        result = self.client.table("tasks").update(updates).eq("id", task["id"]).execute()
        rows = result.data or []
        if not rows:
            raise ExternalServiceError("Supabase did not return an updated task record")
        return rows[0]

    def complete_task(self, task_id: Any) -> Dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValidationError(f"Task {task_id} was not found")
        return self.update_task(task_id, {"status": "Completed", "remaining_minutes": 0})

    def rollover_task(self, task_id: Any, remaining_minutes: int) -> Dict[str, Any]:
        task = self.get_task(task_id)
        if task is None:
            raise ValidationError(f"Task {task_id} was not found")

        updates = {
            "status": "Pending",
            "remaining_minutes": _clean_int(remaining_minutes, fallback=int(task.get("remaining_minutes") or task.get("estimated_minutes") or 0)),
            "scheduled_start_at": None,
            "scheduled_end_at": None,
            "previous_calendar_event_id": task.get("calendar_event_id"),
            "calendar_event_id": None,
            "rollover_count": _clean_int(task.get("rollover_count"), fallback=0) + 1,
            "updated_at": utc_now_iso(),
        }
        result = self.client.table("tasks").update(updates).eq("id", task["id"]).execute()
        rows = result.data or []
        if not rows:
            raise ExternalServiceError("Supabase did not return a rolled over task record")
        return rows[0]

    def render_task_description(self, task: Dict[str, Any]) -> str:
        children = self._task_children(task["id"])
        checklist = "\n".join(f"- [ ] {child.get('content', 'Untitled Sub-Task')}" for child in children)
        parts = [
            f"Goal: {task.get('goal_id')}",
            f"Task: {task.get('content')}",
            f"Estimated minutes: {task.get('remaining_minutes') or task.get('estimated_minutes') or 30}",
        ]
        if checklist:
            parts.append("Sub-tasks:\n" + checklist)
        return "\n\n".join(parts)

    def build_calendar_event(self, task: Dict[str, Any], start_at: datetime, end_at: datetime, timezone_name: str) -> Dict[str, Any]:
        priority = normalize_priority(task.get("priority_rank") or task.get("priority"))
        summary = f"[Deep Work] {task.get('content')}" if priority["rank"] == 1 else task.get("content", "Untitled Task")
        return {
            "summary": summary,
            "description": self.render_task_description(task),
            "start": {"dateTime": start_at.isoformat(), "timeZone": timezone_name},
            "end": {"dateTime": end_at.isoformat(), "timeZone": timezone_name},
            "colorId": "11" if priority["rank"] == 1 else "9",
        }

    def schedule_pending_tasks(
        self,
        calendar_service,
        *,
        start_hour: int = 7,
        buffer_minutes: int = 15,
        timezone_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if calendar_service is None:
            raise ConfigurationError("Google Calendar credentials are missing")

        zone, display_zone = parse_time_zone(timezone_name)
        tomorrow = datetime.now(zone) + timedelta(days=1)
        current_slot = tomorrow.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        scheduled = []
        failed = []

        for task in self.list_pending_parent_tasks():
            duration = _clean_int(task.get("remaining_minutes") or task.get("estimated_minutes"), fallback=30)
            start_at = current_slot
            end_at = start_at + timedelta(minutes=duration)
            event = self.build_calendar_event(task, start_at, end_at, display_zone)

            try:
                created_event = calendar_service.events().insert(calendarId="primary", body=event).execute()
                updated_task = self.update_task(
                    task["id"],
                    {
                        "status": "Scheduled",
                        "scheduled_start_at": start_at.isoformat(),
                        "scheduled_end_at": end_at.isoformat(),
                        "calendar_event_id": created_event.get("id"),
                    },
                )
                scheduled.append(
                    {
                        "task": updated_task,
                        "calendar_event_id": created_event.get("id"),
                        "start_at": start_at.isoformat(),
                        "end_at": end_at.isoformat(),
                    }
                )
                current_slot = end_at + timedelta(minutes=buffer_minutes)
            except Exception as exc:
                failed.append({"task_id": task.get("id"), "error": str(exc)})

        return {
            "timezone": display_zone,
            "start_hour": start_hour,
            "scheduled": scheduled,
            "failed": failed,
        }

    def review_snapshot(self) -> Dict[str, Any]:
        scheduled = self.list_scheduled_parent_tasks()
        pending = self.list_pending_parent_tasks()
        completed = [task for task in self._table_rows("tasks") if task.get("status") == "Completed" and not task.get("parent_task_id")]
        return {
            "scheduled": scheduled,
            "pending": pending,
            "completed": completed,
            "counts": {
                "scheduled": len(scheduled),
                "pending": len(pending),
                "completed": len(completed),
            },
        }

    def apply_review_updates(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(updates, list):
            raise ValidationError("updates must be a list")

        results = []
        for item in updates:
            if not isinstance(item, dict) or "task_id" not in item:
                raise ValidationError("Each update must include a task_id")
            task_id = item["task_id"]
            if item.get("completed") is True or _clean_text(item.get("status"), fallback="").lower() == "completed":
                results.append(self.complete_task(task_id))
            elif item.get("remaining_minutes") is not None or _clean_text(item.get("status"), fallback="").lower() in {"pending", "rollover"}:
                results.append(self.rollover_task(task_id, item.get("remaining_minutes") or item.get("estimated_minutes") or 30))
            else:
                results.append(self.update_task(task_id, item))

        return {"updated": results, "count": len(results)}


def build_service() -> TaskService:
    return TaskService()
