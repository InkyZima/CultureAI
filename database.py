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
            
            # Create injections table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS injections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    injection TEXT NOT NULL,
                    consumed BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create agent_calls table for logging Gemini API calls
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT,
                    function_called TEXT,
                    function_args TEXT,
                    function_response TEXT,
                    error TEXT,
                    latency_ms INTEGER,
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
    
    def log_agent_call(self, call_data):
        """
        Log a Gemini API call to the agent_calls table.
        
        Args:
            call_data (dict): Dictionary containing call information with the following keys:
                - timestamp: ISO-formatted timestamp of when the call was made
                - model: The Gemini model used
                - prompt: The prompt sent to the model
                - response: The response received from the model (optional)
                - function_called: Name of the function called (optional)
                - function_args: JSON string of function arguments (optional)
                - function_response: The response from the function (optional)
                - error: Any error that occurred (optional)
                - latency_ms: The call latency in milliseconds (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract call components with defaults for optional fields
            timestamp = call_data.get('timestamp', '')
            model = call_data.get('model', '')
            prompt = call_data.get('prompt', '')
            response = call_data.get('response', None)
            function_called = call_data.get('function_called', None)
            function_args = call_data.get('function_args', None)
            function_response = call_data.get('function_response', None)
            error = call_data.get('error', None)
            latency_ms = call_data.get('latency_ms', None)
            
            # Convert dict/objects to JSON strings
            if response and not isinstance(response, str):
                response = json.dumps(response)
            if function_args and not isinstance(function_args, str):
                function_args = json.dumps(function_args)
            if function_response and not isinstance(function_response, str):
                function_response = json.dumps(function_response)
            
            # Insert the call into the database
            self.cursor.execute(
                """
                INSERT INTO agent_calls (
                    timestamp, model, prompt, response, function_called,
                    function_args, function_response, error, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp, model, prompt, response, function_called,
                    function_args, function_response, error, latency_ms
                )
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error logging agent call to database: {e}")
            return False
    
    def get_agent_calls(self, limit=100):
        """
        Retrieve the most recent agent calls from the database.
        
        Args:
            limit (int): Maximum number of records to retrieve
            
        Returns:
            list: List of agent call dictionaries
        """
        try:
            self.cursor.execute(
                "SELECT * FROM agent_calls ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = self.cursor.fetchall()
            
            # Convert rows to dictionaries
            calls = []
            for row in rows:
                calls.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'model': row['model'],
                    'prompt': row['prompt'],
                    'response': row['response'],
                    'function_called': row['function_called'],
                    'function_args': row['function_args'],
                    'function_response': row['function_response'],
                    'error': row['error'],
                    'latency_ms': row['latency_ms'],
                    'created_at': row['created_at']
                })
            
            return calls
        except Exception as e:
            print(f"Error retrieving agent calls from database: {e}")
            return []
    
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
    
    def delete_all_messages(self):
        """Delete all messages from the database."""
        try:
            self.cursor.execute("DELETE FROM messages")
            self.connection.commit()
            print(f"All messages deleted from the database.")
            return True
        except Exception as e:
            print(f"Error deleting messages from database: {e}")
            return False
    
    def save_injection(self, injection_data):
        """Save an injection to the database."""
        try:
            # Extract injection components
            role = injection_data.get('role', '')
            timestamp = injection_data.get('timestamp', '')
            injection = injection_data.get('injection', '')
            consumed = injection_data.get('consumed', False)
            
            # Insert the injection into the database
            self.cursor.execute(
                "INSERT INTO injections (role, timestamp, injection, consumed) VALUES (?, ?, ?, ?)",
                (role, timestamp, injection, 1 if consumed else 0)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error saving injection to database: {e}")
            return False
    
    def get_injections(self, consumed=None, limit=100):
        """Retrieve injections from the database.
        
        Args:
            consumed (bool, optional): Filter by consumed status. If None, returns all injections.
            limit (int): Maximum number of records to retrieve.
            
        Returns:
            list: List of injection dictionaries
        """
        try:
            query = "SELECT * FROM injections"
            params = []
            
            if consumed is not None:
                query += " WHERE consumed = ?"
                params.append(1 if consumed else 0)
                
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, tuple(params))
            rows = self.cursor.fetchall()
            
            # Convert rows to dictionaries
            injections = []
            for row in rows:
                injections.append({
                    'id': row['id'],
                    'role': row['role'],
                    'timestamp': row['timestamp'],
                    'injection': row['injection'],
                    'consumed': bool(row['consumed']),
                    'created_at': row['created_at']
                })
            
            return injections
        except Exception as e:
            print(f"Error retrieving injections from database: {e}")
            return []
    
    def mark_injection_consumed(self, injection_id):
        """Mark an injection as consumed."""
        try:
            self.cursor.execute(
                "UPDATE injections SET consumed = 1 WHERE id = ?",
                (injection_id,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error marking injection as consumed: {e}")
            return False
    
    def delete_all_injections(self):
        """Delete all injections from the database."""
        try:
            self.cursor.execute("DELETE FROM injections")
            self.connection.commit()
            print(f"All injections deleted from the database.")
            return True
        except Exception as e:
            print(f"Error deleting injections from database: {e}")
            return False
    
    def delete_all_agent_calls(self):
        """Delete all agent calls from the database."""
        try:
            self.cursor.execute("DELETE FROM agent_calls")
            self.connection.commit()
            print(f"All agent calls deleted from the database.")
            return True
        except Exception as e:
            print(f"Error deleting agent calls from database: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")
