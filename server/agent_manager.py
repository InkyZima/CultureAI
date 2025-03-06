"""
Manages agent interactions and execution.
"""
import datetime
from agent.agent_chain import AgentChain
from agent.placeholder_handler import process_template
from server.config import socketio

class AgentManager:
    """
    Manages interactions with the agent chain and executes agent actions.
    """
    
    def __init__(self, message_manager):
        """
        Initialize the agent manager.
        
        Args:
            message_manager: The message manager instance for state management
        """
        self.message_manager = message_manager
        self.db = message_manager.db
    
    def handle_direct_agent_command(self, user_message):
        """
        Handle a direct command to the agent (prefixed with '@agent').
        
        Args:
            user_message (str): The user's message to the agent
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            # Extract the message part after "@agent"
            agent_prompt = user_message[7:].strip()
            
            # Run the agent chain with the prompt
            print(f"Running agent chain with prompt: {agent_prompt}")
            agent_chain = AgentChain(db=self.db)
            
            # Process any placeholders in the prompt
            processed_prompt = process_template(agent_prompt)
            
            # Execute the agent chain with the processed prompt
            result = agent_chain.execute(custom_prompt=processed_prompt)
            
            # Log the agent chain execution
            print(f"Agent Chain Execution Results:")
            print(f"Action taken: {result.get('action_taken', False)}")
            
            # Add a system message to inform the user
            # Get current time with timezone information
            current_time = datetime.datetime.now().astimezone()
            
            system_message = {
                'message': f"Agent chain executed with prompt: '{agent_prompt}'",
                'timestamp': current_time.isoformat(),
                'role': 'System'
            }
            self.message_manager.add_message(system_message)
            socketio.emit('message', system_message, broadcast=True)
            
            # Prepare the agent's response to the user
            agent_response_message = self._format_agent_response(result)
            
            # Send the agent's response back to the user
            agent_response = {
                'message': agent_response_message,
                'timestamp': current_time.isoformat(),
                'role': 'Agent-AI'
            }
            self.message_manager.add_message(agent_response)
            socketio.emit('message', agent_response, broadcast=True)
            
            return True
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_message = f"Error running agent chain: {str(e)}"
            print(error_message)
            print(f"Detailed traceback:\n{error_details}")
            
            # Get current time with timezone information
            current_time = datetime.datetime.now().astimezone()
            
            system_message = {
                'message': error_message,
                'timestamp': current_time.isoformat(),
                'role': 'System'
            }
            self.message_manager.add_message(system_message)
            socketio.emit('message', system_message, broadcast=True)
            return False
    
    def run_periodic_agent_check(self, user_message):
        """
        Run a periodic agent check to see if agent assistance is needed.
        
        Args:
            user_message (str): The user's most recent message
        """
        try:
            # Initialize and execute the agent chain
            agent_chain = AgentChain(db=self.db)
            
            # Create a custom prompt based on the current conversation state
            custom_prompt = f"""
            Current time: {datetime.datetime.now().isoformat()}
            The user has sent their {self.message_manager.user_message_counter}th message.
            Last message from user: "{user_message}"
            
            Analyze the conversation and decide if any tools should be used to help the user with their cultural practices.
            """
            
            result = agent_chain.execute(custom_prompt)
            
            # Log the agent chain execution
            print(f"Agent Chain Execution Results:")
            print(f"Action taken: {result.get('action_taken', False)}")
            
            if result.get('action_taken', False):
                tool_used = result.get('tool_used', 'unknown')
                print(f"Tool used: {tool_used}")
                
                # Add a system message about the agent's action
                tool_message = "I notice you might need assistance. "
                
                if tool_used == "send_notification":
                    notification = result.get('tool_args', {}).get('message', '')
                    tool_message += f"I've sent you a notification: '{notification}'"
                elif tool_used == "inject_instruction":
                    instruction = result.get('tool_args', {}).get('instruction', '')
                    tool_message += f"I'll be providing this guidance soon: '{instruction}'"
                
                system_message = {
                    'message': tool_message,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'System'
                }
                
                socketio.emit('message', system_message, broadcast=True)
            
        except Exception as e:
            print(f"Error executing agent chain: {str(e)}")
    
    def _format_agent_response(self, result):
        """
        Format the agent response based on the execution results.
        
        Args:
            result (dict): The agent chain execution result
            
        Returns:
            str: Formatted response message
        """
        # Get the first tool call from action_history if available
        action_history = result.get('action_history', [])
        if action_history and len(action_history) > 0:
            first_action = action_history[0]
            tool_name = first_action.get('tool_name', 'unknown')
            tool_args = first_action.get('tool_args', {})
            
            # Format the tool args as a string
            args_str = ", ".join([f"'{k}': '{v}'" for k, v in tool_args.items()])
            agent_response_message = f"Executing tool: {tool_name} with args: {{{args_str}}}"
            
            # Add tool result information if available
            tool_result = first_action.get('tool_result', {})
            
            # Handle different result types (dict, string, or other)
            if isinstance(tool_result, dict):
                if tool_result.get('success', True):
                    agent_response_message += "\nThe operation was successful."
                else:
                    error = tool_result.get('error', 'unknown error')
                    agent_response_message += f"\nHowever, there was an issue: {error}"
            elif isinstance(tool_result, str):
                # Try to parse the string as JSON
                try:
                    import json
                    json_result = json.loads(tool_result)
                    if isinstance(json_result, dict) and json_result.get('success', True):
                        agent_response_message += "\nThe operation was successful."
                    elif isinstance(json_result, dict):
                        error = json_result.get('error', 'unknown error')
                        agent_response_message += f"\nHowever, there was an issue: {error}"
                    else:
                        # If not a dict with success/error keys, just truncate and display the string
                        if len(tool_result) > 100:
                            agent_response_message += f"\nResult: {tool_result[:100]}..."
                        else:
                            agent_response_message += f"\nResult: {tool_result}"
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, just truncate and display the string
                    if len(tool_result) > 100:
                        agent_response_message += f"\nResult: {tool_result[:100]}..."
                    else:
                        agent_response_message += f"\nResult: {tool_result}"
            else:
                # For other types, convert to string
                agent_response_message += f"\nResult: {str(tool_result)}"
        else:
            # If no action was taken, get the reason
            reason = result.get('reason', "No specific reason was provided.")
            agent_response_message = f"I analyzed your request but determined no action was needed. {reason}"
        
        return agent_response_message
