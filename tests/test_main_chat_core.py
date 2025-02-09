"""Tests for the MainChatCore class."""

import os
import pytest
import sqlite3
from src.main_chat_core import MainChatCore
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def chat_core():
    """Fixture that provides a MainChatCore instance with mocked dependencies."""
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
    
    # Create MainChatCore instance with mocked components
    with patch('src.core_initializer.ChatGoogleGenerativeAI') as mock_llm:
        # Configure mock LLM to return a predictable response
        mock_llm_instance = MagicMock()
        mock_response = AIMessage(content="Test AI response")
        
        # Make ainvoke a coroutine that returns our mock response
        async def mock_ainvoke(*args, **kwargs):
            return mock_response
        mock_llm_instance.ainvoke = mock_ainvoke
        mock_llm.return_value = mock_llm_instance
        
        # Create chat core instance
        from src.core_initializer import CoreInitializer
        CoreInitializer.init_database(test_db_path)  # Initialize database first
        
        core = MainChatCore()
        core.db_path = test_db_path
        
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
    """Test basic user message and AI response flow."""
    # Process a user message
    test_message = "Hello, how are you?"
    response = await chat_core.process_message(HumanMessage(content=test_message))
    
    # Verify AI response
    assert response.content == "Test AI response"
    
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

@pytest.mark.asyncio
async def test_chat_history_persistence(chat_core):
    """Test that chat history is properly persisted and loaded."""
    # Send multiple messages
    messages = ["Hello!", "How's the weather?", "Tell me about your day"]
    for msg in messages:
        await chat_core.process_message(HumanMessage(content=msg))
    
    # Create a new chat core instance to test loading
    with patch('src.core_initializer.ChatGoogleGenerativeAI'):
        new_core = MainChatCore()
        new_core.db_path = chat_core.db_path
        
        # Verify all user messages are present in chat history
        human_messages = [msg.content for msg in new_core.chat_history if isinstance(msg, HumanMessage)]
        assert all(msg in human_messages for msg in messages)
        assert len(human_messages) == len(messages)
        
        # Verify AI responses are present
        ai_messages = [msg.content for msg in new_core.chat_history if isinstance(msg, AIMessage)]
        assert len(ai_messages) == len(messages)
        assert all(msg == "Test AI response" for msg in ai_messages)

@pytest.mark.asyncio
async def test_system_prompt_update(chat_core):
    """Test updating the system prompt."""
    new_prompt = "New test system prompt"
    chat_core.update_system_prompt(new_prompt)
    
    # Verify the prompt was updated
    messages = chat_core.chat_prompt.format_messages(chat_history=[], input="test")
    assert messages[0].content == new_prompt
