import os
from supabase import create_client, Client

# We will store these securely in Vercel's environment variables later.
# For local testing, we fetch them from your computer's environment.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize the secure connection
def get_db_connection() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("⚠️ Supabase URL and Key are missing!")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Let's test it!
if __name__ == "__main__":
    try:
        db = get_db_connection()
        print("✅ Successfully connected to the Allrounder-AI Brain!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")