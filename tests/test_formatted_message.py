#!/usr/bin/env python3
"""
Test script to validate the formatting of messages in the chat interface.

This script specifically tests the message format used in the ChatProcessor
to ensure it's compatible with the Gemini API.
"""

import os
import sys
import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our custom wrapper
from chat.gemini_wrapper import GeminiModule as genai

# Load environment variables from .env file
load_dotenv()

# Check if API key is available
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    sys.exit(1)

# Configure the Gemini API
genai.configure(key=api_key)

# Print the API key first few chars for debugging
print(f"API Key found: {api_key[:4]}...")

def test_formatted_message():
    """Test the same formatted message pattern used in ChatProcessor"""
    model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
    print(f"Using model: {model_name}")
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Start a new chat session
    chat = model.start_chat()
    
    # Format the message exactly like ChatProcessor does
    timestamp = datetime.datetime.now().isoformat()
    formatted_time = datetime.datetime.fromisoformat(timestamp).strftime('%H:%M')
    injection_string = "Respond helpfully."
    
    # THIS IS THE EXACT FORMAT USED IN CHAT PROCESSOR
    formatted_message = f"[{formatted_time}] [System instruction: {injection_string}] \n\n Test message"
    print(f"\nFormatted message: {formatted_message}")
    
    # Send the formatted message
    try:
        print("\nSending formatted message...")
        response = chat.send_message(formatted_message)
        print("Success! Response received.")
        print(f"Response text: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing formatted message pattern...\n")
    
    try:
        result = test_formatted_message()
        if result:
            print("\nTest completed successfully! The formatted message pattern works.")
        else:
            print("\nTest failed. The formatted message pattern is causing errors.")
            sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
