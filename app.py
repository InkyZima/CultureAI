# git push cultureai-remote master:main

import datetime
import atexit
from flask import Flask, render_template
from flask_socketio import SocketIO
from database import MessageDatabase
from chat import ChatProcessor, default_model
from agent.agent_chain import AgentChain

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-s!e43gmt-key'
socketio = SocketIO(app)

# Create an instance of the MessageDatabase
db = MessageDatabase()
# Delete all messages and injections from the database when app starts
# db.delete_all_messages()
# db.delete_all_injections()

# Create a messages array to store chat history
messages = []

# Create a injections array to store text to be injected into the conversation between Chat-AI and user
injections = []

# User message counter to track when to run the agent chain
user_message_counter = 0

# Load existing messages and injections from the database
def load_data_from_database():
    """Load existing messages and injections from the database into memory"""
    global messages, injections
    
    # Load messages
    db_messages = db.get_messages(limit=100)  # Limit to last 100 messages
    if db_messages:
        # Reverse to get chronological order (oldest first)
        db_messages.reverse()
        
        # Format as needed for the messages array
        for msg in db_messages:
            message_obj = {
                'message': msg['message'],
                'timestamp': msg['timestamp'],
                'role': msg['role']
            }
            messages.append(message_obj)
        print(f"Loaded {len(messages)} messages from database")
    
    # Load injections
    db_injections = db.get_injections(consumed=False)  # Get only unconsumed injections
    if db_injections:
        # Add to injections array
        for inj in db_injections:
            injection_obj = {
                'injection': inj['injection'],
                'timestamp': inj['timestamp'],
                'role': inj['role'],
                'consumed': inj['consumed']
            }
            injections.append(injection_obj)
        print(f"Loaded {len(injections)} active injections from database")

# Load data when app starts
load_data_from_database()


# Create an instance of the ChatProcessor with SocketIO and database
chat_processor = ChatProcessor(socketio, db)

# Initialize the chat session with conversation history
if messages:
    # Create a session based on existing chat history
    # This makes the chat model aware of previous conversations
    session_id = 'default'
    history = []
    
    # Add system prompt as the first interaction
    system_prompt = chat_processor.system_prompt
    history.append({"role": "user", "parts": [system_prompt]})
    history.append({"role": "model", "parts": ["Understood."]})
    
    # Add existing messages to history
    for msg in messages:
        role = "user" if msg.get('role') == "User" else "model"
        # Only add user and AI messages to the history (skip system messages)
        if msg.get('role') in ['User', 'Chat-AI']:
            history.append({"role": role, "parts": [msg.get('message')]})
    
    # Initialize chat session with history
    chat_processor.chat_sessions[session_id] = chat_processor.model.start_chat(history=history)
    print(f"Initialized chat session with {len(history) - 2} previous messages") # Subtract 2 for system prompt

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
    
    # Check for the delete command
    if data.get('role') == 'User' and '/delete' in data.get('message', ''):
        try:
            # Delete all messages and injections
            db.delete_all_messages()
            db.delete_all_injections()
            db.delete_all_agent_calls()
            
            # Also clear the in-memory arrays
            messages.clear()
            injections.clear()
            
            # Inform the user
            system_message = {
                'message': 'All messages and injections have been deleted.',
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'System'
            }
            socketio.emit('message', system_message)
            return True
            
        except Exception as e:
            print(f"Error processing delete command: {e}")
            system_message = {
                'message': f'Error deleting messages and injections: {str(e)}',
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'System'
            }
            socketio.emit('message', system_message)
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
    
    # Execute agent chain every third user message
    global user_message_counter
    execute_agent_chain = False
    
    if data.get('role') == 'User':
        user_message_counter += 1
        if user_message_counter % 3 == 0:
            execute_agent_chain = True
            print(f"Third user message detected (#{user_message_counter}). Executing agent chain...")
    
    if data.get('role') == 'User' and not talkToAgent:
        # Process the message with ChatProcessor, passing the entire message history
        # and the injections array
        chat_processor.process_message(data, messages, injections)
        
        # Execute the agent chain every third message
        if execute_agent_chain:
            try:
                # Initialize and execute the agent chain
                agent_chain = AgentChain()
                
                # Create a custom prompt based on the current conversation state
                custom_prompt = f"""
                Current time: {datetime.datetime.now().isoformat()}
                The user has sent their {user_message_counter}th message.
                Last message from user: "{data.get('message')}"
                
                Analyze the conversation and decide if any tools should be used to help the user with their cultural practices.
                """
                
                result = agent_chain.execute(custom_prompt)
                
                # Log the agent chain execution
                print(f"Agent Chain Execution Results:")
                print(f"Action taken: {result.get('action_taken', False)}")
                
                if result.get('action_taken', False):
                    tool_used = result.get('tool_used', 'unknown')
                    print(f"Tool used: {tool_used}")
                    
                    # Add a system message about the agent's action
                    tool_message = "I notice you might need assistance. "
                    
                    if tool_used == "send_notification":
                        notification = result.get('tool_args', {}).get('message', '')
                        tool_message += f"I've sent you a notification: '{notification}'"
                    elif tool_used == "inject_instruction":
                        instruction = result.get('tool_args', {}).get('instruction', '')
                        tool_message += f"I'll be providing this guidance soon: '{instruction}'"
                    
                    system_message = {
                        'message': tool_message,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'role': 'System'
                    }
                    
                    socketio.emit('message', system_message, broadcast=True)
                
            except Exception as e:
                print(f"Error executing agent chain: {str(e)}")
            
    elif data.get('role') == 'Chat-AI' or talkToAgent:
        # Inform the agent about the chat-AI's response, passing the entire message history
        # agent.receive_user_message(data, messages)
        print("Calling agent only.")
    
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
        # Close the database connection
        close_db_connection()
