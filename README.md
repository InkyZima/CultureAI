# CultureAI

## Overview

LoopAgentClaude is an advanced chat application that combines real-time messaging with AI-powered conversational capabilities. Built with Flask, Socket.IO, and Google's Gemini AI, it provides a flexible platform for dynamic persona management, contextual message injection, and tool calling capabilities.

## Project Structure

```
LoopAgentClaude/
├── agent/                 # Agent component for autonomous actions
│   ├── tools/             # Tool implementations
│   ├── agent_chain.py     # Tool execution workflow
│   ├── thinking_agent.py  # Decision-making agent
│   └── placeholder_handler.py # Template processing system
├── chat/                  # Chat processing functionality
│   └── chat.py            # Chat message processing
├── server/                # Server components (after refactoring)
│   ├── config.py          # Server configuration
│   ├── message_manager.py # Message state management
│   ├── command_handler.py # User command processing
│   ├── agent_manager.py   # Agent interaction management
│   └── socket_handlers.py # Socket event handling
├── static/                # Static assets (JS, CSS)
├── templates/             # HTML templates
├── system_prompts/        # System prompts for AI models
├── app.py                 # Main application entry point
└── database.py            # Database interactions
```

## Key Features

### Real-time Chat System
- WebSocket-based messaging
- Support for multiple AI roles (Chat-AI and Agent-AI)
- Direct agent messaging via "@agent" prefix

### LLM Agent with Tool Calling
- Implements Google Gemini function calling interface
- Support for tool registration and execution
- Flexible and extensible framework for adding new tools
- Includes read_file tool implementation with proper error handling
- Mock mode for testing without API keys

### Persona Management
- Dynamic persona switching via "/persona" commands
- Multiple pre-defined personas:
  * Conversationalist
  * Joker
  * Default Elementarist
- Extensible system for adding new personas

### Injection System
- Database-backed injection tracking
- Custom instruction/context injection
- Prevents repeated use of injections
- Supports both database and in-memory tracking

### Database Management
- SQLite database with:
  * messages table
  * injections table
  * agent_calls table
- Automatic table creation
- Message persistence and retrieval

## Modular Architecture

The application has been refactored into a modular architecture:

### Server Module
- **MessageManager**: Handles database interactions and in-memory state
- **CommandHandler**: Processes special user commands
- **AgentManager**: Manages agent interactions and execution
- **SocketHandlers**: Handles WebSocket events
- **Config**: Maintains server configuration

### Agent Module
- **ThinkingAgent**: Makes decisions about tool usage
- **AgentChain**: Coordinates tool execution workflow
- **PlaceholderHandler**: Processes dynamic templates
- **ToolsRegistry**: Manages available tools

### Chat Module
- **ChatProcessor**: Handles message processing with Gemini AI

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create .env file:
```bash
GOOGLE_API_KEY="your-api-key"
DEFAULT_MODEL="gemini-2.0-flash-thinking-exp"
```

3. Run the application:
```bash
python app.py
```

4. Test the LLM agent's tool calling:
```bash
python test_llm_agent.py
```

## API Documentation

### WebSocket Endpoints
- `/connect`: Handle new client connections
- `/message`: Process incoming messages
- `/disconnect`: Handle client disconnections

### LLM Agent Interface
- `agent.process_message(prompt)`: Process a message and execute any tool calls
- Returns a dictionary with:
  - `response`: Text response from the LLM
  - `tool_used`: Name of the tool used (if any)
  - `tool_args`: Arguments passed to the tool (if a tool was used)
  - `tool_result`: Result from the tool execution (if a tool was used)

### Tool Registry
- `tools_registry.get_tool(name)`: Get a tool function by name
- `tools_registry.register_tool(name, func, spec)`: Register a new tool
- `tools_registry.get_all_tool_specs()`: Get all tool specifications

### Persona Commands
- `/persona conversationalist`: Switch to conversationalist persona
- `/persona joker`: Switch to joker persona
- `/persona default`: Switch to default persona

## Database Schema

### messages Table
| Column     | Type        | Description                     |
|------------|-------------|---------------------------------|
| id         | INTEGER     | Primary key                     |
| message    | TEXT        | Message content                 |
| timestamp  | TEXT        | ISO-formatted timestamp         |
| role       | TEXT        | Sender role (User, System, etc.)|
| created_at | TEXT        | Database insertion timestamp    |

### injections Table
| Column     | Type        | Description                     |
|------------|-------------|---------------------------------|
| id         | INTEGER     | Primary key                     |
| role       | TEXT        | Injection source                |
| timestamp  | TEXT        | Creation timestamp              |
| injection  | TEXT        | Injection content               |
| consumed   | INTEGER     | Consumption status (0/1)        |

### agent_calls Table
| Column            | Type        | Description                    |
|-------------------|-------------|--------------------------------|
| id                | INTEGER     | Primary key                    |
| timestamp         | TEXT        | Call timestamp                 |
| model             | TEXT        | Model used                     |
| prompt            | TEXT        | Input prompt                   |
| response          | TEXT        | Model response                 |
| function_called   | TEXT        | Tool name if called            |
| function_args     | TEXT        | Tool arguments (JSON)          |
| function_response | TEXT        | Tool execution result          |
| error             | TEXT        | Error if occurred              |
| latency_ms        | INTEGER     | Execution time in milliseconds |

## Contribution Guidelines

1. Fork the repository
2. Create a new branch for your feature
3. Write clear, well-documented code
4. Add tests for new functionality
5. Submit a pull request with detailed description

## Future Development

- Complete refactoring of app.py into the server module
- Add more sophisticated tools
- Implement advanced error handling
- Enhance the UI with interactive elements
- Add user authentication system
- Create a proper deployment pipeline
