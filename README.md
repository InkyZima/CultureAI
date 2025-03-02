# LoopAgentClaude Chat Application

## Overview

LoopAgentClaude is an advanced chat application that combines real-time messaging with AI-powered conversational capabilities. Built with Flask, Socket.IO, and Google's Gemini AI, it provides a flexible platform for dynamic persona management and contextual message injection.

## Key Features

### Real-time Chat System
- WebSocket-based messaging
- Support for multiple AI roles (Chat-AI and Agent-AI)
- Direct agent messaging via "@agent" prefix

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
- Automatic table creation
- Message persistence and retrieval

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

## API Documentation

### WebSocket Endpoints
- `/connect`: Handle new client connections
- `/message`: Process incoming messages
- `/disconnect`: Handle client disconnections

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

## Contribution Guidelines

1. Fork the repository
2. Create a new branch for your feature
3. Write clear, well-documented code
4. Add tests for new functionality
5. Submit a pull request with detailed description

## Security Notes

- API keys stored in .env file
- Basic input sanitization
- No advanced authentication implemented
