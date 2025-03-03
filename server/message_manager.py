"""
Message management module for in-memory state and database interactions.
"""
import datetime
from database import MessageDatabase

class MessageManager:
    """
    Manages message state and database interactions for the chat application.
    """
    
    def __init__(self, db=None):
        """
        Initialize the message manager.
        
        Args:
            db (MessageDatabase, optional): Database instance. If None, creates a new one.
        """
        # Create or use the provided database connection
        self.db = db or MessageDatabase()
        
        # In-memory storage
        self.messages = []
        self.injections = []
        self.user_message_counter = 0
        
        # Load existing data
        self.load_data_from_database()
    
    def load_data_from_database(self):
        """
        Load existing messages and injections from the database into memory.
        """
        # Load messages
        db_messages = self.db.get_messages(limit=100)  # Limit to last 100 messages
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
                self.messages.append(message_obj)
            print(f"Loaded {len(self.messages)} messages from database")
        
        # Load injections
        db_injections = self.db.get_injections(consumed=False)  # Get only unconsumed injections
        if db_injections:
            # Add to injections array
            for inj in db_injections:
                injection_obj = {
                    'injection': inj['injection'],
                    'timestamp': inj['timestamp'],
                    'role': inj['role'],
                    'consumed': inj['consumed']
                }
                self.injections.append(injection_obj)
            print(f"Loaded {len(self.injections)} active injections from database")
    
    def add_message(self, message_data):
        """
        Add a message to the in-memory store and database.
        
        Args:
            message_data (dict): Message data to store
        """
        # Save to database
        self.db.save_message(message_data)
        
        # Add to in-memory store
        self.messages.append(message_data)
        
        # If it's a user message, increment the counter
        if message_data.get('role') == 'User':
            self.user_message_counter += 1
    
    def add_injection(self, injection_data):
        """
        Add an injection to the in-memory store and database.
        
        Args:
            injection_data (dict): Injection data to store
        """
        # Save to database
        self.db.save_injection(injection_data)
        
        # Add to in-memory store
        self.injections.append(injection_data)
    
    def clear_all_data(self):
        """
        Clear all messages and injections from database and memory.
        """
        # Clear database
        self.db.delete_all_messages()
        self.db.delete_all_injections()
        self.db.delete_all_agent_calls()
        
        # Clear in-memory data
        self.messages.clear()
        self.injections.clear()
        self.user_message_counter = 0
    
    def close(self):
        """
        Close the database connection.
        """
        if self.db:
            self.db.close()
