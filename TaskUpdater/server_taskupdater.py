"""
TaskUpdater receives user messages via its POST endpoint and analyzes them to update the list of completed and incomplete tasks.
The tasks are defined in user_objectives.txt. TaskUpdater uses an LLM to determine which tasks have been completed based on the user's messages.
The updated task status is stored in a local sqlite database "tasks.db".
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
from database.init_db import init_db, get_db
import json
import sqlite3
from pathlib import Path

# Load GOOGLE_API_KEY from .env in parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for prototyping
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize database
init_db()

def get_objectives():
    """Read objectives from text file"""
    with open('user_objectives.txt', 'r') as f:
        return f.read().strip()

# Update tasks based on user message
@app.post("/update_tasks")
async def update_tasks(message: dict):
    user_id = message['user_id']
    # Get the conversation from mainchat.db
    conn = sqlite3.connect('../MainChat/database/mainchat.db')
    cursor = conn.execute('''
        SELECT content, party
        FROM chat_logs 
        WHERE user_id = ? 
        ORDER BY timestamp ASC''', (user_id,))
    messages = cursor.fetchall()
    conn.close()
    # Format messages into content string
    content = ""
    for msg_content, party in messages:
        if party == 'user':
            content += f"User: {msg_content}\n"
        else:
            content += f"AI: {msg_content}\n"
    
    objectives = get_objectives()
    # Get latest task state from DB, fallback to objectives if none exists
    conn = get_db()
    cursor = conn.execute('''
        SELECT task_status 
        FROM task_updates 
        ORDER BY timestamp DESC 
        LIMIT 1''')
    row = cursor.fetchone()
    current_task_completion_state = row[0] if row else objectives
    conn.close()
    
    # Create prompt
    prompt = f"""Based on this chat history, check which tasks the user has completed.
Currently completed and incompleted tasks:
{current_task_completion_state}

Structure the response as a valid JSON object with the following format:
{{"tasks": [{{"task": "task description", "completed": 0}}]}}

Return only those tasks which are relevant based on the current time of day: It is currently {datetime.now().strftime("%H:%M")}.

Do not include any explanations or additional text, only return the JSON object. Do not format your output to be human readable. No newline characters.

User message: {content}"""
    
    # Get task status from LLM
    response = model.generate_content(prompt)

    # Validate JSON response
    try:
        json.loads(response.text)
    except json.JSONDecodeError:
        # Try one more time if invalid JSON
        response = model.generate_content(prompt)
        try:
            json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from LLM"}
    
    # Save to database
    conn = get_db()
    conn.execute('INSERT INTO task_updates VALUES (?, ?, ?, ?)',
                (datetime.now().isoformat(), user_id, content, response.text))
    conn.close()
    
    return {"content": response.text}

# Get task status. First, try to fetch the latest tasks status (of the day, if limit_to_today is True) from the database. If there is none, return the objetives instead 
@app.post("/get_task_status")
async def get_task_status(message: dict):
    user_id = message['user_id']
    limit_to_today = message.get('limit_to_today', True)

    conn = get_db()
    try:
        if limit_to_today:
            today = datetime.now().date().isoformat()
            cursor = conn.execute('''
                SELECT task_status 
                FROM task_updates 
                WHERE user_id = ? 
                AND date(timestamp) = ?
                ORDER BY timestamp DESC 
                LIMIT 1''', (user_id, today))
        else:
            cursor = conn.execute('''
                SELECT task_status 
                FROM task_updates 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1''', (user_id,))
        
        last_status = cursor.fetchone()
        if last_status:
            return {"content": last_status[0]}
        
        # If no status found, return initial objectives formatted as JSON
        with open('user_objectives.txt') as f:
            objectives = json.loads(f.read())
            tasks = [{"task": obj, "completed": 0} for obj in objectives["objectives"]]
            return {"content": json.dumps({"tasks": tasks})}
    
    finally:
        conn.close()

@app.post("/clear_tasks")
async def clear_tasks(message: dict):
    user_id = message['user_id']
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM task_updates WHERE user_id = ?', (user_id,))
        # After clearing tasks, insert initial objectives as first status
        with open('user_objectives.txt') as f:
            objectives = json.loads(f.read())
            tasks = [{"task": obj, "completed": 0} for obj in objectives["objectives"]]
            conn.execute('INSERT INTO task_updates VALUES (?, ?, ?, ?)',
                        (datetime.now().isoformat(), user_id, "", json.dumps({"tasks": tasks})))
        return {"status": "success"}
    finally:
        conn.close()

if __name__ == "__main__":
    #clear the chat history if args include --clear-history 
    import sys
    
    if '--clear-db' in sys.argv:
        conn = get_db()
        conn.execute('DELETE FROM task_updates')
        conn.close()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)


"""
Usage:
curl -X POST http://localhost:8002/update_tasks \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user123",
    "content": "I have meditated twice today; in the morning and during my lunch break."
}'
"""