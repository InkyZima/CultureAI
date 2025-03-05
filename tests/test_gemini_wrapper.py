#!/usr/bin/env python3
"""
Test script for the custom Gemini API wrapper.

This script tests the basic functionality of the custom Gemini API wrapper
used as a replacement for the official google-generativeai SDK on Python 3.7.
"""

import os
import sys
import time
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

def test_simple_request():
    """Test a simple request to the Gemini API"""
    model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
    print(f"Using model: {model_name}")
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Start a new chat session
    chat = model.start_chat()
    
    # Send a test message
    print("\nSending test message...")
    start_time = time.time()
    response = chat.send_message("Hello, can you give me a brief introduction to yourself?")
    elapsed_time = time.time() - start_time
    
    # Print the response
    print(f"\nResponse received in {elapsed_time:.2f} seconds:")
    print("-" * 50)
    print(response.text)
    print(f"Timestamp: {response.timestamp}")
    print("-" * 50)
    
    # Send a follow-up message to test history handling
    print("\nSending follow-up message...")
    start_time = time.time()
    response = chat.send_message("How can you assist with Python development?")
    elapsed_time = time.time() - start_time
    
    # Print the response
    print(f"\nResponse received in {elapsed_time:.2f} seconds:")
    print("-" * 50)
    print(response.text)
    print(f"Timestamp: {response.timestamp}")
    print("-" * 50)
    
    return True

def test_generate_content():
    """Test the generate_content method used by the thinking agent"""
    model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
    print(f"Using model: {model_name} for generate_content test")
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Send a test prompt
    print("\nSending test prompt for generate_content...")
    start_time = time.time()
    
    test_prompt = """
    Question: What is the capital of France?
    Please provide a short answer.
    """
    
    response = model.generate_content(test_prompt)
    elapsed_time = time.time() - start_time
    
    # Print the response
    print(f"\nResponse received in {elapsed_time:.2f} seconds:")
    print("-" * 50)
    print(response.text)
    print(f"Timestamp: {response.timestamp}")
    print("-" * 50)
    
    return True

if __name__ == "__main__":
    print("Testing custom Gemini API wrapper for Python 3.7...\n")
    
    try:
        result = test_simple_request()
        if result:
            print("\nTest completed successfully! The custom wrapper is working as expected.")
        result = test_generate_content()
        if result:
            print("\nTest completed successfully! The generate_content method is working as expected.")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        sys.exit(1)
