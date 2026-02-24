import sqlite3
import json
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Google Calendar Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_calendar_service():
    """Loads the token and returns the Calendar API service."""
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('calendar', 'v3', credentials=creds)
    else:
        print("❌ Error: token.json not found. Run google_auth.py first.")
        return None

def fetch_pending_tasks(cursor):
    """Fetches tasks prioritized by priority level."""
    cursor.execute('''
        SELECT task_id, title, subtasks, duration_mins, priority 
        FROM tasks 
        WHERE status = 'Pending' 
        ORDER BY priority ASC
    ''')
    return cursor.fetchall()

def format_description(subtasks_json):
    """Converts the JSON array of subtasks into a clean checklist."""
    try:
        subtasks = json.loads(subtasks_json)
        formatted = "<b>Goals for this block:</b><br>"
        for task in subtasks:
            formatted += f"• [ ] {task}<br>"
        return formatted
    except:
        return "No specific subtasks listed."

def schedule_tasks():
    print("🚀 Starting Dynamic Daily Task Engine...")
    
    # Connect to DB and Google Calendar
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    service = get_calendar_service()
    
    if not service:
        return

    tasks = fetch_pending_tasks(cursor)
    
    if not tasks:
        print("✅ No pending tasks to schedule. You are all caught up!")
        return

    # Start scheduling for TOMORROW at 7:00 AM (your chosen wake-up time)
    now = datetime.now()
    schedule_start = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    current_time_slot = schedule_start

    print(f"\n📅 Scheduling {len(tasks)} tasks starting from {schedule_start.strftime('%Y-%m-%d %I:%M %p')}\n")

    for task in tasks:
        task_id, title, subtasks_json, duration_mins, priority = task
        
        # Calculate start and end times
        start_time_str = current_time_slot.isoformat()
        end_time_slot = current_time_slot + timedelta(minutes=duration_mins)
        end_time_str = end_time_slot.isoformat()
        
        # Format the description with subtasks
        description = format_description(subtasks_json)

        # Build the Calendar Event payload
        event = {
            'summary': f"[Deep Work] {title}" if priority == 1 else title,
            'description': description,
            'start': {
                'dateTime': start_time_str,
                'timeZone': 'Asia/Kolkata', # Standard IST timezone
            },
            'end': {
                'dateTime': end_time_str,
                'timeZone': 'Asia/Kolkata',
            },
            'colorId': '11' if priority == 1 else '9', # Red for High Priority, Blue for others
        }

        try:
            # Push to Google Calendar
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            print(f"✅ Scheduled: {title} ({duration_mins} mins) at {current_time_slot.strftime('%I:%M %p')}")
            
            # Update database status to 'Scheduled'
            cursor.execute("UPDATE tasks SET status = 'Scheduled' WHERE task_id = ?", (task_id,))
            conn.commit()
            
            # Add a 15-minute Anti-Burnout Buffer after each task
            current_time_slot = end_time_slot + timedelta(minutes=15)
            
        except Exception as e:
            print(f"❌ Failed to schedule {title}. Error: {e}")

    conn.close()
    print("\n🎉 All pending tasks successfully pushed to Google Calendar!")

if __name__ == '__main__':
    schedule_tasks()