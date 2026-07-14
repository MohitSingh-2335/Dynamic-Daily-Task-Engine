from __future__ import annotations

import sys
from datetime import datetime

from api.service import build_service


def setup_idea_table():
    return build_service().readiness_report()


def log_idea(idea_text):
    idea = build_service().log_idea(idea_text, source="idea_inbox")
    print(f"Idea logged: {idea.get('content')}")


def view_ideas():
    ideas = build_service().list_unread_ideas()
    if not ideas:
        print("Your idea inbox is empty.")
        return

    print("Your Unread Ideas")
    for idea in ideas:
        created_at = idea.get("created_at")
        formatted_time = created_at
        if created_at:
            try:
                formatted_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%b %d, %I:%M %p")
            except ValueError:
                formatted_time = created_at
        print(f"[{idea.get('id')}] {formatted_time} - {idea.get('content')}")


if __name__ == "__main__":
    setup_idea_table()
    if len(sys.argv) > 1:
        log_idea(" ".join(sys.argv[1:]))
    else:
        view_ideas()