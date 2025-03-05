"""Gemini API wrapper for Python 3.7 compatibility.

This module provides a simple wrapper around the Google Gemini API
using direct HTTP requests instead of the official SDK, which requires
Python 3.9+.
"""

import os
import json
import time
import datetime
import requests
from typing import Dict, List, Any, Optional

# Capture local timezone for consistent timestamp formatting
try:
    LOCAL_TIMEZONE = datetime.datetime.now().astimezone().tzinfo
except Exception:
    # Fallback for Python 3.7 where astimezone() without argument might not be well supported
    import tzlocal
    LOCAL_TIMEZONE = tzlocal.get_localzone()

class GeminiSession:
    """A wrapper for Gemini chat sessions compatible with Python 3.7"""
    
    def __init__(self, history=None):
        """Initialize a new chat session with optional history"""
        self.history = history or []
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("CHAT_MODEL") or "gemini-2.0-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}"
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    
    def send_message(self, message: str, max_retries=3) -> 'GeminiResponse':
        """Send a message and get a response from the Gemini API"""
        # Add the user message to history with timestamp
        current_time = datetime.datetime.now(LOCAL_TIMEZONE).isoformat()
        self.history.append({
            "role": "user", 
            "parts": [{"text": message}],
            "timestamp": current_time
        })
        
        # Prepare the request
        url = f"{self.base_url}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Create the request body
        data = {
            "contents": self.history,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "stopSequences": []
            }
        }
        
        # Retry logic for rate limiting or temporary failures
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Make the request
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
                    
                response_json = response.json()
                
                # Extract the response text
                try:
                    response_text = response_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # Add the response to history with timestamp
                    current_time = datetime.datetime.now(LOCAL_TIMEZONE).isoformat()
                    self.history.append({
                        "role": "model", 
                        "parts": [{"text": response_text}],
                        "timestamp": current_time
                    })
                    
                    # Return a response object
                    return GeminiResponse(response_text)
                except (KeyError, IndexError) as e:
                    error_msg = f"Failed to extract response text: {e}. Response: {response_json}"
                    print(error_msg)
                    raise Exception(error_msg)
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                print(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                print(f"Request error: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # If we've exhausted all retries
        raise Exception(f"Failed to get response after {max_retries} retries")

class GeminiResponse:
    """A wrapper for Gemini API responses"""
    
    def __init__(self, text):
        self.text = text
        # Add timestamp with proper timezone information
        self.timestamp = datetime.datetime.now(LOCAL_TIMEZONE).isoformat()

class GenerativeModel:
    """A wrapper for the Gemini GenerativeModel class"""
    
    def __init__(self, model_name):
        """Initialize a model with the given name"""
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}"
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")
    
    def start_chat(self, history=None):
        """Start a new chat session with optional history"""
        return GeminiSession(history)
    
    def generate_content(self, prompt, max_retries=3):
        """Generate content from a prompt (non-chat mode)"""
        # Prepare the request
        url = f"{self.base_url}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Create the request body - single prompt instead of chat history
        data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "stopSequences": []
            }
        }
        
        # Retry logic for rate limiting or temporary failures
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Make the request
                response = requests.post(url, headers=headers, json=data, timeout=60)  # Longer timeout for thinking
                
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
                    print(f"Request headers: {headers}")
                    print(f"Request URL: {url}")
                    raise Exception(error_msg)
                    
                response_json = response.json()
                
                # Extract the response text
                try:
                    response_text = response_json['candidates'][0]['content']['parts'][0]['text']
                    current_time = datetime.datetime.now(LOCAL_TIMEZONE).isoformat()
                    response = GeminiResponse(response_text)
                    response.timestamp = current_time
                    return response
                except (KeyError, IndexError) as e:
                    error_msg = f"Failed to extract response text: {e}. Response: {response_json}"
                    print(error_msg)
                    raise Exception(error_msg)
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                print(f"Request timed out. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                print(f"Request error: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # If we've exhausted all retries
        raise Exception(f"Failed to get response after {max_retries} retries")

# Module-level functions to maintain API compatibility
def configure(api_key=None):
    """Set the API key (for compatibility with the official SDK)"""
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

# Create a module-level namespace for backward compatibility
class GeminiModule:
    GenerativeModel = GenerativeModel
    configure = configure
