"""
Here is the workflow/chain for tool execution:
1. A thinking model gets called. It shall consider all context information to decide if and which tool to execute. It returns its decision, along with the information which tool to use and with which input.
2. A non-thinking model gets called with the output of the thinking model. It shall turn this output into a standard json tool call. This shall be its output.
3. In code, the tool gets called using this output of the non-thinking model.

The 1. step is implemented in thinking_agent.py.
The 2. step is implemented in calling_agent.py.
Everything (including step 3. / calling the tool) comes together in this file.
"""

import os
import json
import re
import datetime
from typing import Dict, Any, Optional, Tuple

# Import the ThinkingAgent
from .thinking_agent import ThinkingAgent

# Import the tools registry
from .tools.tools_registry import tools_registry

class AgentChain:
    """
    Chain that coordinates the execution of thinking and tool calling.
    
    The workflow is:
    1. ThinkingAgent decides if a tool should be used and which one
    2. Parse the thinking agent's output to extract tool name and arguments
    3. Execute the tool if needed
    """
    
    def __init__(self):
        """Initialize the AgentChain with the thinking agent and tools registry."""
        self.thinking_agent = ThinkingAgent()
        self.tools_registry = tools_registry
    
    def execute(self, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the full agent chain.
        
        Args:
            custom_prompt (Optional[str]): Custom prompt to use. If None, uses agent_prompt.txt
            
        Returns:
            Dict[str, Any]: Dictionary with the chain execution results
        """
        # Step 1: Call the thinking agent to decide what to do
        thinking_result = self.thinking_agent.process_message(custom_prompt)
        decision_text = thinking_result.get("decision", "")
        
        # Step 2: Parse the decision to extract tool information
        tool_decision = self._parse_decision(decision_text)
        
        # Step 3: Execute the tool if needed
        if tool_decision["should_use_tool"]:
            tool_name = tool_decision["tool_name"]
            tool_args = tool_decision["tool_args"]
            
            # Log the tool execution
            print(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool
            tool_result = self._execute_tool(tool_name, tool_args)
            
            # Prepare and return the result
            return {
                "action_taken": True,
                "tool_used": tool_name,
                "tool_args": tool_args,
                "tool_result": tool_result,
                "decision": decision_text,
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            # No tool was used
            return {
                "action_taken": False,
                "decision": decision_text,
                "reason": tool_decision.get("reason", "No reason provided"),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _parse_decision(self, decision_text: str) -> Dict[str, Any]:
        """
        Parse the thinking agent's decision text to extract tool information.
        
        Args:
            decision_text (str): The decision text from the thinking agent
            
        Returns:
            Dict[str, Any]: Dictionary with parsed tool information
        """
        # Default result with no tool
        result = {
            "should_use_tool": False,
            "tool_name": None,
            "tool_args": {},
            "reason": "No clear decision was made"
        }
        
        # Check if the decision is to use a tool
        if decision_text.lower().startswith("yes:"):
            result["should_use_tool"] = True
            
            # Extract tool name, arguments, and reason using regex
            # Format: "Yes: Call the [tool_name] tool with [arg_type] '[arg_value]' because [reason]"
            
            # Check for inject_instruction tool
            inject_match = re.search(r"inject_instruction tool with instruction '(.*?)' because (.*)", decision_text, re.IGNORECASE)
            if inject_match:
                result["tool_name"] = "inject_instruction"
                result["tool_args"] = {"instruction": inject_match.group(1)}
                result["reason"] = inject_match.group(2)
                return result
            
            # Check for send_notification tool
            notify_match = re.search(r"send_notification tool with message '(.*?)' because (.*)", decision_text, re.IGNORECASE)
            if notify_match:
                result["tool_name"] = "send_notification"
                result["tool_args"] = {"message": notify_match.group(1)}
                result["reason"] = notify_match.group(2)
                return result
        
        # If decision is not to use a tool or couldn't parse the tool
        elif decision_text.lower().startswith("no:"):
            # Extract reason
            reason_match = re.search(r"No: (.*)", decision_text)
            if reason_match:
                result["reason"] = reason_match.group(1)
        
        return result
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given name and arguments.
        
        Args:
            tool_name (str): The name of the tool to execute
            tool_args (Dict[str, Any]): The arguments for the tool
            
        Returns:
            Dict[str, Any]: The result of the tool execution
        """
        try:
            # Get the tool function from the registry
            tool_function = self.tools_registry.get_tool(tool_name)
            
            if not tool_function:
                return {
                    "success": False,
                    "error": f"Tool not found: {tool_name}"
                }
            
            # Execute the tool
            result_str = tool_function(**tool_args)
            
            # Parse the JSON result
            try:
                result = json.loads(result_str)
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Tool returned invalid JSON: {result_str}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool {tool_name}: {str(e)}"
            }


if __name__ == "__main__":
    # Example usage
    agent_chain = AgentChain()
    result = agent_chain.execute()
    print(f"AgentChain execution result: {json.dumps(result, indent=2)}")
