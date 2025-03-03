#!/usr/bin/env python
"""
Direct test script for the read_file tool without LLM
"""
import os
import json
from agent.tools import tools_registry

def main():
    """
    Test the read_file tool directly
    """
    # Get the read_file tool
    read_file_tool = tools_registry.get_tool("read_file")
    
    if not read_file_tool:
        print("Error: read_file tool not found in registry")
        return
    
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
    
    # Call the tool directly
    print(f"Calling read_file tool with path: {joker_txt_path}")
    result = read_file_tool(file_path=joker_txt_path)
    
    try:
        result_json = json.loads(result)
        print("Tool returned JSON:")
        print(json.dumps(result_json, indent=2))
        
        if "content" in result_json:
            print("\nFile content:")
            print(result_json["content"])
        else:
            print(f"\nError: {result_json.get('error', 'Unknown error')}")
    except json.JSONDecodeError:
        print("Error: Tool did not return valid JSON")
        print(f"Raw response: {result}")

if __name__ == "__main__":
    main()
