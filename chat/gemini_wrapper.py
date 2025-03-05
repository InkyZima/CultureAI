"""Gemini API wrapper for Python 3.7 compatibility.

This module provides a simple wrapper around the Google Gemini API
using direct HTTP requests instead of the official SDK, which requires
Python 3.9+.
"""

import os
import sys
import time
import json
import datetime
import requests
from typing import Dict, List, Any, Optional
from types import SimpleNamespace

# Capture local timezone for consistent timestamp formatting
try:
    import tzlocal
    import pytz
except ImportError:
    print("Warning: tzlocal or pytz not installed. Using UTC for timestamps.")
    LOCAL_TIMEZONE = None
else:
    LOCAL_TIMEZONE = tzlocal.get_localzone()

# Base URL for the v1beta API
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Global configuration
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
model_url = model_name

# Standard generation configuration
generation_config = {
    "temperature": 0.7,
    "topK": 40,
    "topP": 0.95,
    "maxOutputTokens": 2048,
    "stopSequences": []
}

def send_request_with_retries(url, data, max_retries=3):
    """Helper function to send request with retry logic"""
    headers = {"Content-Type": "application/json"}
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # Handle rate limiting (429) or server errors (5xx)
            if response.status_code == 429 or (response.status_code >= 500 and response.status_code < 600):
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)  # Exponential backoff with max of 60 seconds
                print(f"Rate limited or server error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                print(error_msg)
                print(f"Request data: {json.dumps(data, indent=2)}")
                raise Exception(error_msg)
                
            return response.json()
                
        except requests.exceptions.Timeout:
            retry_count += 1
            wait_time = min(2 ** retry_count, 60)
            print(f"Request timed out. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            retry_count += 1
            time.sleep(min(2 ** retry_count, 60))
    
    raise Exception(f"Failed after {max_retries} retries")

class GeminiSession:
    """A chat session with the Gemini API"""
    
    def __init__(self, history=None):
        """Initialize a chat session with optional history"""
        self.messages = history or []
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = f"{BASE_URL}/{self.model_name}"
        self.generation_config = generation_config
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    
    def send_message(self, message_text):
        """Send a message to the chat session and return the response"""
        # Convert message to proper format for v1beta API
        message = {
            'role': 'user',
            'parts': [{'text': message_text}]
        }
        self.messages.append(message)
        
        url = f"{self.base_url}:generateContent?key={self.api_key}"
        # Prepare the request data with formatted messages
        request_data = {
            'contents': self.messages,
            'generationConfig': self.generation_config
        }

        # Uncomment for debugging
        print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        # Send the request with retries
        response_data = send_request_with_retries(url, request_data)
        
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            # Extract and format the assistant's response
            candidate = response_data['candidates'][0]
            if 'content' in candidate:
                content = candidate['content']
                if 'parts' in content and len(content['parts']) > 0:
                    text = content['parts'][0].get('text', '')
                    
                    # Create a response object to mimic the official SDK
                    response = SimpleNamespace()
                    response.text = text
                    
                    # Save the assistant's response to history
                    assistant_message = {
                        'role': 'model',
                        'parts': [{'text': text}]
                    }
                    self.messages.append(assistant_message)
                    
                    return response
        
        # Handle error cases
        raise Exception(f"Failed to get valid response from API: {json.dumps(response_data, indent=2)}")

class GeminiResponse:
    """A wrapper for Gemini API responses"""
    
    def __init__(self, text):
        self.text = text
        # Add timestamp with proper timezone information
        self.timestamp = datetime.datetime.now(LOCAL_TIMEZONE).isoformat()

class GenerativeModel:
    """A wrapper for Gemini API generative models"""
    
    def __init__(self, model_name):
        """Initialize a model with the given name"""
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = f"{BASE_URL}/{self.model_name}"
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    
    def start_chat(self, history=None):
        """Start a new chat session with optional history"""
        # Ensure history has the correct format for v1beta API
        if history is not None:
            # Convert any string parts to proper format with text key
            formatted_history = []
            for msg in history:
                if 'parts' in msg:
                    parts = []
                    for part in msg['parts']:
                        if isinstance(part, str):
                            parts.append({'text': part})
                        else:
                            parts.append(part)
                    formatted_history.append({
                        'role': msg['role'],
                        'parts': parts
                    })
                else:
                    formatted_history.append(msg)
            return GeminiSession(formatted_history)
        return GeminiSession()
    
    def generate_content(self, prompt, max_retries=3):
        """Generate content from a prompt (non-chat mode)"""
        url = f"{self.base_url}:generateContent?key={self.api_key}"
        
        # If prompt is a string, convert to proper format
        if isinstance(prompt, str):
            data = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": generation_config
            }
        else:
            # Assume prompt is already formatted correctly
            data = {
                "contents": prompt,
                "generationConfig": generation_config
            }
        
        # Send the request with retries
        response_data = send_request_with_retries(url, data, max_retries)
        
        # Extract the response text
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            candidate = response_data['candidates'][0]
            if 'content' in candidate:
                content = candidate['content']
                if 'parts' in content and len(content['parts']) > 0:
                    text = content['parts'][0].get('text', '')
                    
                    # Create a response object
                    response = SimpleNamespace()
                    response.text = text
                    return response
        
        raise Exception(f"Failed to get valid response from API: {json.dumps(response_data, indent=2)}")

# Module-level functions to maintain API compatibility
def configure(key=None):
    """Configure the Gemini API with the given API key"""
    global api_key
    if key:
        api_key = key

# Create a module-level namespace for backward compatibility
class GeminiModule:
    """A namespace for Gemini API functions"""
    GenerativeModel = GenerativeModel
    configure = configure
