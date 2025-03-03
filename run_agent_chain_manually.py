#!/usr/bin/env python
"""
This script manually runs the agent chain implemented in agent/agent_chain.py.
It executes the full agent chain that:
1. Uses the thinking agent to decide if a tool should be used
2. Parses the decision and extracts tool name and arguments
3. Executes the tool if needed

This script is a simple demonstration of the agent chain in action.
"""

import os
import traceback
import json
from dotenv import load_dotenv
from agent.agent_chain import AgentChain

# Load environment variables from .env file if it exists
load_dotenv()

try:
    # Initialize the agent chain
    print("Initializing Agent Chain...")
    agent_chain = AgentChain()
    
    # Run the agent chain
    print("Executing agent chain...")
    response = agent_chain.execute()
    
    # Print the response
    print("\nAgent Chain Execution Results:")
    print(json.dumps(response, indent=2))
    
    # Print a summary based on the action taken
    if response.get("action_taken", False):
        tool_used = response.get("tool_used", "unknown")
        print(f"\nAction Summary: Tool '{tool_used}' was executed")
        
        # If it was a notification, show the message content
        if tool_used == "send_notification":
            message = response.get("tool_args", {}).get("message", "")
            print(f"Notification sent: '{message}'")
        
        # If it was an instruction injection, show the instruction
        elif tool_used == "inject_instruction":
            instruction = response.get("tool_args", {}).get("instruction", "")
            print(f"Instruction injected: '{instruction}'")
        
        # Show if the tool execution was successful
        tool_result = response.get("tool_result", {})
        if tool_result.get("success", False):
            print("Tool execution was successful.")
        else:
            error = tool_result.get("error", "Unknown error")
            print(f"Tool execution failed: {error}")
    else:
        reason = response.get("reason", "No reason provided")
        print(f"\nAction Summary: No action was taken. Reason: {reason}")
    
except Exception as e:
    print(f"Exception: {e}")
    print(traceback.format_exc())
