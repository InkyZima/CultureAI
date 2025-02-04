# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import firebase_admin
from firebase_admin import credentials, messaging
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pathlib import Path
from plyer import notification
import sqlite3
import asyncio
from collections import defaultdict
import queue
import threading
import json  # Add this import at the top
import google.generativeai as genai
from datetime import datetime
import pytz
import httpx
from typing import Dict
from pathlib import Path

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for prototyping
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get the directory where this script is located
current_dir = Path(__file__).parent

# Initialize Firebase Admin SDK with correct path
cred = credentials.Certificate(str(current_dir / "universalpush-73f31-firebase-adminsdk-fbsvc-e209f7537b.json"))
firebase_admin.initialize_app(cred)

# Pydantic models for request validation
class NotificationRequest(BaseModel):
    title: str
    body: str
    token: str | None = None
    user_id: str | None = "user123"

class NotificationSettingRequest(BaseModel):
    user_id: str
    enabled: bool

# Database functions
def init_db():
    db_path = Path(__file__).parent / "notifications.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notification_settings (
            user_id TEXT PRIMARY KEY,
            android_enabled INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    db_path = Path(__file__).parent / "notifications.db"
    return sqlite3.connect(str(db_path))

# Initialize database on startup
init_db()

# Store notification queues for each user
notification_queues = defaultdict(queue.Queue)



# Load GOOGLE_API_KEY from .env in parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Store background tasks for each user
notification_tasks: Dict[str, asyncio.Task] = {}

async def run_notification_checker(user_id: str, interval_minutes: int):
    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)  # Wait first
            await notification_decider({"user_id": user_id})  # Then check
        except Exception as e:
            print(f"Error in notification checker: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before retrying if there's an error

@app.post("/set_android_notifications")
async def set_android_notifications(request: dict):
    user_id = request.get('user_id')
    enabled = request.get('enabled')
    interval = request.get('interval', 30)  # Default to 30 minutes
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        conn = get_db()
        conn.execute('''
            INSERT INTO notification_settings (user_id, android_enabled)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            android_enabled = ?
        ''', (user_id, enabled, enabled))
        conn.commit()
        conn.close()

        # Handle background task
        if enabled:
            if user_id in notification_tasks:
                notification_tasks[user_id].cancel()
            notification_tasks[user_id] = asyncio.create_task(
                run_notification_checker(user_id, interval)
            )
        elif user_id in notification_tasks:
            notification_tasks[user_id].cancel()
            del notification_tasks[user_id]

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_pc_notifications")
async def set_pc_notifications(request: dict):
    """
    Endpoint to enable/disable PC notifications for a user and set the check interval.
    
    Args:
        request (dict): Contains:
            - user_id (str): ID of the user to update settings for
            - enabled (bool): Whether to enable/disable PC notifications
            - interval (int): Minutes between notification checks (default 30)
    
    Returns:
        dict: {"success": True} if successful
        
    Raises:
        HTTPException: If user_id is missing or on database errors
    """
    user_id = request.get('user_id')
    enabled = request.get('enabled')
    interval = request.get('interval', 30)  # Default to 30 minutes
    print(("Enabling" if enabled else "Disabling") + " PC notifications with interval: " + str(interval) + " minutes.")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        # Update notification settings in database
        conn = get_db()
        conn.execute('''
            INSERT INTO notification_settings (user_id, pc_enabled)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            pc_enabled = ?
        ''', (user_id, enabled, enabled))
        conn.commit()
        conn.close()

        # Handle background notification checking task
        if enabled:
            # Cancel existing task if any
            if user_id in notification_tasks:
                notification_tasks[user_id].cancel()
            # Create new notification checker task with specified interval
            notification_tasks[user_id] = asyncio.create_task(
                run_notification_checker(user_id, interval)
            )
        # If notifications disabled, clean up task if no other notification types enabled
        elif user_id in notification_tasks and not any([
            get_notification_setting(user_id, 'android_enabled'),
            get_notification_setting(user_id, 'pc_enabled')
        ]):
            notification_tasks[user_id].cancel()
            del notification_tasks[user_id]

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_notification_setting(user_id: str, setting: str) -> bool:
    conn = get_db()
    result = conn.execute(f'SELECT {setting} FROM notification_settings WHERE user_id = ?', 
                         (user_id,)).fetchone()
    conn.close()
    return bool(result and result[0])

@app.post("/register_watcher")
async def register_watcher(request: dict):
    user_id = request.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    return {"success": True}

@app.get("/notifications/{user_id}")
async def notifications_stream(user_id: str):
    async def event_generator():
        while True:
            if not notification_queues[user_id].empty():
                notification = notification_queues[user_id].get()
                yield {
                    "event": "message",
                    "data": json.dumps(notification)  # Convert dict to JSON string
                }
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())

