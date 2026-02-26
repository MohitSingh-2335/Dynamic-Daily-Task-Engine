import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from .database import get_db_connection

# Initialize the Flask App
app = Flask(__name__)
# Allow your future Vercel frontend to talk to this backend
CORS(app) 

# Initialize Groq Client
# We will set this in your terminal just like the Supabase keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route('/api/health', methods=['GET'])
def health_check():
    """A simple endpoint to verify the server is awake."""
    return jsonify({"status": "online", "message": "Allrounder AI Engine is ready."}), 200

import json

@app.route('/api/process-brain-dump', methods=['POST'])
def process_brain_dump():
    """Takes user text, sends it to Groq, and returns structured JSON."""
    data = request.json
    user_text = data.get("text")

    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    if not groq_client:
        return jsonify({"error": "Groq API key missing on server"}), 500

    # The System Prompt: This is what makes your app smarter than TickTick
    system_prompt = """
    You are the 'Allrounder AI', an elite productivity engine. 
    The user will give you a raw brain dump of tasks. 
    Your job is to structure this into a deeply nested hierarchy (Goal -> Task -> Sub-task).
    
    RULES:
    1. Enforce the 'Focus Forcer' concept: assign an 'execution_order' (1, 2, 3) to sequential tasks.
    2. Estimate time in minutes ('estimated_minutes').
    3. Assign priority ('High', 'Medium', 'Low').
    4. Timeframe must be one of: 'Daily', 'Weekly', 'Monthly', 'Yearly'.
    
    You MUST output ONLY valid JSON in this exact structure:
    {
      "goal": { "title": "String", "timeframe": "Daily" },
      "tasks": [
        {
          "content": "String",
          "level": 1,
          "estimated_minutes": 60,
          "execution_order": 1,
          "priority": "High",
          "sub_tasks": [
             {
               "content": "String",
               "level": 2,
               "estimated_minutes": 30,
               "execution_order": 1,
               "priority": "High"
             }
          ]
        }
      ]
    }
    """

    try:
        # 1. Call the ultra-fast Groq LPU
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        # Extract the JSON response
        ai_response = chat_completion.choices[0].message.content
        structured_data = json.loads(ai_response)
        
        # 2. Connect to the Database
        db = get_db_connection()
        
        # 3. Insert the Goal
        goal_data = structured_data.get("goal", {})
        goal_res = db.table("goals").insert({
            "title": goal_data.get("title", "Brain Dump Goal"),
            "timeframe": goal_data.get("timeframe", "Daily"),
            "status": "Pending"
        }).execute()
        
        goal_id = goal_res.data[0]['id']

        # 4. Insert the Tasks & Sub-Tasks (The Focus Forcer)
        tasks_data = structured_data.get("tasks", [])
        for task in tasks_data:
            # Insert Parent Task
            task_res = db.table("tasks").insert({
                "goal_id": goal_id,
                "content": task.get("content", "Untitled Task"),
                "level": task.get("level", 1),
                "estimated_minutes": task.get("estimated_minutes", 30),
                "execution_order": task.get("execution_order", 1),
                "priority": task.get("priority", "Medium"),
                "status": "Pending"
            }).execute()
            
            parent_task_id = task_res.data[0]['id']

            # Insert Sub-Tasks
            sub_tasks = task.get("sub_tasks", [])
            for sub in sub_tasks:
                db.table("tasks").insert({
                    "goal_id": goal_id,
                    "parent_task_id": parent_task_id, # Links to the step above!
                    "content": sub.get("content", "Untitled Sub-Task"),
                    "level": sub.get("level", 2),
                    "estimated_minutes": sub.get("estimated_minutes", 30),
                    "execution_order": sub.get("execution_order", 2),
                    "priority": sub.get("priority", "Medium"),
                    "status": "Pending"
                }).execute()

        return jsonify({
            "status": "success", 
            "message": "Schedule locked into Supabase Brain!",
            "goal_id": goal_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the local server for testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)