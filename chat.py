import datetime

class ChatProcessor:
    def __init__(self, socketio, db=None):
        """Initialize the chat processor with SocketIO instance and optional database."""
        self.socketio = socketio
        self.db = db
    
    def set_database(self, db):
        """Set the database instance."""
        self.db = db
    
    def process_message(self, message_data):
        """
        Process a user message:
        - Transform the message to all caps
        - Send it back via the WebSocket
        """
        # Extract message content and other data
        original_message = message_data.get('message', '')
        timestamp = message_data.get('timestamp', datetime.datetime.now().isoformat())
        
        # Transform the message to all caps
        transformed_message = original_message.upper()
        
        # Create a response message
        response = {
            'message': transformed_message,
            'timestamp': datetime.datetime.now().isoformat(),
            'role': 'Chat-AI',
            'original_message': original_message  # For debugging/reference
        }
        
        # Log the processed message
        print(f"chat.py: transformed message '{original_message}' to '{transformed_message}'")
        
        # Save to database if available
        if self.db:
            self.db.save_message(response)
        
        # Send the message back to all clients
        self.socketio.emit('message', response)
        
        return response
        
if __name__ == "__main__":
    print("This file should not be run directly. Import it from app.py instead.")
