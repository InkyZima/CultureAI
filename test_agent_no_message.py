#!/usr/bin/env python
"""
This script tests the agent's ability to run without providing a message parameter.
In this case, it should automatically read the system_prompts/agent_prompt.txt file.
"""

import os
import traceback
import json
from dotenv import load_dotenv
from agent.llm_agent import LLMAgent

# Load environment variables from .env file if it exists
load_dotenv()

try:
    # Initialize the agent
    print("Initializing LLM Agent...")
    agent = LLMAgent()
    
    # Run the agent without providing a message
    print("Processing message with no message parameter (should read from agent_prompt.txt)...")
    response = agent.process_message()
    
    # Print the response
    print("Agent response:")
    print(json.dumps(response, indent=2))
    
except Exception as e:
    print(f"Exception: {e}")
    print(traceback.format_exc())
