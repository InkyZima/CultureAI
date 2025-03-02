"""
Legacy module that contains backward-compatible functions for older code that 
might still be referencing the original API.
"""
import os
import json
import time
import datetime
from google import genai
from google.genai.types import Tool, GenerateContentConfig, FunctionDeclaration

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
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_API_KEY environment variable is not set")
        return ""
        
    client = genai.Client(api_key=api_key)

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
        timestamp = datetime.datetime.now().isoformat()
        start_time = time.time()
    except Exception as e:
        print(f"Error initializing database for logging: {e}")
        timestamp = None
        start_time = None

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=input,
            config=GenerateContentConfig(
                tools=tools
            )
        )
        
        # Log successful API call
        if db and timestamp and start_time:
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
        if db and timestamp and start_time:
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
