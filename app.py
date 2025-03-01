from flask import Flask, render_template
from flask_socketio import SocketIO
import datetime
import atexit
from agent import MessageAgent  # Import the MessageAgent class
from database import MessageDatabase  # Import the MessageDatabase class
from chat import ChatProcessor  # Import the ChatProcessor class

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-s!e43gmt-key'
socketio = SocketIO(app)

# Create an instance of the MessageDatabase
db = MessageDatabase()

# Create an instance of the MessageAgent with the database
agent = MessageAgent(socketio, db)

# Create an instance of the ChatProcessor
chat_processor = ChatProcessor(socketio, db)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    # Log the received message
    print(f'Received message: {data}')
    
    # Save the message to the database
    db.save_message(data)
    
    # Process the message if it's from a user
    if data.get('role') == 'User':
        # Inform the agent about the user message
        agent.receive_user_message(data)
        
        # Process the message with ChatProcessor (transform to all caps)
        chat_processor.process_message(data)
    
    # Broadcast the message to all clients except the sender
    socketio.emit('message', data, broadcast=True, include_self=False)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    
    # Create system message for new user
    system_message = {
        'message': 'A new user has joined the chat',
        'timestamp': datetime.datetime.now().isoformat(),
        'role': 'System'
    }
    
    # Save the system message to the database
    db.save_message(system_message)
    
    socketio.emit('message', system_message, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
    # Create system message for user leaving
    system_message = {
        'message': 'A user has left the chat',
        'timestamp': datetime.datetime.now().isoformat(),
        'role': 'System'
    }
    
    # Save the system message to the database
    db.save_message(system_message)
    
    socketio.emit('message', system_message, broadcast=True)

# Register a function to close the database connection when the application exits
def close_db_connection():
    if db:
        db.close()

atexit.register(close_db_connection)

if __name__ == '__main__':
    # Start the agent before running the app
    agent.start()
    
    try:
        # Run the Flask application
        socketio.run(app, debug=True)
    finally:
        # Ensure the agent is stopped when the app exits
        agent.stop()
        # Close the database connection
        close_db_connection()
