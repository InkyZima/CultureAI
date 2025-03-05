#!/usr/bin/env python3
"""
Test script to validate the entire chat session process.

This script simulates how the ChatProcessor initializes and uses the chat session.
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

# Configure the Gemini API - This sets the API key in the module
genai.configure(key=api_key)

# Print the API key first few chars for debugging
print(f"API Key found: {api_key[:4]}...")

def get_system_prompt():
    """Simple system prompt for testing"""
    return "You are a helpful assistant in a chat application."

def get_system_prompt_preflight():
    """Simple preflight prompt for testing"""
    return "I understand. I will be a helpful assistant."

def test_chat_session():
    """Test the complete chat session process"""
    model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
    print(f"Using model: {model_name}")
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Get system prompts
    system_prompt = get_system_prompt()
    system_prompt_preflight = get_system_prompt_preflight()
    
    print(f"\nSystem prompt: {system_prompt}")
    print(f"System prompt preflight: {system_prompt_preflight}")
    
    # Initialize chat with system prompt - EXACTLY LIKE IN CHATPROCESSOR
    chat_session = model.start_chat(
        history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": [system_prompt_preflight]}
        ]
    )
    
    # Now prepare and send a user message like in _send_message_to_gemini
    timestamp = datetime.datetime.now().isoformat()
    formatted_time = datetime.datetime.fromisoformat(timestamp).strftime('%H:%M')
    injection_string = "Respond helpfully."
    user_message = "Hello, how are you?"
    
    formatted_message = f"[{formatted_time}] [System instruction: {injection_string}] \n\n {user_message}"
    print(f"\nFormatted message: {formatted_message}")
    
    # Send the formatted message
    try:
        print("\nSending message to chat session with system prompt...")
        response = chat_session.send_message(formatted_message)
        print("Success! Response received.")
        print(f"Response text: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing complete chat session process...\n")
    
    try:
        result = test_chat_session()
        if result:
            print("\nTest completed successfully! The chat session process works.")
        else:
            print("\nTest failed. The chat session process is causing errors.")
            sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
