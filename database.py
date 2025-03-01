import sqlite3
import os
import json

class MessageDatabase:
    def __init__(self, db_file='messages.db'):
        """Initialize the database connection."""
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Connect to the SQLite database."""
        try:
            # Check if the database file exists
            db_exists = os.path.exists(self.db_file)
            
            # Create a connection to the database
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # This enables column access by name
            self.cursor = self.connection.cursor()
            
            if not db_exists:
                print(f"Database file {self.db_file} created.")
            else:
                print(f"Connected to existing database {self.db_file}.")
                
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            # Create messages table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.connection.commit()
            print("Database tables created or already exist.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
    
    def save_message(self, message_data):
        """Save a message to the database."""
        try:
            # Extract message components
            message_text = message_data.get('message', '')
            timestamp = message_data.get('timestamp', '')
            role = message_data.get('role', '')
            
            # If message_data is a string, try to handle it (for backward compatibility)
            if isinstance(message_data, str):
                message_text = message_data
                timestamp = ''
                role = 'Unknown'
            
            # Insert the message into the database
            self.cursor.execute(
                "INSERT INTO messages (message, timestamp, role) VALUES (?, ?, ?)",
                (message_text, timestamp, role)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error saving message to database: {e}")
            return False
    
    def get_messages(self, limit=100):
        """Retrieve the most recent messages from the database."""
        try:
            self.cursor.execute(
                "SELECT * FROM messages ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = self.cursor.fetchall()
            
            # Convert rows to dictionaries
            messages = []
            for row in rows:
                messages.append({
                    'id': row['id'],
                    'message': row['message'],
                    'timestamp': row['timestamp'],
                    'role': row['role'],
                    'created_at': row['created_at']
                })
            
            return messages
        except Exception as e:
            print(f"Error retrieving messages from database: {e}")
            return []
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
