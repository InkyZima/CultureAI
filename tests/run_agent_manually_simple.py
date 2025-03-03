#!/usr/bin/env python
"""
This script manually runs the agent implemented in agent/llm_agent.py. It calls process_message with the prompt "Send the user a notification with the content 'Hi from Chat-AI'!". This script is as simple as possible. It does nothing else than what was just described.
"""

import os
import traceback
import json
from dotenv import load_dotenv
from agent.thinking_agent import ThinkingAgent

# Load environment variables from .env file if it exists
load_dotenv()

try:
    # Initialize the agent
    print("Initializing LLM Agent...")
    agent = ThinkingAgent()
    
    # Run the agent with the specified prompt
    print("Processing message...")
    prompt = "Send the user a notification with the content 'Hi from Chat-AI'!"
    response = agent.process_message()
    
    # Print the response
    print("Agent response:")
    print(json.dumps(response, indent=2))
    
except Exception as e:
    print(f"Exception: {e}")
    print(traceback.format_exc())
