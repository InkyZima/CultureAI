from google import genai
from google.genai.types import Tool, GenerateContentConfig, FunctionDeclaration
import os
import json
import re
import time
import datetime
from google import genai
from google.generativeai import types
from .tools.tools_registry import tools_registry

# Import the database
try:
    from database import MessageDatabase
    db = MessageDatabase()
except ImportError:
    # When running from a test script in a different directory
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import MessageDatabase
    db = MessageDatabase()

class LLMAgent:
    """
    LLM Agent that can process messages and execute tool calls using Google's Generative AI.
    """
    
    def __init__(self, use_mock_for_testing=True):
        """
        Initialize the LLM agent with the Google Generative AI client.
        
        Args:
            use_mock_for_testing (bool): If True, a mock response will be used if the API key is missing
        """
        # Initialize Google Generative AI client
        api_key = os.getenv("GOOGLE_API_KEY")
        self.use_mock = use_mock_for_testing and not api_key
        
        if not api_key and not self.use_mock:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        if not self.use_mock:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.0-flash-001"  # Using a Gemini model that supports tool calling
        
        # Get tool specs from the registry
        self.tool_specs = tools_registry.get_all_tool_specs()
    
    def _log_api_call(self, model, prompt, response=None, function_called=None, function_args=None, function_response=None, error=None, start_time=None, end_time=None):
        """
        Log a Gemini API call to the database.
        
        Args:
            model (str): The model used for the call
            prompt (str or dict): The prompt sent to the model
            response (obj, optional): The response received from the model
            function_called (str, optional): Name of the function called
            function_args (dict, optional): Arguments passed to the function
            function_response (dict, optional): Response from the function
            error (str, optional): Any error that occurred
            start_time (float, optional): Start time of the call (time.time())
            end_time (float, optional): End time of the call (time.time())
        """
        # Calculate latency if start and end times are provided
        latency_ms = None
        if start_time and end_time:
            latency_ms = int((end_time - start_time) * 1000)  # Convert to milliseconds
        
        # Create ISO timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Convert prompt to string if it's not already
        if isinstance(prompt, dict) or not isinstance(prompt, str):
            prompt_str = json.dumps(prompt)
        else:
            prompt_str = prompt
            
        # Log the call to the database
        call_data = {
            'timestamp': timestamp,
            'model': model,
            'prompt': prompt_str,
            'response': response,
            'function_called': function_called,
            'function_args': function_args,
            'function_response': function_response,
            'error': error,
            'latency_ms': latency_ms
        }
        
        try:
            db.log_agent_call(call_data)
        except Exception as e:
            print(f"Error logging agent call: {e}")
    
    def process_message(self, message):
        """
        Process a user message and execute any tool calls if needed.
        
        Args:
            message (str): The user's message
            
        Returns:
            dict: Response from the LLM agent, including any tool call results
        """
        # If using mock for testing, check if message contains a path
        if self.use_mock:
            # Extract file path using regex pattern
            file_path_match = re.search(r'(?:^|\s)([a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*)', message)
            if file_path_match:
                file_path = file_path_match.group(1)
                # Get the function from the registry
                tool_func = tools_registry.get_tool("read_file")
                if tool_func:
                    try:
                        start_time = time.time()
                        function_result = tool_func(file_path=file_path)
                        function_response = json.loads(function_result)
                        end_time = time.time()
                        
                        # Log the mock call
                        self._log_api_call(
                            model="mock-model",
                            prompt=message,
                            response="Mock response for testing",
                            function_called="read_file",
                            function_args={"file_path": file_path},
                            function_response=function_response,
                            start_time=start_time,
                            end_time=end_time
                        )
                        
                        return {
                            "response": f"I've read the file at {file_path}.",
                            "tool_used": "read_file",
                            "tool_args": {"file_path": file_path},
                            "tool_result": function_response
                        }
                    except Exception as e:
                        error = str(e)
                        
                        # Log the error
                        self._log_api_call(
                            model="mock-model",
                            prompt=message,
                            error=error
                        )
                        
                        return {
                            "response": f"Error: {error}",
                            "tool_used": None,
                            "error": error
                        }
            
            # Log the failed call
            self._log_api_call(
                model="mock-model",
                prompt=message,
                response="I couldn't find a valid file path in your message."
            )
            
            return {
                "response": "I couldn't find a valid file path in your message.",
                "tool_used": None
            }
        
        try:
            # Convert tool specs to Gemini format
            tools = []
            for spec in self.tool_specs:
                if "function_declarations" in spec:
                    tool = types.Tool(function_declarations=[
                        types.FunctionDeclaration(
                            name=func_decl["name"],
                            description=func_decl["description"],
                            parameters=types.Schema(**func_decl["parameters"])
                        ) for func_decl in spec["function_declarations"]
                    ])
                    tools.append(tool)
            
            # Create user prompt content
            user_prompt_content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=message)]
            )
            
            # Record start time for latency calculation
            start_time = time.time()
            
            # Generate initial response with tool calling enabled
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[user_prompt_content],
                    config=types.GenerateContentConfig(
                        tools=tools,
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(mode='ANY')
                        )
                    )
                )
                
                initial_response_end_time = time.time()
                
                # Log the initial API call
                self._log_api_call(
                    model=self.model,
                    prompt=str(user_prompt_content),
                    response=str(response),
                    start_time=start_time,
                    end_time=initial_response_end_time
                )
            except Exception as e:
                error = str(e)
                end_time = time.time()
                
                # Log the failed API call
                self._log_api_call(
                    model=self.model,
                    prompt=str(user_prompt_content),
                    error=error,
                    start_time=start_time,
                    end_time=end_time
                )
                
                return {
                    "response": f"Error calling Gemini API: {error}",
                    "tool_used": None,
                    "error": error
                }
            
            # Check if there's a function call in the response
            if not hasattr(response, 'function_calls') or not response.function_calls:
                end_time = time.time()
                
                return {
                    "response": response.text,
                    "tool_used": None
                }
            
            # Get the function call
            function_call = response.function_calls[0]
            function_name = function_call.name
            function_args = function_call.function_call.args
            
            # Log the function call details
            self._log_api_call(
                model=self.model,
                prompt=str(user_prompt_content),
                function_called=function_name,
                function_args=function_args
            )
            
            # Get the function from the registry
            tool_func = tools_registry.get_tool(function_name)
            if not tool_func:
                error = f"Function {function_name} not found in registry"
                
                # Log the error
                self._log_api_call(
                    model=self.model,
                    prompt=str(user_prompt_content),
                    function_called=function_name,
                    function_args=function_args,
                    error=error
                )
                
                return {
                    "response": error,
                    "tool_used": None,
                    "error": error
                }
            
            # Execute the function
            function_start_time = time.time()
            try:
                function_result = tool_func(**function_args)
                # Parse the JSON result
                function_response = json.loads(function_result)
                function_end_time = time.time()
                
                # Log the function execution
                self._log_api_call(
                    model=self.model,
                    prompt=f"Function execution: {function_name}",
                    function_called=function_name,
                    function_args=function_args,
                    function_response=function_response,
                    start_time=function_start_time,
                    end_time=function_end_time
                )
            except Exception as e:
                error = str(e)
                function_end_time = time.time()
                function_response = {"error": error}
                
                # Log the function error
                self._log_api_call(
                    model=self.model,
                    prompt=f"Function execution: {function_name}",
                    function_called=function_name,
                    function_args=function_args,
                    error=error,
                    start_time=function_start_time,
                    end_time=function_end_time
                )
            
            # Create function response part
            function_response_part = types.Part.from_function_response(
                name=function_name,
                response=function_response
            )
            function_response_content = types.Content(
                role='tool', 
                parts=[function_response_part]
            )
            
            # Generate final response
            final_start_time = time.time()
            try:
                final_response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        user_prompt_content,
                        response.candidates[0].content,
                        function_response_content
                    ],
                    config=types.GenerateContentConfig(
                        tools=tools
                    )
                )
                final_end_time = time.time()
                
                # Log the final API call
                self._log_api_call(
                    model=self.model,
                    prompt=f"Final response generation with function results for {function_name}",
                    response=str(final_response),
                    function_called=function_name,
                    function_response=function_response,
                    start_time=final_start_time,
                    end_time=final_end_time
                )
            except Exception as e:
                error = str(e)
                final_end_time = time.time()
                
                # Log the error
                self._log_api_call(
                    model=self.model,
                    prompt=f"Final response generation with function results for {function_name}",
                    function_called=function_name,
                    function_response=function_response,
                    error=error,
                    start_time=final_start_time,
                    end_time=final_end_time
                )
                
                return {
                    "response": f"Error generating final response: {error}",
                    "tool_used": function_name,
                    "tool_args": function_args,
                    "tool_result": function_response,
                    "error": error
                }
            
            # Return the result
            return {
                "response": final_response.text,
                "tool_used": function_name,
                "tool_args": function_args,
                "tool_result": function_response
            }
            
        except Exception as e:
            error = str(e)
            
            # Log the overall error
            self._log_api_call(
                model=self.model if not self.use_mock else "mock-model",
                prompt=message,
                error=error
            )
            
            return {
                "response": f"Error: {error}",
                "tool_used": None,
                "error": error
            }


