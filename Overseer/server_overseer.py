"""
Overseer is going to suggest how to move the current chat conversation between User and LLM forward, given the current time, user_objectives.txt (objectives, which the user is supposed to achieve today), and relevant information about what the user has done today already.
Overseer will be called via POST endpoint and given all this information. Overseer than queries a LLM (with the system prompt: "It is {current_time}. The user is having a conversation with a guide, who's task is to ensure that the user achieves their objectives for today. Based on those {objectives} and {current_user_achievements}, what should the guide ask the user or ask the user to do, in order to ensure they achieve their objectives for today? Your answer must be in the form: Ask the user at the next opportunity _. Example: Ask the user at the next opportunity if they meditated this morning." ). Overseer then responds to the POST request with: "[System instruction: {llm_response}], for example: [System instruction: Ask the user at the next opportunity if they meditated this morning.]". Overseer also saves this response to a local sqlite database "overseer_suggestions.db" including a timestamp.
The overseer should run every 4 prompts (to not spam system instructions to the Main Chat LLM).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
from database.init_db import init_db, get_db
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


# the achievements are stored in the database ../Extractor/extracted_info.db. Only the newest entry is relevant.
def get_current_user_achievements(user_id):
    """Get current user achievements from database"""
    conn = sqlite3.connect('../TaskUpdater/database/tasks.db')
    cursor = conn.execute('SELECT task_status FROM task_updates WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return "No tasks have been recorded yet. The user is just getting started."
    
    return result[0]




@app.post("/oversee")
async def oversee(message: dict):

    user_id = message['user_id']
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # current_user_achievements = "The user has meditated twice today; in the morning and during their lunch break." #dummy data
    current_user_achievements = get_current_user_achievements(user_id)
    
    # Create prompt
    prompt = f"""It is {current_time}. The user is having a conversation with a guide, who's task is to ensure that the user achieves their objectives for today. 
    Based on those objectives and their current completion state, what information should the guide ask of the user, or what should the guide ask the user to do, in order to ensure they achieve their objectives for today? 
    Here are the objectives and their current completion state:
    {current_user_achievements}

    Your answer must be in the form: Ask the user at the next opportunity _. Example: Ask the user at the next opportunity if they meditated this morning."""


    # Get suggestion from Gemini
    response = model.generate_content(prompt)
    
    # Save to database
    conn = get_db()
    conn.execute('INSERT INTO overseer_suggestions VALUES (?, ?, ?)',
                (datetime.now().isoformat(), user_id, response.text))
    conn.close()
    return {"content": "\n\n[System instruction: " + response.text.strip() + "]"}


@app.post("/get_system_instruction")
async def get_system_instruction(message: dict):
    user_id = message['user_id']
    
    conn = get_db()
    try:
        cursor = conn.execute('''
            SELECT overseer_suggestion 
            FROM overseer_suggestions 
            WHERE user_id = ?
            ORDER BY timestamp DESC 
            LIMIT 1''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return {"content": "\n\n[System instruction: " + row[0].strip() + "]"}
        return {"content": ""}
        
    finally:
        conn.close()



if __name__ == "__main__":
    #clear the chat history if args include --clear-history 
    import sys
    if '--clear-db' in sys.argv:
        conn = get_db()
        conn.execute('DELETE FROM extracted_info')
        conn.close()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)


"""
Usage:
curl -X POST http://localhost:8003/oversee \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user123"
}'
"""