@app.post("/universalpush/send")
async def send_notification(request: NotificationRequest):
    # Send Android notification if enabled
    conn = get_db()
    result = conn.execute('SELECT android_enabled FROM notification_settings WHERE user_id = ?', 
                         (request.user_id,)).fetchone()
    conn.close()
    
    if not result or not result[0]:
        return {"success": False, "message": "Android notifications disabled for this user"}
    
    message = messaging.Message(
        notification=messaging.Notification(
            title=request.title,
            body=request.body
        ),
        token=request.token if request.token else open(str(current_dir / "devicetoken.txt")).read().strip()
    )
    
    try:
        response = messaging.send(message)
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notification_decider")
async def notification_decider(request: dict):
    print("triggered /notification_decider")
    user_id = request.get('user_id', 'user123')
    
    try:
        # Get current time in a readable format
        tz = pytz.timezone('Europe/Berlin')  # Adjust timezone as needed
        current_time = datetime.now(tz).strftime("%H:%M on %A")
        
        # Get conversation history from chat backend
        chat_response = await fetch('http://localhost:8001/chat_history', {
            'method': 'POST',
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({
                'user_id': user_id,
                'limit': 10,
                'limit_to_today': True
            })
        })
        chat_data = chat_response.json()  # Removed await since json() is not async
        conversation_history = "\n".join([
            f"{msg['party']}: {msg['content']}" 
            for msg in chat_data.get('messages', [])
        ])
        
        # Get user objectives from task backend
        task_response = await fetch('http://localhost:8002/get_task_status', {
            'method': 'POST',
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({
                'user_id': user_id,
                'limit_to_today': True
            })
        })
        task_data = task_response.json()  # Removed await here too
        user_objectives = task_data.get('content', '[]')
        
        # AI objectives (could be stored in a config or database)
        ai_objectives = open(str(current_dir / "ai_objectives.txt")).read().strip()

        prompt = f"""You are the User's AI-assistant. 
Context:
Current time: {current_time}

Conversation history:
{conversation_history}

User's objectives:
{user_objectives}

AI-assistant's objectives:
{ai_objectives}

Considering the current time of day, the conversation history, the time of the last conversation, the User's objectives and the AI-assistant's objectives,
would now be a good time to proactively approach the user to ask a question or remind them of one of their objectives? What should the AI-assistant say to the user?
Reply in the following format: "Yes: Ask the user if they had pizza for lunch." """

        print("Querying the LLM, with conversation history: " + conversation_history)
        response = model.generate_content(prompt)
        decision = response.text.strip()
        
        print(f"Notification decision: {decision}")  # Log the decision
        
        if decision.startswith("Yes:"):
            message = decision[4:].strip()
            
            notification_request = NotificationRequest(
                title="AI Assistant",
                body=message,
                user_id=user_id
            )
            
            # Queue notification for frontend ONCE
            notification_queues[user_id].put({
                "title": "AI Assistant",
                "body": message
            })
            
            # Send Android notification if enabled
            await send_notification(notification_request)
            
            return {"decision": "yes", "message": message}
        else:
            return {"decision": "no", "message": decision}
            
    except Exception as e:
        print(f"Error in notification_decider: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for HTTP requests
async def fetch(url, options):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            options['method'],
            url,
            headers=options.get('headers', {}),
            json=json.loads(options.get('body', '{}'))
        )
        response.raise_for_status()
        return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004)

"""

curl -X POST -H "Content-Type: application/json" -d '{
  "title": "Test Notification",
  "body": "This is a test notification",
  "token": "YOUR_DEVICE_TOKEN"
}' http://127.0.0.1:8004/universalpush/send

curl -X POST -H "Content-Type: application/json" -d '{
  "title": "Test Notification",
  "body": "This is a test notification"
}' http://127.0.0.1:8004/universalpush/send_pc

If token is ommited, it will be sent to the token in devicetoken.txt
"""