# Legacy function for backward compatibility
def agent_llm_invoke_google(input="You are a helpful assistant.", model="agent-large", role="system", tools=[]):
    """
    Legacy function to invoke the Google Generative AI model.
    This is maintained for backward compatibility.
    
    Args:
        input (str): The input prompt
        model (str): The model to use
        role (str): The role for the message
        tools (list): List of tools to provide to the model
        
    Returns:
        The function call from the model's response, or an empty string if an error occurs
    """
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # add the read_file tool to the tools array
    read_file_tool = Tool(function_declarations=[
        FunctionDeclaration(
            name="read_file",
            description="Reads the contents of a file",
            parameters={
                "file_path": "string"
            }
        )
    ])
    tools.append(read_file_tool)
    
    # Log API call to database
    try:
        db = MessageDatabase()
        timestamp = datetime.datetime.now().isoformat()
        start_time = time.time()
    except Exception as e:
        print(f"Error initializing database for logging: {e}")
        db = None

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=input,
            config=GenerateContentConfig(
                tools=tools
            )
        )
        
        # Log successful API call
        if db:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            function_called = None
            function_args = None
            if hasattr(response.candidates[0].content.parts[-1], 'function_call'):
                function_call = response.candidates[0].content.parts[-1].function_call
                function_called = function_call.name
                function_args = json.dumps(function_call.args)
                
            db.log_agent_call({
                'timestamp': timestamp,
                'model': "gemini-2.0-flash-001",
                'prompt': input,
                'response': str(response),
                'function_called': function_called,
                'function_args': function_args,
                'latency_ms': latency_ms
            })

        if hasattr(response.candidates[0].content.parts[-1], 'function_call'):
            return response.candidates[0].content.parts[-1].function_call
        return ""
        
    except Exception as e:
        # Log failed API call
        if db:
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            db.log_agent_call({
                'timestamp': timestamp,
                'model': "gemini-2.0-flash-001",
                'prompt': input,
                'error': str(e),
                'latency_ms': latency_ms
            })
            
        print("An error occurred when invoking the LLM: %s" % e)
        return ""