"""
SocketIO event handlers for the chat application.
"""
import datetime
from server.config import socketio

class SocketHandlers:
    """
    Manages SocketIO event handlers for the chat application.
    """
    
    def __init__(self, message_manager, chat_processor, command_handler, agent_manager):
        """
        Initialize socket handlers.
        
        Args:
            message_manager: Message manager instance
            chat_processor: Chat processor instance
            command_handler: Command handler instance
            agent_manager: Agent manager instance
        """
        self.message_manager = message_manager
        self.chat_processor = chat_processor
        self.command_handler = command_handler
        self.agent_manager = agent_manager
        
        # Register socket handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all SocketIO event handlers."""
        socketio.on('connect')(self.handle_connect)
        socketio.on('disconnect')(self.handle_disconnect)
        socketio.on('message')(self.handle_message)
    
    def handle_connect(self):
        """Handle client connection event."""
        print('Client connected')
        
        # Create system message for new user
        system_message = {
            'message': f'You are talking to: {self.chat_processor.default_model}.',
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'System'
        }
        
        # Don't save the system message to the database
        # self.message_manager.add_message(system_message)
        
        socketio.emit('message', system_message, broadcast=True)
    
    def handle_disconnect(self):
        """Handle client disconnection event."""
        print('Client disconnected')
        
        # Create system message for user disconnection
        system_message = {
            'message': 'A user has left the chat',
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'System'
        }
        
        # Don't save the system message to the database
        # self.message_manager.add_message(system_message)
        
        socketio.emit('message', system_message, broadcast=True)
    
    def handle_message(self, data):
        """
        Handle incoming messages from clients.
        
        Args:
            data (dict): The message data
        """
        # (Re)Set the timestamp
        data['timestamp'] = datetime.datetime.now().isoformat()
        
        # Save the message to the database and memory
        self.message_manager.add_message(data)
        
        # Check for and handle special commands such as persona switches
        if self.command_handler.handle_user_commands(data):
            return
        
        # Check if this is a direct message to the agent
        user_message = data.get('message', '')
        if user_message.lower().startswith('@agent'):
            self.agent_manager.handle_direct_agent_command(user_message)
            return
        
        # Check for regular @agent mention without making it a direct command
        talk_to_agent = True if "@agent" in user_message else False
        
        # Check if it's time for a periodic agent check
        execute_agent_chain = False
        if data.get('role') == 'User':
            if self.message_manager.user_message_counter % 3 == 0:
                execute_agent_chain = True
                print(f"Third user message detected (#{self.message_manager.user_message_counter}). Executing agent chain...")
        
        if data.get('role') == 'User' and not talk_to_agent:
            # Process the message with ChatProcessor, passing the entire message history
            # and the injections array
            self.chat_processor.process_message(
                data, 
                self.message_manager.messages, 
                self.message_manager.injections
            )
            
            # Execute the agent chain every third message
            if execute_agent_chain:
                self.agent_manager.run_periodic_agent_check(user_message)
            
        elif data.get('role') == 'Chat-AI' or talk_to_agent:
            # Inform the agent about the chat-AI's response
            print("Calling agent only.")
        
        # Broadcast the message to all clients except the sender
        # This prevents message duplication for the original sender
        socketio.emit('message', data, broadcast=True, include_self=False)
