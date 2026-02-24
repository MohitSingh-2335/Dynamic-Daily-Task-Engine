import sqlite3
import json

# 1. Connect to the local SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('daily_engine.db')
cursor = conn.cursor()

def create_schema():
    """Creates the main table to hold all tasks, phases, and habits."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_category TEXT NOT NULL,
        title TEXT NOT NULL,
        subtasks TEXT, -- Stored as a JSON string
        duration_mins INTEGER NOT NULL,
        energy_level TEXT, -- Peak, High, Moderate, Low
        status TEXT DEFAULT 'Pending', -- Pending, Scheduled, Completed
        priority INTEGER DEFAULT 2 -- 1 (High), 2 (Medium), 3 (Low)
    )
    ''')
    conn.commit()
    print("✅ Database schema created successfully.")

def insert_seed_data():
    """Injects initial tasks into the database to test the system."""
    
    sample_tasks = [
        (
            "7-Phase AI", 
            "Phase 1 & 2: Data Exploration and Cleaning", 
            json.dumps(["Import Pandas and NumPy", "Check for null values", "Normalize numerical columns"]), 
            120, 
            "Peak", 
            "Pending", 
            1
        ),
        (
            "DePIN-Guard", 
            "Review AI Model Architecture", 
            json.dumps(["Check PyTorch training script", "Review team pull requests", "Test local endpoints"]), 
            90, 
            "High", 
            "Pending", 
            1
        ),
        (
            "Health & Diet", 
            "Lunch & Disconnect", 
            json.dumps(["Eat Palak, Broccoli, Karela, Chukandar, Lehsun", "Drink 2 glasses of water"]), 
            60, 
            "Low", 
            "Pending", 
            2
        ),
        (
            "Personal Development", 
            "Reading Block", 
            json.dumps(["Read 15 mins of dependency-reduction book", "Take quick notes"]), 
            30, 
            "Wind-down", 
            "Pending", 
            3
        ),
        (
            "Gaming", 
            "Evening Gaming Block", 
            json.dumps(["Genshin Impact: Daily Commissions", "Infinite Galaxy: 10 min check-in"]), 
            70, 
            "Relaxed", 
            "Pending", 
            3
        )
    ]

    # Insert tasks only if the table is empty to prevent duplicates on rerun
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO tasks (project_category, title, subtasks, duration_mins, energy_level, status, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_tasks)
        conn.commit()
        print("✅ Seed data injected successfully.")
    else:
        print("⚠️ Data already exists. Skipping seed injection.")

def fetch_pending_tasks():
    """Retrieves tasks that need to be scheduled."""
    cursor.execute("SELECT task_id, title, duration_mins, priority FROM tasks WHERE status = 'Pending' ORDER BY priority ASC")
    pending = cursor.fetchall()
    
    print("\n--- 📋 Current Pending Tasks ---")
    for task in pending:
        print(f"ID: {task[0]} | Priority: {task[3]} | Title: {task[1]} | Duration: {task[2]} mins")
    return pending

# Run the setup
if __name__ == "__main__":
    create_schema()
    insert_seed_data()
    fetch_pending_tasks()
    
    # Close the connection when done
    conn.close()