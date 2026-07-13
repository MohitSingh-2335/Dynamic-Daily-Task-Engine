from __future__ import annotations

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def authenticate_google():
    creds = None
    token_path = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def get_calendar_service():
    try:
        return authenticate_google()
    except Exception as exc:
        print(f"Google Calendar authentication failed: {exc}")
        return None


if __name__ == "__main__":
    service = authenticate_google()
    print("Google Calendar authenticated" if service else "Google Calendar authentication failed")