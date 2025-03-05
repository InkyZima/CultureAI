"""
Test the Google Generative AI API with tools
"""
import os
import sys
import json

try:
    # Try to import the official SDK first
    import google.generativeai as genai
    print("Using official Google Generative AI SDK in tests")
except ImportError:
    # Fall back to our custom wrapper for Python 3.7
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from chat.gemini_wrapper import GeminiModule as genai
    print("Using custom Gemini wrapper for Python 3.7 compatibility in tests")

from dotenv import load_dotenv
import inspect

# Load environment variables
load_dotenv()

# API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not found")

# Configure the generative AI
genai.configure(api_key=api_key)

# Check version
print(f"Google Generative AI version: {genai.__version__}")

# Show available methods and attributes
print("\nAvailable methods in genai module:")
for item in dir(genai):
    if not item.startswith('_'):
        print(f"  {item}")

# Try to get model configuration
print("\nModel availability:")
try:
    models = genai.list_models()
    for model in models:
        print(f"  {model.name}")
        if hasattr(model, 'supported_methods'):
            print(f"    Supported methods: {model.supported_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

# Print GenerativeModel methods
print("\nGenerativeModel methods:")
for name, method in inspect.getmembers(genai.GenerativeModel, predicate=inspect.isfunction):
    if not name.startswith('_'):
        print(f"  {name}")
        if hasattr(method, '__doc__') and method.__doc__:
            print(f"    Doc: {method.__doc__.strip()[:100]}...")

# Define a simple tool
read_file_tool = {
    "function_schema": {
        "name": "read_file",
        "description": "Read file contents",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Try another format
read_file_tool_alt = {
    "name": "read_file",
    "description": "Read file contents",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            }
        },
        "required": ["file_path"]
    }
}

# Try a third format
read_file_tool_alt2 = {
    "function": {
        "name": "read_file",
        "description": "Read file contents",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file"
                }
            },
            "required": ["file_path"]
        }
    }
}

# Trying Google's older documentation format
schema_for_older_version = {
    "schema_version": "v2",
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the file"
        }
    },
    "required": ["file_path"]
}

# Try the simplest schema
simplest_schema = {
    "schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string"
            }
        },
        "required": ["file_path"]
    }
}

# Try a direct call without tool syntax
print("\nTrying a simple call without tools...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "What's the capital of France?"
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

# Try each tool format
print("\nTrying first tool format...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "Please read the file at C:\\example.txt",
        tools=[read_file_tool]
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTrying second tool format...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "Please read the file at C:\\example.txt",
        tools=[read_file_tool_alt]
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTrying third tool format...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "Please read the file at C:\\example.txt",
        tools=[read_file_tool_alt2]
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTrying older documentation format...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "Please read the file at C:\\example.txt",
        tools=[{"schema": schema_for_older_version}]
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

print("\nTrying simplest schema...")
try:
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        "Please read the file at C:\\example.txt",
        tools=[simplest_schema]
    )
    print("Success!")
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")

# Let's try to print the parameter requirements for tools
print("\nChecking tool parameter requirements:")
try:
    from inspect import signature
    sig = signature(model.generate_content)
    for param_name, param in sig.parameters.items():
        if param_name == "tools":
            print(f"Parameter 'tools' type annotation: {param.annotation}")
            break
    print("Attempting to get method docstring:")
    print(model.generate_content.__doc__)
except Exception as e:
    print(f"Error getting tool parameter info: {e}")

# Print tool calls if any
def detect_tool_calls(response):
    try:
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            print(f"Function call detected: {part.function_call}")
                            return True
    except:
        pass
    return False
