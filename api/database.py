from __future__ import annotations

import os

from supabase import Client, create_client


def get_db_connection() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
    return create_client(supabase_url, supabase_key)


if __name__ == "__main__":
    try:
        get_db_connection()
        print("Supabase connection initialized")
    except Exception as exc:
        print(f"Connection failed: {exc}")