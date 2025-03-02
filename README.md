# Simple Chat Application

A simple chat application with an HTML frontend and a Flask backend that communicates via WebSockets.

## Features

- Real-time messaging using WebSockets
- Simple and clean user interface
- Responsive design
- Notifications when users join or leave
- Automatic messages from an AI agent every 5 seconds
- SQLite database for message persistence
- Message logging with timestamp and role information
- Google Gemini AI integration for intelligent responses

## Setup Instructions

1. Install the required packages:

```bash
pip install -r requirements.txt
pip install google-generativeai==0.3.1 python-dotenv==1.0.0
```

2. Create a `.env` file in the root directory with your Google API credentials:

```bash
GOOGLE_API_KEY="your-google-api-key"
DEFAULT_MODEL="gemini-2.0-flash-thinking-exp"  # or another Gemini model
```

3. Run the application:

```bash
python app.py
```

4. Open your browser and navigate to `http://127.0.0.1:5000/` to use the chat application.

## How It Works

- The frontend connects to the backend via Socket.IO (WebSocket)
- Messages are sent from the client to the server and then broadcast to all other connected clients
- The UI updates in real-time without page refreshes
- An AI agent automatically sends messages every 5 seconds
- All messages (user, system, and agent) are stored in an SQLite database
- Messages include the content, timestamp, and role of the sender
- Google Gemini AI integration provides intelligent responses to user messages

## New Feature: Google Gemini AI Integration

This chat application now integrates with Google's Gemini AI model to provide intelligent responses to user messages!

### How it works:
1. User sends a message through the chat interface
2. The message is sent to Google's Gemini AI model
3. The AI generates a thoughtful response
4. The response is sent back to all connected clients in real-time

### Setup:
1. Create a `.env` file in the root directory with your Google API credentials:
   ```
   GOOGLE_API_KEY="your-google-api-key"
   DEFAULT_MODEL="gemini-2.0-flash-thinking-exp"  # or another Gemini model
   ```
2. Install the additional requirements:
   ```
   pip install google-generativeai==0.3.1 python-dotenv==1.0.0
   ```

### Note:
- The `.env` file is included in `.gitignore` to prevent accidentally committing your API key
- You can change the model by updating the `DEFAULT_MODEL` variable in your `.env` file
- Chat history is maintained for each session to provide context-aware responses

## Database Structure

The application uses an SQLite database (`messages.db`) to store all messages. The database contains a single table:

- **messages**: Stores all chat messages with the following fields:
  - `id`: Unique identifier for each message (auto-incrementing integer)
  - `message`: The actual message content
  - `timestamp`: ISO-formatted timestamp of when the message was sent
  - `role`: The role of the sender (User, System, Agent-AI, etc.)
  - `created_at`: Timestamp of when the message was added to the database

## Technologies Used

- Frontend: HTML, CSS, JavaScript, Socket.IO client
- Backend: Python, Flask, Flask-SocketIO
- Database: SQLite
- AI Integration: Google Gemini AI
