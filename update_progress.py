from __future__ import annotations

from api.service import build_service


def update_tasks():
    service = build_service()
    scheduled_tasks = service.list_scheduled_parent_tasks()

    if not scheduled_tasks:
        print("No scheduled tasks found.")
        return

    print("Evening Review")
    print("Update what you accomplished today.\n")

    updates = []
    for task in scheduled_tasks:
        title = task.get("content", "Untitled Task")
        duration = task.get("scheduled_start_at")
        print(f"{title} ({duration or task.get('estimated_minutes', 0)} mins)")

        while True:
            response = input("Did you finish this completely? (y/n): ").strip().lower()
            if response == "y":
                updates.append({"task_id": task["id"], "completed": True})
                print("Marked as completed.\n")
                break
            if response == "n":
                leftover = input("How many minutes of work are still left? ")
                updates.append({"task_id": task["id"], "remaining_minutes": leftover})
                print(f"Rolled over {leftover} mins.\n")
                break
            print("Please enter 'y' or 'n'.")

    result = service.apply_review_updates(updates)
    print(result)
    print("Evening review complete.")


if __name__ == "__main__":
    update_tasks()