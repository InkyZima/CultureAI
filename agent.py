import time
import threading
import datetime
import random

class MessageAgent:
    def __init__(self, socketio, db=None):
        self.socketio = socketio
        self.db = db  # Database instance (can be None)
        self.is_running = False
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
    
    def set_database(self, db):
        """Set the database instance."""
        self.db = db
    
    def start(self):
        """Start the agent in a separate thread."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            print("Agent started and will send messages every 5 seconds")
    
    def stop(self):
        """Stop the agent."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
            print("Agent stopped")
    
    def receive_user_message(self, message_data):
        """Handle a user message received from the frontend."""
        # Extract the message content from the data
        message_content = message_data.get('message', '')
        user_role = message_data.get('role', 'Unknown')
        
        # Print the received message to the shell
        print(f"agent.py: received user message: {message_content} (from {user_role})")
        
        # Here you could add additional logic to process or respond to the message
    
    def _run(self):
        """Main loop for the agent."""
        while self.is_running:
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
