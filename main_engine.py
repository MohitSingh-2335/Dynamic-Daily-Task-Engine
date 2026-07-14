from __future__ import annotations

import os

from api.service import ConfigurationError, build_service
from google_auth import get_calendar_service


def schedule_tasks():
    print("Starting Dynamic Daily Task Engine")
    calendar_service = get_calendar_service()
    if calendar_service is None:
        raise ConfigurationError("Google Calendar credentials are missing")

    result = build_service().schedule_pending_tasks(
        calendar_service,
        start_hour=int(os.environ.get("SCHEDULE_START_HOUR", "7")),
        buffer_minutes=int(os.environ.get("SCHEDULE_BUFFER_MINUTES", "15")),
        timezone_name=os.environ.get("DEFAULT_TIME_ZONE"),
    )
    print(result)


if __name__ == "__main__":
    schedule_tasks()