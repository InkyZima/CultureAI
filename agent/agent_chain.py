"""
Here is the workflow/chain for tool execution:
- A thinking model gets called. It shall consider all context information to decide if and which tool to execute. It returns its decision, along with the information which tool to use and with which input.
- In this file, the tool-calling output from the thinking model is deconstructed (manually), and the tool is called.
- After the tool was called and retured a result/output, the thinking model gets called again (loop, until it decides not to call another tool or maximum up to 5 times), with the additional context of its last decision, tool call and tool output. 
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
    
    def __init__(self, prompt_path: Optional[str] = None):
        """
        Initialize the AgentChain with the thinking agent and tools registry.
        
        Args:
            prompt_path (Optional[str]): Path to a custom prompt template file.
                If None, uses the default agent_prompt.txt
        """
        # Initialize ThinkingAgent with optional custom prompt path
        self.thinking_agent = ThinkingAgent(prompt_path=prompt_path)
        self.tools_registry = tools_registry
    
    def execute(self, custom_prompt: Optional[str] = None, custom_prompt_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the full agent chain.
        
        Args:
            custom_prompt (Optional[str]): Custom prompt text to use directly.
                If None, uses the prompt template specified in ThinkingAgent.
            custom_prompt_path (Optional[str]): Path to a custom prompt template file.
                Overrides the default template for this execution only.
                
        Returns:
            Dict[str, Any]: Dictionary with the chain execution results
        """
        # Initialize loop variables
        max_iterations = 5
        current_iteration = 0
        decision_history = []
        action_history = []
        
        # Start with the original prompt
        current_prompt = custom_prompt
        current_prompt_path = custom_prompt_path
        final_result = None
        
        # Main execution loop - continue until we decide not to use a tool or reach max iterations
        while current_iteration < max_iterations:
            current_iteration += 1
            
            # Step 1: Call the thinking agent to decide what to do
            thinking_result = self.thinking_agent.process_message(
                custom_prompt=current_prompt,
                custom_prompt_path=current_prompt_path
            )
            decision_text = thinking_result.get("decision", "")
            
            # Add the decision to the history
            decision_time = thinking_result.get("timestamp", datetime.datetime.now().isoformat())
            decision_entry = {
                "iteration": current_iteration,
                "timestamp": decision_time,
                "decision": decision_text
            }
            decision_history.append(decision_entry)
            
            # Step 2: Parse the decision to extract tool information
            tool_decision = self._parse_decision(decision_text)
            
            # If the agent decides not to use a tool, break the loop
            if not tool_decision["should_use_tool"]:
                print(f"Iteration {current_iteration}: Agent decided not to use any tools.")
                final_result = {
                    "action_taken": False,
                    "decision": decision_text,
                    "reason": tool_decision.get("reason", "No reason provided"),
                    "decision_history": decision_history,
                    "action_history": action_history,
                    "iterations": current_iteration,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                break
            
            # Step 3: Execute the tool if needed
            tool_name = tool_decision["tool_name"]
            tool_args = tool_decision["tool_args"]
            
            # Log the tool execution
            print(f"Iteration {current_iteration}: Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool
            tool_result = self._execute_tool(tool_name, tool_args)
            tool_execution_time = datetime.datetime.now().isoformat()
            
            # Add the action to the history
            action_entry = {
                "iteration": current_iteration,
                "timestamp": tool_execution_time,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "tool_result": tool_result
            }
            action_history.append(action_entry)
            
            # If this is the last allowed iteration, prepare the final result
            if current_iteration >= max_iterations:
                print(f"Reached maximum iterations ({max_iterations}). Stopping execution chain.")
                final_result = {
                    "action_taken": True,
                    "tool_used": tool_name,
                    "tool_args": tool_args,
                    "tool_result": tool_result,
                    "decision": decision_text,
                    "decision_history": decision_history,
                    "action_history": action_history,
                    "iterations": current_iteration,
                    "max_iterations_reached": True,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                break
                
            # Prepare context for the next iteration
            context_history = self._format_history_for_next_iteration(decision_history, action_history)
            
            # For subsequent iterations, always use context_history with the original template
            # For first iteration, we might have used custom_prompt or custom_prompt_path
            current_prompt = context_history
            current_prompt_path = None  # Reset to use default template for subsequent iterations
        
        # If we didn't set a final result (this shouldn't happen but just in case)
        if final_result is None:
            final_result = {
                "action_taken": False,
                "error": "Execution chain completed without a final result",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        return final_result
        
    def _format_history_for_next_iteration(self, decision_history: list, action_history: list) -> str:
        """
        Format the decision and action history into a context string for the next iteration.
        
        Args:
            decision_history (list): List of previous decisions
            action_history (list): List of previous actions and their results
            
        Returns:
            str: Formatted context history string
        """
        # Only include the most recent history entries to keep the context manageable
        recent_entries = min(len(decision_history), 3)  # Show at most the last 3 iterations
        
        context_parts = []
        context_parts.append("**Previous actions and decisions:**\n")
        
        for i in range(recent_entries):
            idx = len(decision_history) - recent_entries + i
            if idx >= 0:
                decision = decision_history[idx]
                iteration = decision.get("iteration", "?")
                decision_text = decision.get("decision", "")
                timestamp = decision.get("timestamp", "")
                
                context_parts.append(f"Iteration {iteration} [{timestamp}] Decision: {decision_text}")
                
                # Add the corresponding action if available
                if idx < len(action_history):
                    action = action_history[idx]
                    tool_name = action.get("tool_name", "")
                    tool_args = action.get("tool_args", {})
                    tool_result = action.get("tool_result", {})
                    
                    args_str = ", ".join([f"{k}='{v}'" for k, v in tool_args.items()])
                    context_parts.append(f"Iteration {iteration} Tool executed: {tool_name}({args_str})")
                    
                    # Add a summary of the tool result
                    if tool_result.get("success", False):
                        if tool_name == "send_notification":
                            context_parts.append(f"Result: Notification sent successfully")
                        elif tool_name == "inject_instruction":
                            context_parts.append(f"Result: Instruction injected successfully")
                        else:
                            context_parts.append(f"Result: Tool execution successful")
                    else:
                        error = tool_result.get("error", "Unknown error")
                        context_parts.append(f"Result: Tool execution failed - {error}")
                
                context_parts.append("")  # Empty line between iterations
        
        # Add a prompt for the next decision
        context_parts.append("\nBased on the previous actions and their results, decide if another tool should be used.")
        context_parts.append("Remember that you can either choose to use a tool again or decide that no further action is needed at this time.")
        
        return "\n".join(context_parts)
    
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
        
        # Normalize the decision text
        decision_text = decision_text.strip()
        
        # Check if the decision is to use a tool (more flexible pattern matching)
        if re.search(r'(?:^|\s)(?:[-*•]?\s*)?yes:', decision_text, re.IGNORECASE):
            result["should_use_tool"] = True
            
            # Extract tool name, arguments, and reason using regex
            # More flexible pattern that can handle variations in formatting
            
            # Check for inject_instruction tool
            inject_match = re.search(r"inject_instruction tool with (?:instruction|message) ['\[](.*?)['|\]] because (.*)", decision_text, re.IGNORECASE)
            if inject_match:
                result["tool_name"] = "inject_instruction"
                result["tool_args"] = {"instruction": inject_match.group(1)}
                result["reason"] = inject_match.group(2)
                return result
            
            # Check for send_notification tool - more flexible pattern
            notify_match = re.search(r"send_notification tool with (?:message|notification) ['\[](.*?)['|\]] because (.*)", decision_text, re.IGNORECASE)
            if notify_match:
                result["tool_name"] = "send_notification"
                result["tool_args"] = {"message": notify_match.group(1)}
                result["reason"] = notify_match.group(2)
                return result
            
            # Generic pattern for any tool as a fallback
            generic_match = re.search(r"(?:use|call) the (\w+) tool with (?:\w+) ['\[](.*?)['|\]] because (.*)", decision_text, re.IGNORECASE)
            if generic_match:
                tool_name = generic_match.group(1).lower()
                
                # Map to proper tool names if there's slight variation
                if "notification" in tool_name:
                    tool_name = "send_notification"
                    arg_name = "message"
                elif "inject" in tool_name or "instruction" in tool_name:
                    tool_name = "inject_instruction"
                    arg_name = "instruction"
                else:
                    # Default for unknown tools
                    arg_name = "value"
                
                result["tool_name"] = tool_name
                result["tool_args"] = {arg_name: generic_match.group(2)}
                result["reason"] = generic_match.group(3)
                return result
        
        # If decision is not to use a tool
        elif re.search(r'(?:^|\s)(?:[-*•]?\s*)?no:', decision_text, re.IGNORECASE):
            # Extract reason - more flexible pattern
            reason_match = re.search(r"no:\s*(.*)", decision_text, re.IGNORECASE)
            if reason_match:
                result["reason"] = reason_match.group(1)
        
        # Log the parsing attempt to help with debugging
        if not result["should_use_tool"] and not result["reason"] == "No clear decision was made":
            print(f"Parsed decision: No tool use. Reason: {result['reason']}")
        elif not result["should_use_tool"]:
            print(f"Failed to parse decision clearly: {decision_text[:100]}...")
        
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
