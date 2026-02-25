import sqlite3
import sys
from datetime import datetime

def setup_idea_table():
    """Creates the ideas table if it doesn't exist yet."""
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ideas (
            idea_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Unread'
        )
    ''')
    conn.commit()
    conn.close()

def log_idea(idea_text):
    """Saves a new idea to the database."""
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ideas (content) VALUES (?)", (idea_text,))
    conn.commit()
    conn.close()
    print(f"💡 Idea logged securely: '{idea_text}'")

def view_ideas():
    """Displays all unread ideas."""
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    cursor.execute("SELECT idea_id, content, timestamp FROM ideas WHERE status = 'Unread'")
    ideas = cursor.fetchall()
    conn.close()
    
    if not ideas:
        print("📭 Your idea inbox is empty.")
        return
        
    print("\n--- 🧠 Your Unread Ideas ---")
    for idea in ideas:
        # Format the timestamp to be cleaner
        time_obj = datetime.strptime(idea[2], '%Y-%m-%d %H:%M:%S')
        formatted_time = time_obj.strftime('%b %d, %I:%M %p')
        print(f"[{idea[0]}] {formatted_time} - {idea[1]}")

if __name__ == "__main__":
    setup_idea_table()
    
    # If you type an idea after the script name, it saves it.
    if len(sys.argv) > 1:
        idea = " ".join(sys.argv[1:])
        log_idea(idea)
    # If you just run the script, it shows your inbox.
    else:
        view_ideas()