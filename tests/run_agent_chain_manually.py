#!/usr/bin/env python
"""
Script to test the AgentChain component from agent_chain.py.

This script demonstrates the execution of the full agent chain workflow:
1. Thinking Agent makes a decision
2. Decision is parsed to extract tool information
3. Tool is executed if needed

Usage:
    python run_agent_chain_manually.py
    python run_agent_chain_manually.py --file agent_prompt.txt
    python run_agent_chain_manually.py --template agent_test_prompt.txt
    python run_agent_chain_manually.py --prompt "send the user a test notification"
"""

import json
import sys
import os
import argparse
from agent.agent_chain import AgentChain

def print_with_highlights(title, content):
    """Print content with highlighted title."""
    print(f"\n{title}")
    print(json.dumps(content, indent=2))
    print()

def read_prompt_from_file(filename):
    """Read prompt content from a file in the system_prompts directory."""
    file_path = os.path.join("system_prompts", filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            print(f"Loaded prompt from {file_path}")
            return content
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file: {str(e)}")
        sys.exit(1)

def get_prompt_template_path(filename):
    """Get the full path to a prompt template file in the system_prompts directory."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_prompts", filename)

def run_agent_chain(prompt=None, template_path=None):
    """
    Execute the agent chain with optional custom prompt or template.
    
    Args:
        prompt (str, optional): Custom prompt text to use directly.
        template_path (str, optional): Path to a template file with placeholders.
            If provided, the template will be processed for placeholders.
    """
    # Initialize the agent chain
    print("Initializing Agent Chain...")
    agent_chain = AgentChain()
    print("Executing agent chain...")

    # Use provided prompt, template, or default example prompt
    if template_path:
        print(f"Using template: {template_path}")
        # Let the AgentChain handle the template and placeholders
        custom_prompt = None
        custom_prompt_path = template_path
    elif prompt is None:
        # Default example prompt
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
        custom_prompt_path = None
    else:
        # Use the provided prompt text directly
        custom_prompt = prompt
        custom_prompt_path = None
    
    # Execute the agent chain with the appropriate parameters
    result = agent_chain.execute(custom_prompt=custom_prompt, custom_prompt_path=custom_prompt_path)
    
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

def main():
    """Parse command-line arguments and execute the agent chain."""
    parser = argparse.ArgumentParser(description='Run the agent chain with custom input.')
    
    # Create a mutually exclusive group for the three options
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--file', type=str, help='File in system_prompts directory to use as raw prompt text')
    group.add_argument('--template', type=str, help='Template file in system_prompts directory to use (placeholders will be replaced)')
    group.add_argument('--prompt', type=str, help='Custom prompt text to use directly')
    
    args = parser.parse_args()
    
    # Determine which prompt to use
    custom_prompt = None
    template_path = None
    
    if args.template:
        print(f"Using template file: {args.template}")
        template_path = get_prompt_template_path(args.template)
    elif args.file:
        print(f"Using prompt from file: {args.file}")
        custom_prompt = read_prompt_from_file(args.file)
    elif args.prompt:
        print(f"Using provided prompt text")
        custom_prompt = args.prompt
    
    # Run the agent chain with the determined parameters
    run_agent_chain(prompt=custom_prompt, template_path=template_path)

if __name__ == "__main__":
    main()
