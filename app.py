"""
Entry point for the CultureAI application, integrating components from the server package.
"""
import atexit
import datetime
import os
from flask import render_template
from database import MessageDatabase
from chat.chat import ChatProcessor
from server.config import app, socketio, LOCAL_TIMEZONE
from server.message_manager import MessageManager
from server.command_handler import CommandHandler
from server.agent_manager import AgentManager
from server.socket_handlers import SocketHandlers

# Initialize database
db = MessageDatabase()

# Initialize message manager
message_manager = MessageManager(db)

# Initialize chat processor
chat_processor = ChatProcessor(socketio, db)

# Initialize the chat session with conversation history
if message_manager.messages:
    # Create a session based on existing chat history
    # This makes the chat model aware of previous conversations
    session_id = 'default'
    history = []
    
    # Add system prompt as the first interaction
    system_prompt = chat_processor.system_prompt
    history.append({"role": "user", "parts": [system_prompt]})
    history.append({"role": "model", "parts": ["Understood."]})
    
    # Add existing messages to history
    for msg in message_manager.messages:
        role = "user" if msg.get('role') == "User" else "model"
        # Only add user and AI messages to the history (skip system messages)
        if msg.get('role') in ['User', 'Chat-AI']:
            history.append({"role": role, "parts": [msg.get('message')]})
    
    # Initialize chat session with history
    chat_processor.chat_sessions[session_id] = chat_processor.model.start_chat(history=history)
    print(f"Initialized chat session with {len(history) - 2} previous messages") # Subtract 2 for system prompt

# Initialize command handler
command_handler = CommandHandler(message_manager, chat_processor)

# Initialize agent manager
agent_manager = AgentManager(message_manager)

# Create a custom socket handlers class that adds the greeting message
class CustomSocketHandlers(SocketHandlers):
    def handle_connect(self):
        """Handle client connection event with additional welcome message."""
        # Call the parent method first
        super().handle_connect()
        
        # Load and send the Elementarist greeting
        try:
            greeting_path = os.path.join('system_prompts', 'static_texts', 'Elemenarist_greeting.txt')
            with open(greeting_path, 'r', encoding='utf-8') as file:
                elementarist_greeting = file.read().strip()
            
            greeting_message = {
                'message': elementarist_greeting,
                'timestamp': datetime.datetime.now(LOCAL_TIMEZONE).isoformat(),
                'role': 'Chat-AI'
            }
            
            socketio.emit('message', greeting_message, broadcast=True)
        except Exception as e:
            print(f"Error sending greeting: {e}")

# Initialize socket handlers with our custom class
socket_handlers = CustomSocketHandlers(message_manager, chat_processor, command_handler, agent_manager)

@app.route('/')
def index():
    """Render the main index page."""
    return render_template('index.html')

# Register a function to close the database connection when the application exits
def close_db_connection():
    """Close the database connection gracefully."""
    message_manager.close()

atexit.register(close_db_connection)

if __name__ == '__main__':
    try:
        # Run the Flask application
        print("Starting CultureAI application...")
        print("Access the chat interface at http://localhost:5000 or http://<your-ip>:5000")
        
        # Use host='0.0.0.0' to make the app accessible from other devices on the network
        # This is important for Raspberry Pi deployments
        socketio.run(app, debug=True, host='0.0.0.0')
    finally:
        # Close the database connection
        close_db_connection()
