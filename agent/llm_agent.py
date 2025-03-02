import os
import json
import time
import datetime
from typing import Dict, Any, List, Optional

import google.generativeai as genai

# Import database for logging
try:
    from database import MessageDatabase
    db = MessageDatabase()
except ImportError:
    # When running from a test script in a different directory
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import MessageDatabase
    db = MessageDatabase()

# Import tools registry
from .tools.tools_registry import tools_registry

class LLMAgent:
    """
    Agent that processes user messages using Google's Generative AI (Gemini model)
    and executes tool calls based on the model's responses.
    """
    
    def __init__(self):
        """
        Initialize the LLMAgent with Google Generative AI client and tool specifications.
        """
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Configure the Google Generative AI client
        genai.configure(api_key=api_key)
        
        # Get tool specifications from the registry
        self.tools_registry = tools_registry
        self.tool_specs = self.tools_registry.get_all_tool_specs()
        
        # Set the model to use
        self.model_name = "gemini-2.0-flash-001"

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message and generate a response, potentially executing tools.
        
        Args:
            message (str): The user's message
            
        Returns:
            Dict[str, Any]: A dictionary containing the response and any tool execution results
        """
        try:
            # Log this API call
            timestamp = datetime.datetime.now().isoformat()
            start_time = time.time()
            
            # Create a Model instance
            model = genai.GenerativeModel(self.model_name)
            
            # Generate content with tools
            response = model.generate_content(
                contents=message,
                tools=self.tool_specs
            )
            
            # Calculate latency
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Initialize variables
            tool_used = None
            tool_args = None
            tool_result = None
            
            # Check if there's a function call in the response
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content.parts:
                    last_part = candidate.content.parts[-1]
                    if hasattr(last_part, 'function_call'):
                        # Extract function call details
                        function_call = last_part.function_call
                        tool_used = function_call.name
                        tool_args = {}
                        
                        # Convert args to a plain dictionary
                        for key, value in function_call.args.items():
                            tool_args[key] = value
                        
                        # Log the function call
                        self._log_api_call(
                            timestamp=timestamp,
                            prompt=message,
                            response=self._safe_str(response),
                            function_called=tool_used,
                            function_args=json.dumps(tool_args),
                            latency_ms=latency_ms
                        )
                        
                        # Execute the tool
                        result = self._execute_tool(tool_used, tool_args)
                        tool_result = result
                        
                        # Parse the result
                        result_json = json.loads(result)
                        
                        # Create messages for the follow-up request
                        chat = [
                            {"role": "user", "parts": [{"text": message}]},
                            {"role": "model", "parts": [{"function_call": {"name": tool_used, "args": tool_args}}]},
                            {"role": "function", "parts": [{"function_response": {"name": tool_used, "response": result_json}}]}
                        ]
                        
                        # Generate the final response that includes the function result
                        final_response = model.generate_content(chat)
                        
                        # Log the final response
                        self._log_api_call(
                            timestamp=datetime.datetime.now().isoformat(),
                            prompt=f"[Function Result] {result}",
                            response=self._safe_str(final_response),
                            function_response=result,
                            latency_ms=int((time.time() - end_time) * 1000)
                        )
                        
                        # Return the result
                        return {
                            "response": final_response.text,
                            "tool_used": tool_used,
                            "tool_args": tool_args,
                            "tool_result": tool_result
                        }
            
            # No function calls, just return the response text
            self._log_api_call(
                timestamp=timestamp,
                prompt=message,
                response=self._safe_str(response),
                latency_ms=latency_ms
            )
            
            return {
                "response": response.text
            }
                
        except Exception as e:
            # Log the error
            error_message = f"Error processing message: {str(e)}"
            print(f"Error: {error_message}")
            import traceback
            print(traceback.format_exc())
            
            self._log_api_call(
                timestamp=datetime.datetime.now().isoformat(),
                prompt=message,
                error=error_message,
                latency_ms=0
            )
            
            return {
                "response": "I'm sorry, but I encountered an error processing your message.",
                "error": error_message
            }
    
    def _safe_str(self, obj: Any) -> str:
        """
        Safely convert an object to string, handling non-serializable objects.
        
        Args:
            obj (Any): The object to convert
            
        Returns:
            str: String representation of the object
        """
        try:
            return str(obj)
        except Exception:
            return "Object could not be converted to string"
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name (str): The name of the tool to execute
            tool_args (Dict[str, Any]): The arguments for the tool
            
        Returns:
            str: The result of the tool execution as a JSON string
        """
        try:
            # Look up the tool in the registry
            tool_function = self.tools_registry.get_tool(tool_name)
            
            if not tool_function:
                return json.dumps({
                    "error": f"Tool not found: {tool_name}"
                })
            
            # Execute the tool
            result = tool_function(**tool_args)
            return result
            
        except Exception as e:
            return json.dumps({
                "error": f"Error executing tool {tool_name}: {str(e)}"
            })
    
    def _log_api_call(self, timestamp: str, prompt: str, response: Optional[str] = None,
                     function_called: Optional[str] = None, function_args: Optional[str] = None,
                     function_response: Optional[str] = None, error: Optional[str] = None,
                     latency_ms: int = 0) -> None:
        """
        Log an API call to the database.
        
        Args:
            timestamp (str): ISO-formatted timestamp
            prompt (str): The prompt sent to the model
            response (str, optional): The response from the model
            function_called (str, optional): The name of the function called
            function_args (str, optional): The arguments for the function call
            function_response (str, optional): The response from the function
            error (str, optional): Any error that occurred
            latency_ms (int): The latency in milliseconds
        """
        try:
            # Log to the database
            db.log_agent_call({
                'timestamp': timestamp,
                'model': self.model_name,
                'prompt': prompt,
                'response': response,
                'function_called': function_called,
                'function_args': function_args,
                'function_response': function_response,
                'error': error,
                'latency_ms': latency_ms
            })
        except Exception as e:
            print(f"Error logging API call: {str(e)}")