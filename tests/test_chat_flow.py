#!/usr/bin/env python3
"""
Test script to validate the entire chat flow.
"""

import os
import sys
import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the chat processor
from chat.chat import ChatProcessor

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    sys.exit(1)

# Print the API key first few chars for debugging
print(f"API Key found: {api_key[:4]}...")

# A mock socketio class for testing
class MockSocketIO:
    def __init__(self):
        self.emitted_messages = []
    
    def emit(self, event, data):
        print(f"SocketIO would emit: {event}")
        self.emitted_messages.append({"event": event, "data": data})
        return self.emitted_messages[-1]["data"]

def test_chat_flow():
    """Test the entire chat flow process"""
    # Create a mock socketio
    socketio = MockSocketIO()
    
    # Initialize the chat processor
    chat_processor = ChatProcessor(socketio)
    print("\nChat processor initialized")
    
    # Create a test message
    timestamp = datetime.datetime.now().isoformat()
    message_data = {
        "message": "Hello, how are you today?",
        "timestamp": timestamp,
        "session_id": "test_session",
        "role": "user"
    }
    
    # Process the message
    print("\nSending test message to chat processor...")
    response = chat_processor.process_message(message_data)
    
    # Check the response
    if response and "message" in response:
        print(f"\nSuccess! Response received.")
        print(f"Response text: {response['message'][:100]}...")
        return True
    else:
        print("\nTest failed. No valid response received.")
        return False

if __name__ == "__main__":
    print("Testing complete chat flow...\n")
    
    try:
        result = test_chat_flow()
        if result:
            print("\nTest completed successfully! The chat flow works.")
        else:
            print("\nTest failed. The chat flow is causing errors.")
            sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
