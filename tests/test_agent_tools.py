#!/usr/bin/env python
"""
Test script for the new Agent tools: inject_instruction and send_notification
"""
import os
import json
import time
import sys
from pprint import pprint

# We will NOT import LLMAgent here to avoid triggering the automatic database cleanup
# from agent.llm_agent import LLMAgent
from agent.tools.tools_registry import tools_registry
from database import MessageDatabase

def test_inject_instruction():
    """
    Test the inject_instruction tool
    """
    print("\n==== Testing inject_instruction tool ====")
    
    # Clear database before starting the test
    db = MessageDatabase()
    db.delete_all_injections()
    print("Cleared all injections from the database")
    
    # Get the tool from the registry
    inject_tool = tools_registry.get_tool("inject_instruction")
    
    if inject_tool:
        print("Found inject_instruction tool in registry")
        
        # Test the tool with a sample instruction
        instruction = "Ask the user if they meditated this morning"
        print(f"Injecting instruction: '{instruction}'")
        
        result = inject_tool(instruction=instruction)
        
        try:
            result_json = json.loads(result)
            print("Tool returned JSON:")
            print(json.dumps(result_json, indent=2))
            
            if result_json.get("success"):
                print("✓ Success: Instruction injected successfully")
                
                # Check if the injection was saved to the database
                injections = db.get_injections(limit=1)
                
                if injections and len(injections) > 0:
                    print("✓ Success: Injection saved to database")
                    print(f"Injection content: '{injections[0]['injection']}'")
                else:
                    print("✗ Failure: Injection not found in database")
            else:
                print(f"✗ Failure: {result_json.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print("✗ Failure: Tool did not return valid JSON")
            print(f"Raw response: {result}")
    else:
        print("✗ Failure: Could not find inject_instruction tool in registry")

def test_send_notification():
    """
    Test the send_notification tool
    """
    print("\n==== Testing send_notification tool ====")
    
    # Get the tool from the registry
    notification_tool = tools_registry.get_tool("send_notification")
    
    if notification_tool:
        print("Found send_notification tool in registry")
        
        # Test the tool with a sample notification
        message = "Hey there! Just checking in to see how you're doing today."
        print(f"Sending notification: '{message}'")
        
        result = notification_tool(message=message)
        
        try:
            result_json = json.loads(result)
            print("Tool returned JSON:")
            print(json.dumps(result_json, indent=2))
            
            if result_json.get("success"):
                print("✓ Success: Notification sent successfully")
                print("Check your ntfy.sh app or browser to confirm")
            else:
                print(f"✗ Failure: {result_json.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print("✗ Failure: Tool did not return valid JSON")
            print(f"Raw response: {result}")
    else:
        print("✗ Failure: Could not find send_notification tool in registry")

def test_with_llm_agent():
    """
    Test the tools with the LLM Agent
    """
    print("\n==== Testing tools with LLM Agent ====")
    
    # We're NOT testing with the LLM Agent in this script as it
    # would delete our injections when it starts
    print("LLM Agent testing skipped - use a separate script to test with the agent")

def main():
    """
    Run all tests
    """
    # Test individual tools
    test_inject_instruction()
    test_send_notification()
    
    # We're not testing with the LLM agent to avoid database conflicts
    # test_with_llm_agent()

if __name__ == "__main__":
    main()
