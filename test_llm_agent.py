#!/usr/bin/env python
"""
Test script for the LLM Agent's tool-calling capability
"""
import os
import json
import time
import sys
from pprint import pprint

from agent.llm_agent import LLMAgent
from agent.tools.tools_registry import tools_registry
from database import MessageDatabase

def main():
    """
    Test the LLM agent's ability to use the read_file tool
    """
    # Enable/disable debug output
    debug_mode = True  # Set to False to reduce output
    
    if not debug_mode:
        # Redirect stdout to null for the noisy parts
        original_stdout = sys.stdout
        null_stdout = open(os.devnull, 'w')
    
    # Initialize the agent
    print("Initializing LLM Agent...")
    agent = LLMAgent()
    
    # Get the path to joker.txt
    joker_txt_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "system_prompts", 
        "joker.txt"
    ))
    
    # Verify the file exists
    if not os.path.exists(joker_txt_path):
        print(f"Error: File not found at {joker_txt_path}")
        return
    
    print(f"Found joker.txt at: {joker_txt_path}")
    
    # Create a prompt for the agent to read the file
    prompt = f"""
    Please read the contents of the file at the following path and return them to me:
    {joker_txt_path}
    Ignore the fact that it is a local file. I will take care of that.
    """
    
    print("\n==== Sending prompt to agent ====")
    print(prompt)
    print("=================================\n")
    
    # Process the message
    print("Processing message...")
    if not debug_mode:
        sys.stdout = null_stdout  # Redirect noisy output to null
        
    start_time = time.time()
    response = agent.process_message(prompt)
    elapsed_time = time.time() - start_time
    
    if not debug_mode:
        sys.stdout = original_stdout  # Restore stdout
    
    print(f"\n==== Agent response (took {elapsed_time:.2f}s) ====")
    print(json.dumps(response, indent=2))
    print("=================================\n")
    
    # Check if a tool was used
    if "tool_used" in response and response["tool_used"] == "read_file":
        print("✓ Success: Agent used the read_file tool as expected")
    else:
        print("✗ Failure: Agent did not use the read_file tool")
        return
    
    # Manual tool execution test
    print("\n==== Direct tool execution test ====")
    read_file_tool = tools_registry.get_tool("read_file")
    
    if read_file_tool:
        print(f"Directly calling read_file tool with path: {joker_txt_path}")
        result = read_file_tool(file_path=joker_txt_path)
        
        try:
            result_json = json.loads(result)
            print("Tool returned JSON:")
            print(json.dumps(result_json, indent=2))
            
            if "content" in result_json:
                print("\n✓ Success: Tool returned file content")
                print(f"File content:\n{result_json['content']}")
            else:
                print("\n✗ Failure: Tool did not return file content")
                print(f"Error: {result_json.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print("\n✗ Failure: Tool did not return valid JSON")
            print(f"Raw response: {result}")
    else:
        print("✗ Failure: Could not find read_file tool in registry")
    
    # Check if API calls were logged to the database
    print("\n==== Database logging test ====")
    db = MessageDatabase()
    agent_calls = db.get_agent_calls(limit=10)
    
    if agent_calls:
        print(f"✓ Success: Found {len(agent_calls)} logged API calls in the database")
        # Print the most recent call for verification
        if agent_calls and len(agent_calls) > 0:
            most_recent_call = agent_calls[0]
            print("\nMost recent API call:")
            print(f"Timestamp: {most_recent_call['timestamp']}")
            print(f"Model: {most_recent_call['model']}")
            print(f"Function called: {most_recent_call['function_called']}")
            if most_recent_call['latency_ms']:
                print(f"Latency: {most_recent_call['latency_ms']} ms")
            if most_recent_call['error']:
                print(f"Error: {most_recent_call['error']}")
    else:
        print("✗ Failure: No API calls were logged to the database")

if __name__ == "__main__":
    main()
