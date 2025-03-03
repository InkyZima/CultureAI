# Agent Component Documentation

## Overview

The Agent component is a central part of the LoopAgentClaude application, providing an autonomous reasoning layer that can analyze conversations and take action when appropriate. It uses Google's Generative AI (specifically the Gemini model) to make decisions about when and how to intervene in conversations.

## Architecture

The Agent is comprised of several key components:

### ThinkingAgent (`thinking_agent.py`)

The ThinkingAgent is responsible for decision-making about tool execution:

- Sends conversations to the Gemini model for analysis
- Receives a textual decision from the model about which tools to use
- Uses a specialized prompt template to guide the model's thinking
- Supports customization via different prompt templates

### AgentChain (`agent_chain.py`)

The AgentChain coordinates the execution of thinking and tool calling:

1. Uses ThinkingAgent to decide if a tool should be used
2. Parses the decision text to extract tool name and arguments
3. Executes the tool if needed
4. Loops back to ThinkingAgent with the results for further decisions
5. Limits iterations to prevent infinite loops

### PlaceholderHandler (`placeholder_handler.py`)

Provides dynamic template processing functionality:

- Supports placeholders like `{timestamp}`, `{chat_history}`, `{unconsumed_injections}`
- Allows for consistent formatting and context insertion
- Extensible architecture for adding new placeholder types

### Tools Registry (`tools/tools_registry.py`)

Manages the available tools that can be called by the Agent:

- Centralized registry for all tool functions
- Each tool has specifications describing parameters and functionality
- Current tools include:
  - `inject_instruction`: Insert instructions for the Chat-AI
  - `send_notification`: Send a notification to the user
  - `read_file`: Read file contents (with security restrictions)
  - `DANGER_write_file`: Write to a file (with security restrictions)

## Tool Execution Flow

1. **Decision Phase**: ThinkingAgent analyzes conversation context
2. **Parsing Phase**: AgentChain extracts tool directives from decision
3. **Execution Phase**: Tool is retrieved from registry and executed with args
4. **Feedback Phase**: Results are passed back to ThinkingAgent
5. **Loop or Complete**: Either continue with a new decision or return final result

## Key Features

- **Autonomous reasoning**: Makes independent decisions about tool usage
- **Natural language tool selection**: Uses reasoning rather than pattern-matching
- **Iterative execution**: Can perform multiple related actions to solve complex tasks
- **Comprehensive logging**: Records all decisions and actions for debugging
- **Decision history tracking**: Maintains context across iterations
- **Flexible templating**: Supports dynamic prompts with placeholder system

## Usage

The Agent is typically used through the `AgentChain` class:

```python
# Initialize the agent chain
agent_chain = AgentChain(db=database)

# Execute with a specific prompt
result = agent_chain.execute(custom_prompt="Analyze this conversation...")

# Check if action was taken
if result["action_taken"]:
    tool_used = result["tool_used"]
    tool_result = result["tool_result"]
else:
    reason = result["reason"]
```

## Future Improvements

- Add more sophisticated tools
- Implement memory mechanisms for long-term context
- Improve decision parsing with more flexible patterns
- Add support for parallel tool execution
