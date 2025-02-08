import os
import pytest
import sqlite3
import asyncio
from src.main_chat_core import MainChatCore
from unittest.mock import patch, MagicMock

@pytest.fixture
def chat_core():
    # Create a test database path
    test_db_path = 'data/test_chat.db'
    
    # Ensure test directory exists
    os.makedirs('data', exist_ok=True)
    
    # Remove test database if it exists
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            pass  # File might be locked by another test
    
    # Create MainChatCore instance with mocked LLM and task manager
    with patch('src.main_chat_core.ChatGoogleGenerativeAI') as mock_llm, \
         patch('src.main_chat_core.AsyncTaskManager') as mock_task_manager:
        
        # Configure mock LLM to return a predictable response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="Test AI response")]]
        
        # Make agenerate a coroutine that returns our mock response
        async def mock_agenerate(*args, **kwargs):
            return mock_response
        mock_llm_instance.agenerate = mock_agenerate
        mock_llm.return_value = mock_llm_instance
        
        # Mock task manager's async methods
        async def mock_start():
            pass
        async def mock_add_task(*args, **kwargs):
            pass
        mock_task_manager_instance = MagicMock()
        mock_task_manager_instance.start = mock_start
        mock_task_manager_instance.add_task = mock_add_task
        mock_task_manager.return_value = mock_task_manager_instance
        
        # Create chat core instance
        core = MainChatCore()
        core.db_path = test_db_path
        core.init_database()
        
        yield core
        
        # Close any open database connections
        try:
            with sqlite3.connect(test_db_path) as conn:
                conn.close()
        except sqlite3.Error:
            pass
        
        # Cleanup
        for _ in range(3):  # Try a few times with delays
            try:
                if os.path.exists(test_db_path):
                    os.remove(test_db_path)
                break
            except PermissionError:
                import time
                time.sleep(0.1)  # Give some time for connections to close

@pytest.mark.asyncio
async def test_basic_user_ai_interaction(chat_core):
    """Test basic user message and AI response flow"""
    # Process a user message
    test_message = "Hello, how are you?"
    response = await chat_core.process_message(test_message)
    
    # Verify AI response
    assert response == "Test AI response"
    
    # Verify messages were saved to database
    with sqlite3.connect(chat_core.db_path) as conn:
        cursor = conn.cursor()
        
        # Check user message
        cursor.execute('SELECT content FROM messages WHERE role = "human" ORDER BY id DESC LIMIT 1')
        saved_user_msg = cursor.fetchone()[0]
        assert saved_user_msg == test_message
        
        # Check AI response
        cursor.execute('SELECT content FROM messages WHERE role = "ai" ORDER BY id DESC LIMIT 1')
        saved_ai_msg = cursor.fetchone()[0]
        assert saved_ai_msg == "Test AI response"
        
        # Verify system prompt exists
        cursor.execute('SELECT COUNT(*) FROM messages WHERE role = "system"')
        assert cursor.fetchone()[0] == 1

@pytest.mark.asyncio
async def test_chat_history_persistence(chat_core):
    """Test that chat history is properly persisted and loaded"""
    # Send multiple messages
    messages = ["Hello!", "How's the weather?", "Tell me about your day"]
    for msg in messages:
        await chat_core.process_message(msg)
    
    # Create a new chat core instance to test loading
    with patch('src.main_chat_core.ChatGoogleGenerativeAI'), \
         patch('src.main_chat_core.AsyncTaskManager'):
        new_core = MainChatCore()
        new_core.db_path = chat_core.db_path
        
        # Load chat history
        loaded_history = new_core.load_chat_history()
        
        # Verify system message exists
        system_messages = [msg["content"] for msg in loaded_history if msg["role"] == "system"]
        assert len(system_messages) == 1
        system_msg = system_messages[0].lower()
        assert "cultural ai companion" in system_msg
        assert "role" in system_msg
        assert "engage" in system_msg
        
        # Verify all user messages are present
        human_messages = [msg["content"] for msg in loaded_history if msg["role"] == "human"]
        assert all(msg in human_messages for msg in messages)
        assert len(human_messages) == len(messages)
        
        # Verify AI responses are present (excluding system message)
        ai_messages = [msg["content"] for msg in loaded_history if msg["role"] == "ai"]
        assert len(ai_messages) == len(messages)
        assert all(msg == "Test AI response" for msg in ai_messages)
