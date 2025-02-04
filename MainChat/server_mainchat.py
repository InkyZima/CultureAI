"""
The MainChat python service is going to run locally on port 8001 and receive POST requests for sending a user message, along with a chat history and system prompt, to an LLM. The LLM is going to return an answer to MainChat and MainChat is going to respond with this to the POST request as well as save everything to an sqlite database.
The LLM used shall be Google gemini-pro. The module used to talk to the LLM shall be google.generativeai.
We do prototyping here; keep it as simple as possible.

"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
from database.init_db import init_db, get_db
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

def fetch_chat_history(user_id: str, limit: int = 50, limit_to_today: bool = True):
    """Get recent chat history for user in chronological order"""
    conn = get_db()
    
    if limit_to_today:
        today = datetime.now().date().isoformat()
        cursor = conn.execute('''
            SELECT timestamp, party, content 
            FROM chat_logs 
            WHERE user_id = ? 
            AND date(timestamp) = ?
            ORDER BY timestamp ASC 
            LIMIT ?''', (user_id, today, limit))
    else:
        cursor = conn.execute('''
            SELECT timestamp, party, content 
            FROM chat_logs 
            WHERE user_id = ? 
            ORDER BY timestamp ASC 
            LIMIT ?''', (user_id, limit))
    
    history = cursor.fetchall()
    conn.close()
    return history

def format_messages_for_llm(system_prompt: str, history, user_message: str) -> str:
    """Format the conversation in a clear way for the LLM"""
    formatted = ""
    
    if system_prompt:
        formatted += f"System: {system_prompt}\n\n"
    
    for msg in history:
        timestamp, party, content = msg
        formatted += f"[{datetime.fromisoformat(timestamp).strftime('%H:%M')}] {party}: {content}\n\n"
    
    formatted += f"User: {user_message}\n\n"
    formatted += "Assistant:"
    
    return formatted

@app.post("/chat")
async def chat(message: dict):
    user_id = message['user_id']
    user_message = message['content']
    if user_message.startswith("User at "):
        # Extract just the message content after the timestamp
        user_message = user_message.split(": ", 1)[1]
    else:
        # Add timestamp if not present
        current_time = datetime.now().strftime("%H:%M")
        user_message = f"User at {current_time}: {user_message}"
    system_prompt = message.get('system_prompt', '')
    # Read system prompt from file
    try:
        with open('system_prompt.txt', 'r') as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        system_prompt = message.get('system_prompt', '')
    
    # If no system prompt, default to "You are an AI chat assistant."
    if not system_prompt:
        system_prompt = """You are an AI chat assistant."""
    limit_to_today = message.get('limit_to_today', True)
    limit = message.get('limit', 50)
    save_to_history = message.get('save_to_history', True)
    
    # Save user message first
    conn = get_db()
    conn.execute('INSERT INTO chat_logs VALUES (?, ?, ?, ?, ?)',
                (datetime.now().isoformat(), user_id, 'user', user_message, system_prompt))
    conn.close()
    
    # Get and format chat history
    history = fetch_chat_history(user_id)
    formatted_prompt = format_messages_for_llm(system_prompt, history, user_message)
   
    # Get response from Gemini
    response = model.generate_content(formatted_prompt)
    print(response.text)

    # Save AI response
    conn = get_db()
    conn.execute('INSERT INTO chat_logs VALUES (?, ?, ?, ?, ?)',
                (datetime.now().isoformat(), user_id, 'ai', response.text, system_prompt))
    conn.close()
    
    return {"content": response.text}

@app.post("/chat_history")
async def get_chat_history(message: dict):
    user_id = message['user_id']
    limit = message.get('limit', 50)
    limit_to_today = message.get('limit_to_today', True)
    
    conn = get_db()
    try:
        if limit_to_today:
            today = datetime.now().date().isoformat()
            cursor = conn.execute('''
                SELECT timestamp, party, content 
                FROM chat_logs 
                WHERE user_id = ? 
                AND date(timestamp) = ?
                ORDER BY timestamp ASC 
                LIMIT ?''', (user_id, today, limit))
        else:
            cursor = conn.execute('''
                SELECT timestamp, party, content 
                FROM chat_logs 
                WHERE user_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?''', (user_id, limit))
        
        history = cursor.fetchall()
        return {"messages": [{"timestamp": msg[0], "party": msg[1], "content": msg[2]} for msg in history]}
    
    finally:
        conn.close()

@app.post("/clear_history")
async def clear_history(message: dict):
    user_id = message['user_id']
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM chat_logs WHERE user_id = ?', (user_id,))
        return {"status": "success"}
    finally:
        conn.close()


if __name__ == "__main__":
    #clear the chat history if args include --clear-history 
    import sys
    if '--clear-db' in sys.argv:
        conn = get_db()
        conn.execute('DELETE FROM chat_logs')
        conn.close()
        #log to console
        print("Chat history cleared\n")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)



"""
Usage:
curl -X POST http://localhost:8001/chat \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user123",
    "content": "What is my name?"
}'
"""