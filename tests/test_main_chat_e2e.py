import os
import pytest
import sqlite3
from src.main_chat_core import MainChatCore

@pytest.fixture
def chat_core():
    # Create test instance
    chat = MainChatCore()
    
    # Initialize and yield
    yield chat
    
    # Cleanup after test
    try:
        os.remove(chat.db_path)
    except:
        pass

@pytest.mark.asyncio
async def test_basic_chat_flow(chat_core):
    """Test that the chat can process a simple message and return a response"""
    # Initialize chat
    await chat_core.initialize()
    
    # Send a test message
    message = "i like football"
    try:
        response = await chat_core.process_message(message)
        
        # Basic validation
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"\nReceived response: {response}")
        
        # Verify chat history
        assert len(chat_core.chat_history) >= 2  # Should have system prompt and at least one exchange
        assert any(msg["role"] == "user" and msg["content"] == message for msg in chat_core.chat_history)
        assert any(msg["role"] == "assistant" and msg["content"] == response for msg in chat_core.chat_history)
        
    except Exception as e:
        pytest.fail(f"Failed to process message: {str(e)}")
