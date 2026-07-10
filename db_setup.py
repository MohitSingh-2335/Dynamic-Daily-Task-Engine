from __future__ import annotations

from api.service import build_service


def create_schema():
    service = build_service()
    readiness = service.readiness_report()
    print(readiness)


def insert_seed_data():
    print("Seed data is managed in Supabase; apply the schema in README before running intake.")


def fetch_pending_tasks():
    tasks = build_service().list_pending_parent_tasks()
    for task in tasks:
        print(f"ID: {task.get('id')} | Priority: {task.get('priority')} | Title: {task.get('content')} | Duration: {task.get('remaining_minutes') or task.get('estimated_minutes')} mins")
    return tasks


if __name__ == "__main__":
    create_schema()
    insert_seed_data()
    fetch_pending_tasks()