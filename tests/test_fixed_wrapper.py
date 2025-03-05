#!/usr/bin/env python3
"""
Test script to validate the fixes to our Gemini API wrapper.

This script specifically tests the formatting of API requests
to ensure they're compatible with the v1beta API.
"""

import os
import sys
import json
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
genai.configure(api_key=api_key)

def test_message_format():
    """Test that the message format is correct for the API"""
    model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
    print(f"Using model: {model_name}")
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Start a new chat session
    chat = model.start_chat()
    
    # Examine the history structure
    print("\nInitial history structure:")
    print(json.dumps(chat.history, indent=2))
    
    # Send a test message
    print("\nSending test message...")
    try:
        response = chat.send_message("Hello, can you give me a brief introduction to yourself?")
        print("Response received successfully!")
        print(f"Response timestamp: {response.timestamp}")
        print(f"Response text: {response.text[:100]}...")
        
        # Examine the updated history structure
        print("\nUpdated history structure:")
        print(json.dumps(chat.history, indent=2))
        
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nContent payload that was sent:")
        # This assumes the error happened after printing the request payload
        # Check any debugging output in the logs
        return False

if __name__ == "__main__":
    print("Testing fixed Gemini API wrapper...\n")
    
    try:
        result = test_message_format()
        if result:
            print("\nTest completed successfully! The fixed wrapper is working correctly.")
        else:
            print("\nTest failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)
