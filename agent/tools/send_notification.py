#!/usr/bin/env python
"""
Tool for sending notifications to the user via ntfy.sh
"""
import json
import requests
import os
import datetime
import sys
from dotenv import load_dotenv

# Add the parent directory to the system path so we can import required modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from database import MessageDatabase

# Load environment variables
load_dotenv()

def send_notification(message):
    """
    Send a notification to the user via ntfy.sh
    
    Args:
        message (str): The notification message to send
        
    Returns:
        str: JSON string with success/error information
    """
    try:
        if not message or not isinstance(message, str):
            return json.dumps({
                "success": False,
                "error": "Notification message must be a non-empty string"
            })
        
        # Get the ntfy topic from environment variable
        ntfy_topic = os.getenv("NTFY_TOPIC")
        if not ntfy_topic:
            return json.dumps({
                "success": False,
                "error": "NTFY_TOPIC environment variable is not set"
            })
        
        # Create the notification URL
        ntfy_url = f"https://ntfy.sh/{ntfy_topic}"
        
        # Send the POST request to ntfy.sh
        response = requests.post(
            ntfy_url,
            data=message.encode(encoding='utf-8'),
            headers={
                "Title": "LoopAgentClaude Notification",
                "Priority": "default",
                "Tags": "bell"
            }
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Log the notification to the database
            db = MessageDatabase()
            system_message = {
                'message': f"Notification sent: {message}",
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'System'
            }
            db.save_message(system_message)
            
            return json.dumps({
                "success": True,
                "message": "Notification sent successfully",
                "notification": message,
                "timestamp": datetime.datetime.now().isoformat()
            })
        else:
            return json.dumps({
                "success": False,
                "error": f"Failed to send notification: {response.status_code} {response.text}"
            })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

# Define the tool specification for Google Generative AI
TOOL_SPEC = {
    "name": "send_notification",
    "description": "Send a notification to the user. Use it to proactively communicate when the user has been away for too long. Notifications must be short and mobile-friendly.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {
                "type": "STRING",
                "description": "The notification message to send. Examples: 'Good morning! Ready to stretch and then have a productive day?', 'Hey, how was your lunch break?'"
            }
        },
        "required": ["message"]
    }
}
