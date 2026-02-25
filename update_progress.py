import sqlite3

def update_tasks():
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Fetch tasks that were scheduled for today
    cursor.execute("SELECT task_id, title, duration_mins FROM tasks WHERE status = 'Scheduled'")
    scheduled_tasks = cursor.fetchall()

    if not scheduled_tasks:
        print("🎉 No scheduled tasks found. Your slate is clean!")
        return

    print("\n--- 🌙 Evening Review: Task Roll-Over ---")
    print("Let's update what you accomplished today.\n")

    for task in scheduled_tasks:
        task_id, title, duration = task
        print(f"🔹 {title} (Allocated: {duration} mins)")
        
        while True:
            response = input("Did you finish this completely? (y/n): ").strip().lower()
            if response == 'y':
                cursor.execute("UPDATE tasks SET status = 'Completed' WHERE task_id = ?", (task_id,))
                print("   ✅ Marked as Completed.\n")
                break
            elif response == 'n':
                leftover = input("   How many minutes of work are still left? ")
                try:
                    leftover_mins = int(leftover)
                    # Reset status to Pending and update the duration for tomorrow's scheduling
                    cursor.execute("UPDATE tasks SET status = 'Pending', duration_mins = ? WHERE task_id = ?", (leftover_mins, task_id))
                    print(f"   🔄 Rolled over {leftover_mins} mins to tomorrow.\n")
                    break
                except ValueError:
                    print("   ❌ Please enter a valid number.")
            else:
                print("   ❌ Please enter 'y' or 'n'.")

    conn.commit()
    conn.close()
    print("✅ Evening review complete! Your database is ready for tomorrow's schedule generation.")

if __name__ == '__main__':
    update_tasks()