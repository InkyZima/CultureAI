# LLM Agent Documentation

## Overview

The `LLMAgent` class is a central component of the system that processes user messages using Google's Generative AI (specifically the Gemini model) and executes tool calls based on the model's responses. It serves as an interface between the user, the AI model, and various tools or functions that can be executed based on the AI's recommendations.

## Core Functionality

The agent's primary capabilities include:

1. Processing natural language messages from users
2. Using Google's Gemini API to generate responses
3. Detecting and executing tool calls recommended by the AI model
4. Handling function execution results and generating final responses
5. Comprehensive logging of all interactions for debugging and analytics

## Architecture

### Initialization

The `LLMAgent` is initialized with the following components:

- Google Generative AI client (using the Gemini model)
- Tool specifications retrieved from a registry

### Main Components

#### Tool Registry

The agent uses a registry (`tools_registry`) that contains all available tools and their specifications. Each tool has:
- A name
- A function implementation
- A specification that describes its parameters and functionality

Currently, the registry includes tools for:
- Reading files (`read_file`)
- Injecting instructions (`inject_instruction`)
- Sending notifications (`send_notification`)

#### Message Processing Flow

1. **Process Message**: The main entry point `process_message` takes a user message and processes it.
2. **Model Interaction**: The agent sends the message to the Gemini model with tool specifications.
3. **Function Detection**: If the model recommends a function call, the agent extracts the function name and arguments.
4. **Function Execution**: The agent looks up the function in the registry and executes it with the provided arguments.
5. **Response Generation**: The agent sends the function execution results back to the model to generate a final response.
6. **Result Return**: A structured response containing the LLM's answer and any tool execution results is returned.

#### Error Handling

Robust error handling is implemented throughout the process:
- API call errors
- Function lookup errors
- Function execution errors
- Response generation errors

All errors are logged and returned in a structured format.

#### Logging

The agent implements comprehensive logging via the `_log_api_call` method which records:
- Timestamps
- Model information
- Prompts and responses
- Function calls and their arguments
- Function execution results
- Any errors
- Latency measurements

Logs are stored in a database via the `MessageDatabase` class.


## Usage

The agent is typically used as follows:

```python
# Initialize the agent
agent = LLMAgent()

# Process a user message
result = agent.process_message("Can you read the file at C:\\path\\to\\file.txt?")

# Use the result
response_text = result["response"]
tool_used = result["tool_used"]
tool_result = result.get("tool_result")
```

## Technical Details

- Uses Google's Gemini 2.0 Flash model (`gemini-2.0-flash-001`)
- Tool specifications follow Google's Generative AI API format
- All function results are expected to be JSON strings
- The API key is retrieved from the `GOOGLE_API_KEY` environment variable