Dynamic Daily Task Engine ⚙️📅
An intelligent, Python-powered scheduling system that acts as a local, automated personal assistant. It manages complex daily workflows by dynamically slotting tasks into specific time blocks based on energy levels, prioritizing heavy technical workloads, and automatically rolling over incomplete tasks to prevent burnout.

🚀 Motivation
Balancing B.Tech coursework, an intensive Artificial Intelligence and Machine Learning roadmap, collaborative open-source projects, and personal health requires more than a static to-do list. Traditional calendars forget what you didn't finish. This project was built to solve the "analysis paralysis" of complex schedules by handling task state, sub-task tracking, and dynamic re-allocation automatically.

✨ Key Features
Automated Task Roll-Over: Incomplete tasks or leftover minutes are automatically queried from the database and rescheduled for the next available day. No sub-task is ever lost.

Energy-Aligned Scheduling: Matches high-cognitive tasks (like Phase 1 & 2 data exploration and cleaning) to peak morning energy blocks, while slotting gaming and reading into low-energy evening blocks.

Google Calendar API Integration: Pushes the generated schedule directly to Google Calendar, injecting granular sub-task checklists directly into the event descriptions for easy mobile viewing.

Burnout Buffers: Automatically enforces transition gaps and buffer hours between context-heavy tasks.

Stateful Memory: Uses a lightweight local database (SQLite/JSON) to act as the "brain," tracking the exact progress of multi-hour project phases.

🛠️ Tech Stack
Core Logic: Python 3.x

Database: SQLite / JSON

Integration: Google Calendar API, Google Auth

Automation: Windows Task Scheduler / Cron (for nightly 10:30 PM execution)

🧠 How It Works
The Database (Memory): Tasks are logged with metadata including project category, estimated duration, required energy level, and an array of sub-tasks.

The Engine (Logic): A nightly script queries all Pending tasks, calculates available time blocks for the upcoming 7:00 AM - 11:00 PM day, and optimally slots them in.

The Output (Interface): The script executes an API handshake with Google Calendar, creating structured events so you wake up to a perfectly organized day without manual planning.

🔮 Future Scope
LLM Integration: Transitioning the rigid rule-based slotting logic into an Observable Local AI Engine using LangChain and local models to generate the optimized schedule payload.

GitHub API Hook: Automatically parsing newly assigned issues from group repositories and converting them into actionable calendar blocks.
