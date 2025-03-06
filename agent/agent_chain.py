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
import time
import logging
from typing import Dict, Any, Optional, Tuple, List

# Import the ThinkingAgent
from .thinking_agent import ThinkingAgent

# Import the tools registry
from .tools.tools_registry import tools_registry

# Import database for logging
from database import MessageDatabase

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger('agent_chain')
log_file = os.path.join(log_dir, 'agent_chain.log')
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AgentChain:
    """
    Chain that coordinates the execution of thinking and tool calling.
    
    The workflow is:
    1. ThinkingAgent decides if a tool should be used and which one
    2. Parse the thinking agent's output to extract tool name and arguments
    3. Execute the tool if needed
    """
    
    def __init__(self, prompt_path: Optional[str] = None, db: Optional[MessageDatabase] = None):
        """
        Initialize the AgentChain with the thinking agent and tools registry.
        
        Args:
            prompt_path (Optional[str]): Path to a custom prompt template file.
                If None, uses the default agent_prompt.txt
            db (Optional[MessageDatabase]): Database instance for logging agent calls
        """
        # Initialize ThinkingAgent with optional custom prompt path
        self.thinking_agent = ThinkingAgent(prompt_path=prompt_path)
        self.tools_registry = tools_registry
        self.db = db
        logger.info("AgentChain initialized")
    
    def _log_agent_call(self, prompt: str, response: Dict[str, Any], latency_ms: int, error: Optional[str] = None) -> None:
        """
        Log the agent call to the database if available and to a log file.
        
        Args:
            prompt (str): The prompt sent to the agent
            response (Dict[str, Any]): The agent's response
            latency_ms (int): Execution time in milliseconds
            error (Optional[str]): Error message if an error occurred
        """
        # Get current timestamp with timezone information
        local_timezone = datetime.datetime.now().astimezone().tzinfo
        timestamp = datetime.datetime.now(local_timezone).isoformat()
        
        # Extract relevant information
        model = "thinking-agent"  # This is a placeholder as we're not directly using an LLM here
        
        # Extract function call information if available
        function_called = None
        function_args = None
        function_response = None
        
        if response.get("action_taken", False):
            function_called = response.get("tool_used", "")
            function_args = json.dumps(response.get("tool_args", {}))
            function_response = json.dumps(response.get("tool_result", {}))
        
        # Log to file
        log_message = f"Agent call executed | Timestamp: {timestamp} | Model: {model} | Latency: {latency_ms}ms"
        if function_called:
            log_message += f" | Tool: {function_called}"
        if error:
            log_message += f" | Error: {error}"
        
        logger.info(log_message)
        
        # Log prompt and response details
        logger.info(f"Prompt: {prompt[:200]}... (truncated if longer)")
        
        # Log the full response
        response_str = json.dumps(response, indent=2)
        logger.info(f"Response: {response_str}")
        
        # Log to database if available
        if self.db is None:
            logger.warning("Database not available for logging")
            return
            
        try:
            # Log using the database's log_agent_call method
            call_data = {
                'timestamp': timestamp,
                'model': model,
                'prompt': prompt,
                'response': response_str,
                'function_called': function_called,
                'function_args': function_args,
                'function_response': function_response,
                'error': error,
                'latency_ms': latency_ms
            }
            
            success = self.db.log_agent_call(call_data)
            if success:
                logger.info(f"Successfully logged agent call to database, latency: {latency_ms}ms")
            else:
                logger.error("Failed to log agent call to database")
            
        except Exception as e:
            logger.error(f"Error logging agent call to database: {e}")
    
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
        
        # Track overall execution time
        overall_start_time = time.time()
        
        # Log the start of execution
        local_timezone = datetime.datetime.now().astimezone().tzinfo
        start_timestamp = datetime.datetime.now(local_timezone).isoformat()
        logger.info(f"Starting agent chain execution at {start_timestamp}")
        
        # Main execution loop - continue until we decide not to use a tool or reach max iterations
        while current_iteration < max_iterations:
            current_iteration += 1
            
            # Step 1: Call the thinking agent to decide what to do
            start_time = time.time()
            thinking_result = self.thinking_agent.process_message(
                custom_prompt=current_prompt,
                custom_prompt_path=current_prompt_path
            )
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            decision_text = thinking_result.get("decision", "")
            
            # Log the agent call
            self._log_agent_call(
                current_prompt if isinstance(current_prompt, str) else "[Custom prompt from file]", 
                thinking_result, 
                latency_ms
            )
            
            # Add the decision to the history
            decision_time = thinking_result.get("timestamp", datetime.datetime.now(local_timezone).isoformat())
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
                logger.info(f"Iteration {current_iteration}: Agent decided not to use any tools.")
                final_result = {
                    "action_taken": False,
                    "decision": decision_text,
                    "reason": tool_decision.get("reason", "No reason provided"),
                    "decision_history": decision_history,
                    "action_history": action_history,
                    "iterations": current_iteration,
                    "timestamp": datetime.datetime.now(local_timezone).isoformat()
                }
                break
            
            # Step 3: Execute the tool if needed
            tool_name = tool_decision["tool_name"]
            tool_args = tool_decision["tool_args"]
            
            # Log the tool execution
            logger.info(f"Iteration {current_iteration}: Executing tool: {tool_name} with args: {json.dumps(tool_args)}")
            
            # Execute the tool
            tool_result = self._execute_tool(tool_name, tool_args)
            tool_execution_time = datetime.datetime.now(local_timezone).isoformat()
            
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
                logger.warning(f"Reached maximum iterations ({max_iterations}). Stopping execution chain.")
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
                    "timestamp": datetime.datetime.now(local_timezone).isoformat()
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
                "timestamp": datetime.datetime.now(local_timezone).isoformat()
            }
            
        # Log overall execution time
        overall_end_time = time.time()
        overall_latency_ms = int((overall_end_time - overall_start_time) * 1000)
        logger.info(f"Overall agent execution time: {overall_latency_ms}ms")
        
        return final_result
        
    def _format_history_for_next_iteration(self, decision_history: List[Dict[str, Any]], action_history: List[Dict[str, Any]]) -> str:
        """
        Format the decision and action history into a readable format for the next iteration
        
        Args:
            decision_history (List[Dict]): History of decisions made by the thinking agent
            action_history (List[Dict]): History of actions taken
            
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
                
                context_parts.append(f"Iteration {iteration} Decision: {decision_text}")
                
                # Add the corresponding action if available
                if idx < len(action_history):
                    action = action_history[idx]
                    tool_name = action.get("tool_name", "")
                    tool_args = action.get("tool_args", {})
                    tool_result = action.get("tool_result", {})
                    
                    args_str = ", ".join([f"{k}='{v}'" for k, v in tool_args.items()])
                    context_parts.append(f"Iteration {iteration} Tool executed: {tool_name}({args_str})")
                    
                    # Add a summary of the tool result
                    # Handle different result types (dict, string, or other)
                    if isinstance(tool_result, dict):
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
                    elif isinstance(tool_result, str):
                        # For string results, display the string directly
                        # Truncate if it's too long
                        if len(tool_result) > 100:
                            context_parts.append(f"Result: {tool_result[:100]}...")
                        else:
                            context_parts.append(f"Result: {tool_result}")
                    else:
                        # For other types, convert to string
                        context_parts.append(f"Result: {str(tool_result)}")
                
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
            Dict[str, Any]: Dictionary with the parsed decision
        """
        # Default result - no tool usage
        result = {
            "should_use_tool": False,
            "reason": "No tool specified in decision"
        }
        
        # Skip parsing if decision is empty or None
        if not decision_text:
            logger.warning("Empty decision text received from thinking agent")
            return result
        
        # Log the decision text we're parsing
        logger.debug(f"Parsing decision text: {decision_text[:100]}... (truncated)")
        
        # First, try to match the structured format: USE_TOOL[tool_name]{args}
        tool_match = re.search(r"USE_TOOL\s*\[([^\]]+)\]\s*\{([^}]*)\}", decision_text, re.DOTALL)
        
        if tool_match:
            # Parse the structured format
            tool_name = tool_match.group(1).strip()
            args_str = tool_match.group(2).strip()
            
            # Validate that the tool exists in our registry
            if tool_name not in self.tools_registry:
                result["reason"] = f"Tool '{tool_name}' not found in registry"
                logger.error(f"Tool '{tool_name}' not found in registry")
                return result
            
            # Parse the arguments
            tool_args = self._parse_tool_args(args_str)
            
            # Return the successful parsing result
            result = {
                "should_use_tool": True,
                "tool_name": tool_name,
                "tool_args": tool_args
            }
            
            logger.info(f"Successfully parsed decision to use tool: {tool_name} (structured format)")
            return result
        
        # If structured format didn't match, try the natural language format:
        # "Yes: Call the send_notification tool with message 'value' because reason"
        # "Yes: Call the inject_instruction tool with instruction 'value' because reason"
        
        # Check if the decision starts with "Yes:" indicating intent to use a tool
        if re.search(r'^\s*yes\s*:', decision_text, re.IGNORECASE):
            # Try to extract the tool name and parameters
            
            # First check for send_notification tool
            notification_match = re.search(
                r"call\s+the\s+send_notification\s+tool\s+with\s+(?:message|notification)\s+['\"](.*?)['\"]", 
                decision_text, 
                re.IGNORECASE
            )
            if notification_match:
                message = notification_match.group(1).strip()
                tool_args = {"message": message}
                
                result = {
                    "should_use_tool": True,
                    "tool_name": "send_notification",
                    "tool_args": tool_args
                }
                
                logger.info(f"Successfully parsed decision to use tool: send_notification (natural language format)")
                return result
            
            # Then check for inject_instruction tool
            instruction_match = re.search(
                r"call\s+the\s+inject_instruction\s+tool\s+with\s+(?:instruction|message)\s+['\"](.*?)['\"]", 
                decision_text, 
                re.IGNORECASE
            )
            if instruction_match:
                instruction = instruction_match.group(1).strip()
                tool_args = {"instruction": instruction}
                
                result = {
                    "should_use_tool": True,
                    "tool_name": "inject_instruction",
                    "tool_args": tool_args
                }
                
                logger.info(f"Successfully parsed decision to use tool: inject_instruction (natural language format)")
                return result
            
            # If we got here with a 'Yes:' decision but couldn't extract tool details, log a warning
            logger.warning(f"Found 'Yes:' in decision but couldn't extract tool details: {decision_text[:100]}...")
            result["reason"] = "Couldn't parse tool details from 'Yes:' decision"
        
        # Check for explicit decision not to use tools
        if "DO_NOT_USE_TOOL" in decision_text or re.search(r'^\s*no\s*:', decision_text, re.IGNORECASE):
            result["reason"] = "Agent explicitly decided not to use a tool"
            logger.info("Agent explicitly decided not to use a tool")
            return result
            
        # If no pattern matched, log a warning and return the default 'no tool' result
        logger.warning("No valid tool specification found in decision")
        return result
    
    def _parse_tool_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse tool arguments from a string format.
        
        Args:
            args_str (str): String containing tool arguments
            
        Returns:
            Dict[str, Any]: Dictionary of parsed arguments
        """
        tool_args = {}
        if not args_str:
            return tool_args
            
        try:
            # First attempt to parse as JSON
            try:
                tool_args = json.loads(args_str)
                logger.debug(f"Parsed tool args as JSON: {json.dumps(tool_args)}")
                return tool_args
            except json.JSONDecodeError:
                # Fall back to manual parsing
                for arg_pair in re.findall(r'([^=,]+)=([^,]+)(?:,|$)', args_str):
                    key = arg_pair[0].strip()
                    value = arg_pair[1].strip()
                    
                    # Try to parse value as JSON if it looks like a data structure
                    if value.startswith('[') or value.startswith('{') or value.lower() in ['true', 'false', 'null'] or re.match(r'^-?\d+(\.\d+)?$', value):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            # Keep as string if JSON parsing fails
                            pass
                    
                    # Remove surrounding quotes if present
                    if isinstance(value, str) and len(value) >= 2:
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith('\'') and value.endswith('\'')):
                            value = value[1:-1]
                    
                    tool_args[key] = value
                logger.debug(f"Parsed tool args manually: {json.dumps(tool_args)}")
                return tool_args
        except Exception as e:
            logger.error(f"Error parsing tool arguments: {e}")
            return {}
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """
        Execute a tool from the tools registry.
        
        Args:
            tool_name (str): Name of the tool to execute
            tool_args (Dict[str, Any]): Arguments to pass to the tool
            
        Returns:
            Any: The result returned by the tool
        """
        start_time = time.time()
        
        try:
            # Get the tool function from the registry using get_tool method
            tool_fn = self.tools_registry.get_tool(tool_name)
            
            if not tool_fn:
                error_msg = f"Tool '{tool_name}' not found in registry"
                logger.error(error_msg)
                return {"error": error_msg}
            
            # Log tool execution
            logger.info(f"Executing tool: {tool_name} with args: {json.dumps(tool_args)}")
            
            # Execute the tool with the provided arguments
            result = tool_fn(**tool_args)
            
            # Calculate and log execution time
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)
            logger.info(f"Tool {tool_name} executed in {execution_time_ms}ms")
            
            # Return the result
            return result
            
        except Exception as e:
            # Log and return any errors that occur during execution
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.error(f"{error_msg} (execution time: {execution_time_ms}ms)")
            return {"error": error_msg}


if __name__ == "__main__":
    # Example usage
    agent_chain = AgentChain()
    result = agent_chain.execute()
    print(f"AgentChain execution result: {json.dumps(result, indent=2)}")
