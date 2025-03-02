#!/usr/bin/env python
"""
Dedicated test script for tools only, avoiding any agent initialization
"""
import os
import json
import sys
from pprint import pprint

# Import only the database and registry components
from database import MessageDatabase
from agent.tools.tools_registry import tools_registry

def main():
    """
    Test the tools directly without initializing the agent
    """
    # First clear the database of any previous test data
    db = MessageDatabase()
    db.delete_all_injections()
    print("Database cleared of previous injections")
    
    # Test inject_instruction
    print("\n==== Testing inject_instruction tool ====")
    inject_tool = tools_registry.get_tool("inject_instruction")
    if inject_tool:
        instruction = "Ask the user how their meditation practice is going"
        result = inject_tool(instruction=instruction)
        print(f"Tool result: {result}")
        
        # Check the database to verify the injection was saved
        injections = db.get_injections()
        print(f"Found {len(injections)} injections in database")
        if injections:
            print("Most recent injection:")
            pprint(injections[0])
    else:
        print("inject_instruction tool not found!")
    
    # Test send_notification
    print("\n==== Testing send_notification tool ====")
    notify_tool = tools_registry.get_tool("send_notification")
    if notify_tool:
        message = "Time for your afternoon mindfulness session!"
        result = notify_tool(message=message)
        print(f"Tool result: {result}")
    else:
        print("send_notification tool not found!")
    
    # Close the database connection
    db.close()
    print("\nTests completed")

if __name__ == "__main__":
    main()
