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

## Setup Instructions

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python app.py
```

3. Open your browser and navigate to `http://127.0.0.1:5000/` to use the chat application.

## How It Works

- The frontend connects to the backend via Socket.IO (WebSocket)
- Messages are sent from the client to the server and then broadcast to all other connected clients
- The UI updates in real-time without page refreshes
- An AI agent automatically sends messages every 5 seconds
- All messages (user, system, and agent) are stored in an SQLite database
- Messages include the content, timestamp, and role of the sender

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
