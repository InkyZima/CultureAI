import os
import pytest
import sqlite3
from datetime import datetime

class BasicChatCore:
    def __init__(self):
        """Initialize basic chat core for testing"""
        self.db_path = 'data/test_chat.db'
        self.chat_history = []
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Set initial system prompt
        self.system_prompt = "You are a helpful assistant."
        self.chat_history.append({"role": "system", "content": self.system_prompt})
    
    def init_database(self):
        """Initialize the SQLite database with messages table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS messages")
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def save_message(self, role: str, content: str):
        """Save a message to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (role, content) VALUES (?, ?)',
                (role, content)
            )
            conn.commit()
    
    def get_all_messages(self):
        """Get all messages from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role, content FROM messages ORDER BY id')
            return cursor.fetchall()
    
    async def process_message(self, message: str) -> str:
        """Process a user message and return a response"""
        # Add user message to chat history and database
        self.chat_history.append({"role": "user", "content": message})
        self.save_message("user", message)
        
        # Generate simple response
        response = f"You said: {message}"
        
        # Add response to chat history and database
        self.chat_history.append({"role": "assistant", "content": response})
        self.save_message("assistant", response)
        
        return response

@pytest.fixture
def chat_core():
    # Create test instance
    chat = BasicChatCore()
    
    # Initialize and yield
    yield chat
    
    # Cleanup after test
    try:
        os.remove(chat.db_path)
    except:
        pass

@pytest.mark.asyncio
async def test_basic_chat_flow():
    """Test that the chat can process a simple message and save to database"""
    chat = BasicChatCore()
    
    # Send test message
    message = "test message"
    response = await chat.process_message(message)
    
    # Verify response
    assert response == f"You said: {message}"
    
    # Verify chat history
    assert len(chat.chat_history) == 3  # system + user + assistant
    assert chat.chat_history[1]["role"] == "user"
    assert chat.chat_history[1]["content"] == message
    assert chat.chat_history[2]["role"] == "assistant"
    assert chat.chat_history[2]["content"] == response
    
    # Verify database
    messages = chat.get_all_messages()
    assert len(messages) == 2  # user + assistant
    assert messages[0][0] == "user"  # role
    assert messages[0][1] == message  # content
    assert messages[1][0] == "assistant"  # role
    assert messages[1][1] == response  # content
