#!/usr/bin/env python
"""
Script to test the AgentChain component from agent_chain.py.

This script demonstrates the execution of the full agent chain workflow:
1. Thinking Agent makes a decision
2. Decision is parsed to extract tool information
3. Tool is executed if needed

Usage:
    python run_agent_chain_manually.py
"""

import json
import sys
from agent.agent_chain import AgentChain

def print_with_highlights(title, content):
    """Print content with highlighted title."""
    print(f"\n{title}")
    print(json.dumps(content, indent=2))
    print()

def main():
    """Execute the agent chain manually."""
    # Initialize the agent chain
    print("Initializing Agent Chain...")
    agent_chain = AgentChain()
    print("Executing agent chain...")

    # Create a custom prompt that will encourage the agent to use multiple tools
    custom_prompt = """
    The user has been inactive for 3 days and may have forgotten about their cultural practices.
    Additionally, their scheduled meditation session is coming up in 15 minutes according to their calendar.
    The user also mentioned they wanted to learn more about breathing techniques for their meditation practice.
    
    Current time: 10:45 AM, March 3, 2025
    Last conversation: The user mentioned they were feeling stressed about work and wanted to establish
    a regular meditation practice but often forgets. They also expressed interest in learning simple breathing techniques
    they could use during meditation to help with stress reduction.
    
    The AI assistant should first notify the user about their upcoming meditation session, 
    and then send a follow-up instruction about a simple breathing technique they could try during the session.
    
    Analyze the situation and decide if any tools should be used to help the user.
    """
    
    # Execute the agent chain with the custom prompt
    result = agent_chain.execute()
    
    # Print the result with nice formatting
    print_with_highlights("Agent Chain Execution Results:", result)
    
    # Provide a more human-readable summary
    if result.get("action_taken", False):
        # At least one tool was used
        print(f"Action Summary: Tool '{result.get('tool_used', 'unknown')}' was executed")
        
        # Add details specific to each tool
        if result.get("tool_used") == "send_notification":
            notification = result.get("tool_args", {}).get("message", "")
            print(f"Notification sent: '{notification}'")
        elif result.get("tool_used") == "inject_instruction":
            instruction = result.get("tool_args", {}).get("instruction", "")
            print(f"Instruction injected: '{instruction}'")
        
        # Print success/failure
        tool_result = result.get("tool_result", {})
        if tool_result.get("success", False):
            print("Tool execution was successful.")
        else:
            print(f"Tool execution failed: {tool_result.get('error', 'Unknown error')}")
            
        # Print iteration information
        print(f"Total iterations: {result.get('iterations', 1)}")
        if result.get('max_iterations_reached', False):
            print("Note: Maximum number of iterations was reached.")
    else:
        # No tool was used
        print(f"Action Summary: No action was taken. Reason: {result.get('reason', 'No reason provided')}")

if __name__ == "__main__":
    main()
