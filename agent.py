import time
import threading
import datetime
import random

class MessageAgent:
    def __init__(self, socketio, db=None):
        self.socketio = socketio
        self.db = db  # Database instance (can be None)
        self.active = False
        self.thread = None
        self.test_messages = [
            "Hello, this is a test message from the agent!",
            "How are you doing today?",
            "The weather is lovely, isn't it?",
            "Did you know that agents can send automated messages?",
            "This message was sent automatically every 5 seconds.",
            "AI agents can help automate various tasks.",
            "WebSockets are a great way to implement real-time communication!",
            "Flask and Socket.IO make a powerful combination.",
            "Testing, testing, 1, 2, 3...",
            "This is an automated message from your friendly agent."
        ]
        self.last_message_time = 0
    
    def set_database(self, db):
        """Set the database instance."""
        self.db = db
    
    def start(self):
        """Start the message agent in a separate thread."""
        self.active = True
        # self.thread = threading.Thread(target=self._run)
        # self.thread.daemon = True  # Thread will exit when the main program exits
        # self.thread.start()
        print("MessageAgent started in background thread")

    def stop(self):
        """Stop the message agent thread."""
        self.active = False
        if self.thread:
            self.thread.join(timeout=1)  # Wait for thread to finish
        print("MessageAgent stopped")

    def receive_user_message(self, message_data, message_history=[]):
        """
        Receive and process a message from a user or AI.
        
        Args:
            message_data (dict): The message data
            message_history (list): The full history of messages for context
        """
        # Extract message content
        message = message_data.get('message', '')
        role = message_data.get('role', 'Unknown')
        
        # Process the message
        print(f"Agent received message: '{message}' from {role}")
        
        # Update last message timestamp
        self.last_message_time = time.time()
    
    def _process_targeted_message(self, message, message_history):
        """Process a message specifically targeted at the agent.
        
        Args:
            message (str): The message content
            message_history (list): The full history of messages
        """
        # Process message that was specifically directed to the agent
        print(f"Processing targeted message for Agent: '{message}'")
        
        # Simple command processing
        if "status" in message.lower():
            self._send_status_message()
        elif "help" in message.lower():
            self._send_help_message()
        else:
            # For now, just acknowledge
            response = {
                'message': f"Agent received: {message} - I don't have advanced processing capabilities yet.",
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'Agent-AI'
            }
            
            # Save to database if available
            if self.db:
                self.db.save_message(response)
                
            # Send the message to all clients
            self.socketio.emit('message', response)
    
    def _send_status_message(self):
        # For now, just send a simple status message
        response = {
            'message': "Agent is online and running.",
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'Agent-AI'
        }
        
        # Save to database if available
        if self.db:
            self.db.save_message(response)
            
        # Send the message to all clients
        self.socketio.emit('message', response)
    
    def _send_help_message(self):
        # For now, just send a simple help message
        response = {
            'message': "Agent can understand the following commands: status, help.",
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'Agent-AI'
        }
        
        # Save to database if available
        if self.db:
            self.db.save_message(response)
            
        # Send the message to all clients
        self.socketio.emit('message', response)
    
    def _run(self):
        """Main loop for the agent."""
        while self.active:
            try:
                # Generate a test message
                message = self._generate_message()
                
                # Send the message to all connected clients
                self.socketio.emit('message', message)
                
                # Save the message to the database if available
                if self.db:
                    self.db.save_message(message)
                
                # Log the message
                print(f"Agent sent message: {message}")
                
                # Wait for 5 seconds
                time.sleep(5)
            except Exception as e:
                print(f"Error in agent thread: {e}")
                time.sleep(5)  # Wait a bit before retrying
    
    def _generate_message(self):
        """Generate a random test message."""
        return {
            'message': random.choice(self.test_messages),
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'Agent-AI'
        }

# This will be imported and instantiated in app.py
# Do not run this file directly
if __name__ == "__main__":
    print("This file should not be run directly. Import it from app.py instead.")
