"""
Handles special user commands in the chat application.
"""
import datetime
import os
from server.config import socketio

class CommandHandler:
    """
    Handles special user commands like persona changes and data deletion.
    """
    
    def __init__(self, message_manager, chat_processor):
        """
        Initialize the command handler.
        
        Args:
            message_manager: Message manager instance for data management
            chat_processor: Chat processor instance for resetting sessions
        """
        self.message_manager = message_manager
        self.chat_processor = chat_processor
    
    def handle_user_commands(self, data):
        """
        Process special user commands.
        
        Args:
            data (dict): The message data
            
        Returns:
            bool: True if a command was processed, False otherwise
        """
        # Check for persona change commands
        if self._process_persona_command(data, '/persona conversationalist', 'system_prompts/conversationalist.txt'):
            return True
        
        if self._process_persona_command(data, '/persona joker', 'system_prompts/joker.txt'):
            return True
    
        if self._process_persona_command(data, '/persona default', 'system_prompts/system_prompt.txt'):
            return True
        
        # Check for the delete command
        if data.get('role') == 'User' and '/delete' in data.get('message', ''):
            try:
                # Delete all messages and injections
                self.message_manager.clear_all_data()
                
                # Reset the chat processor's chat sessions
                self.chat_processor.chat_sessions.clear()
                
                # Inform the user
                system_message = {
                    'message': 'All messages and injections have been deleted.',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'System'
                }
                socketio.emit('message', system_message, broadcast=True)
                return True
                
            except Exception as e:
                print(f"Error processing delete command: {e}")
                system_message = {
                    'message': f'Error deleting messages and injections: {str(e)}',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'System'
                }
                socketio.emit('message', system_message, broadcast=True)
                return True
        
        # Add more command handlers here in the future
        
        return False  # No commands were processed
    
    def _process_persona_command(self, data, command, persona_file):
        """
        Handle persona change commands by loading content from specified file.
        
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
                
                # Add to injections
                self.message_manager.add_injection(injection)
                
                # Inform the user
                system_message = {
                    'message': f'Persona changed to: {persona_name.capitalize()}',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'System'
                }
                socketio.emit('message', system_message, broadcast=True)
                return True
                
            except Exception as e:
                print(f"Error loading {persona_file} persona: {e}")
                system_message = {
                    'message': f'Error changing persona: {str(e)}',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'role': 'System'
                }
                socketio.emit('message', system_message, broadcast=True)
                return True
        
        return False
