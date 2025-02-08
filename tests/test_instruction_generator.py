import os
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from src.async_modules.instruction_generator import InstructionGenerator

@pytest.fixture
def instruction_generator():
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
    
    # Create InstructionGenerator instance with mocked LLM
    with patch('src.async_modules.instruction_generator.ChatGoogleGenerativeAI') as mock_llm:
        # Configure mock LLM to return a predictable response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text='''Instructions:
- Instruction: Share a story about Japanese tea ceremonies and their cultural significance
  Priority: 4
  Reason: User has shown interest in cultural practices and meditation

- Instruction: Ask about previous experience with mindfulness practices
  Priority: 3
  Reason: Context suggests interest in meditation and cultural learning
''')]]
        
        # Make agenerate a coroutine that returns our mock response
        async def mock_agenerate(*args, **kwargs):
            return mock_response
        mock_llm_instance.agenerate = mock_agenerate
        mock_llm.return_value = mock_llm_instance
        
        # Create generator instance
        generator = InstructionGenerator()
        generator.db_path = test_db_path
        generator.init_database()
        
        yield generator
        
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
                time.sleep(0.1)

@pytest.mark.asyncio
async def test_process_user_triggered(instruction_generator):
    """Test generation of instructions based on user interaction"""
    # Mock chat history and conversation analysis
    chat_history = [
        {"role": "user", "content": "I'm interested in learning about meditation"},
        {"role": "assistant", "content": "That's great! Meditation is a wonderful practice."}
    ]
    
    conversation_analysis = {
        "engagement_level": "high",
        "cultural_learning": "interested in mindfulness practices",
        "guidance_needed": "meditation techniques",
        "suggested_topics": "Japanese tea ceremony, meditation"
    }
    
    # Process the chat history
    instructions = await instruction_generator.process_user_triggered(chat_history, conversation_analysis)
    
    # Debug print
    print("\nGenerated instructions:")
    for instr in instructions:
        print(f"- {instr}")
    
    # Verify instructions were generated
    assert len(instructions) == 2
    
    # Verify first instruction about tea ceremonies
    tea_ceremony_instr = instructions[0]
    assert "tea ceremonies" in tea_ceremony_instr["instruction"].lower()
    assert tea_ceremony_instr["priority"] == 4
    assert "cultural practices" in tea_ceremony_instr["reason"].lower()
    
    # Verify second instruction about mindfulness
    mindfulness_instr = instructions[1]
    assert "mindfulness" in mindfulness_instr["instruction"].lower()
    assert mindfulness_instr["priority"] == 3
    assert "meditation" in mindfulness_instr["reason"].lower()
    
    # Verify instructions were saved to database
    with sqlite3.connect(instruction_generator.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM generated_instructions WHERE trigger_type = "user"')
        count = cursor.fetchone()[0]
        assert count == 2
        
        # Check instruction details
        cursor.execute('''
            SELECT instruction, priority, executed 
            FROM generated_instructions 
            WHERE trigger_type = "user"
        ''')
        instructions_db = cursor.fetchall()
        
        # Verify priorities are within expected range
        assert all(1 <= priority <= 5 for _, priority, _ in instructions_db)
        # Verify instructions are not executed yet
        assert all(not executed for _, _, executed in instructions_db)

@pytest.mark.asyncio
async def test_instruction_parsing(instruction_generator):
    """Test parsing of LLM response into structured instructions"""
    test_response = '''Instructions:
- Instruction: Test instruction 1
  Priority: 1
  Reason: Test reason 1

- Instruction: Test instruction 2
  Priority: 4
  Reason: Test reason 2
'''
    
    # Parse the test response
    instructions = instruction_generator._parse_llm_response(test_response)
    
    # Verify parsing results
    assert len(instructions) == 2
    assert instructions[0]["instruction"] == "Test instruction 1"
    assert instructions[0]["priority"] == 1
    assert instructions[0]["reason"] == "Test reason 1"
    assert instructions[1]["instruction"] == "Test instruction 2"
    assert instructions[1]["priority"] == 4
    assert instructions[1]["reason"] == "Test reason 2"
