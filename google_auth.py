from __future__ import annotations

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


import json

def authenticate_google():
    creds = None
    
    # 1. Try to load token from Environment Variable
    token_json_str = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_json_str:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    else:
        # Fallback: Load from file
        token_path = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # 2. Refresh or authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Full OAuth flow needed
            credentials_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if credentials_json_str:
                credentials_data = json.loads(credentials_json_str)
                flow = InstalledAppFlow.from_client_config(credentials_data, SCOPES)
            else:
                credentials_path = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token only if we're doing local development
        if not token_json_str:
            token_path = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")
            try:
                with open(token_path, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            except OSError:
                pass # Ignore write errors on read-only filesystems (e.g. Vercel)

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