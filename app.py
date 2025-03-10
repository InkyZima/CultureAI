import datetime
import atexit
from flask import Flask, render_template
from flask_socketio import SocketIO
from database import MessageDatabase
from agent import MessageAgent
from chat import ChatProcessor, default_model

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-s!e43gmt-key'
socketio = SocketIO(app)

# Create an instance of the MessageDatabase
db = MessageDatabase()
# Delete all messages and injections from the database when app starts
db.delete_all_messages()
db.delete_all_injections()

# Create a messages array to store chat history
messages = []

# Create a injections array to store text to be injected into the conversation between Chat-AI and user
injections = []

# Create an instance of the MessageAgent with the database
agent = MessageAgent(socketio, db)
agent.start()

# Create an instance of the ChatProcessor with SocketIO and database
chat_processor = ChatProcessor(socketio, db)

@app.route('/')
def index():
    return render_template('index.html')

def process_persona_command(data, command, persona_file):
    """Handle persona change commands by loading content from specified file.
    
    Args:
        data (dict): The message data
        command (str): The command string to check for
        persona_file (str): Path to the persona file
        
    Returns:
        bool: True if command was processed, False otherwise
    """
    if data.get('role') == 'User' and command in data.get('message', ''):
        try:
            # Read the content of the persona file
            with open(persona_file, 'r', encoding='utf-8') as f:
                persona_content = f.read()
            
            # Get persona name from command (remove '/persona ' prefix)
            persona_name = command.replace('/persona ', '')
            
            # Create injection object
            injection = {
                'injection': persona_content,
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'User',
                'consumed': False
            }
            
            # Add to injections array
            injections.append(injection)
            
            # Save to the database
            db.save_injection(injection)
            
            # Inform the user
            system_message = {
                'message': f'Persona changed to: {persona_name.capitalize()}',
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'System'
            }
            socketio.emit('message', system_message)
            return True
            
        except Exception as e:
            print(f"Error loading {persona_file} persona: {e}")
            system_message = {
                'message': f'Error changing persona: {str(e)}',
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'System'
            }
            socketio.emit('message', system_message)
            return True
    
    return False

def handle_user_commands(data):
    """Process special user commands.
    
    Args:
        data (dict): The message data
        
    Returns:
        bool: True if a command was processed, False otherwise
    """
    # Check for persona change commands
    if process_persona_command(data, '/persona conversationalist', 'system_prompts/conversationalist.txt'):
        return True
    
    # Check for persona change to joker
    if process_persona_command(data, '/persona joker', 'system_prompts/joker.txt'):
        return True

    # Check for persona change to joker
    if process_persona_command(data, '/persona default', 'system_prompts/system_prompt.txt'):
        return True
    
    
    # Add more command handlers here in the future
    
    return False  # No commands were processed

@socketio.on('message')
def handle_message(data):
    # Save the message to the database
    db.save_message(data)
    
    # Add the message to the messages array
    messages.append(data)
    
    # Check for and handle special commands such as persona switches
    if handle_user_commands(data):
        return
    
    """
    The Chat-AI has the objective or quickly replying to the user. The Agent-AI has the objective or evaluating the Chat-AI's performance and giving corrective suggestions. Therefore the Chat-AI shall be informed whenever there is a new user message, whereas the Agent-AI shall be informed whenever there is a new Chat-AI message.
    An exception to this rule is when the user specifically wishes to inform only the Agent directly. The user can do so by prefixing their message with "@agent"
    """
    talkToAgent = True if "@agent" in data.get('message') else False
    if data.get('role') == 'User' and not talkToAgent:
        # Process the message with ChatProcessor, passing the entire message history
        # and the injections array
        chat_processor.process_message(data, messages, injections)
    elif data.get('role') == 'Chat-AI' or talkToAgent:
        # Inform the agent about the chat-AI's response, passing the entire message history
        agent.receive_user_message(data, messages)
    
    # Broadcast the message to all clients except the sender
    socketio.emit('message', data, broadcast=True, include_self=False)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    
    # Create system message for new user
    system_message = {
        'message': f'You are talking to: {chat_processor.default_model}.',
        'timestamp': datetime.datetime.now().isoformat(),
        'role': 'System'
    }
    
    # Don't save the system message to the database
    # db.save_message(system_message)
    
    socketio.emit('message', system_message, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
    # Create system message for user disconnection
    system_message = {
        'message': 'A user has left the chat',
        'timestamp': datetime.datetime.now().isoformat(),
        'role': 'System'
    }
    
    # Don't save the system message to the database
    # db.save_message(system_message)
    
    socketio.emit('message', system_message, broadcast=True)

# Register a function to close the database connection when the application exits
def close_db_connection():
    if db:
        db.close()

atexit.register(close_db_connection)

if __name__ == '__main__':
    try:
        # Run the Flask application
        socketio.run(app, debug=True)
    finally:
        # Ensure the agent is stopped when the app exits
        agent.stop()
        # Close the database connection
        close_db_connection()
