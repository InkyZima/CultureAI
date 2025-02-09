import os
import sqlite3
from typing import Dict, Optional

class PromptManager:
    def __init__(self, db_path: str = 'data/chat.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database table for system prompts"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Drop existing table if it exists
            cursor.execute('DROP TABLE IF EXISTS system_prompts')
            
            # Create the table with new schema
            cursor.execute('''
                CREATE TABLE system_prompts (
                    module_name TEXT PRIMARY KEY,
                    prompt_text TEXT NOT NULL,
                    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Define default prompts
            default_prompts = {
                'main_chat': '''You are a cultural AI companion, designed to engage in meaningful conversations and provide guidance throughout the day.
Your responses should be:
1. Culturally aware and sensitive
2. Time-appropriate for the user's current time of day
3. Encouraging and supportive
4. Focused on personal growth and cultural understanding''',
                
                'instruction_generator': '''You are an instruction generator for a cultural AI companion. Your role is to:
1. Analyze conversation context and generate specific, actionable instructions
2. Focus on cultural relevance and engagement
3. Prioritize instructions based on conversation needs
4. Consider both immediate context and longer-term conversation goals
5. Generate instructions that help maintain cultural sensitivity and accuracy''',
                
                'information_extractor': '''You are an information extractor for a cultural AI companion. Your role is to:
1. Extract key information from conversations
2. Identify cultural references and context
3. Track user preferences and interests
4. Note important dates and events
5. Maintain a record of cultural learning points''',
                
                'conversation_analyzer': '''You are a conversation analyzer for a cultural AI companion. Your role is to:
1. Analyze conversation flow and engagement
2. Identify cultural learning opportunities
3. Track conversation themes and patterns
4. Assess cultural sensitivity and appropriateness
5. Provide insights for improving cultural dialogue'''
            }
            
            # Insert default prompts
            for module_name, prompt_text in default_prompts.items():
                cursor.execute('''
                    INSERT INTO system_prompts (module_name, prompt_text)
                    VALUES (?, ?)
                ''', (module_name, prompt_text))
            
            conn.commit()
    
    def get_prompt(self, module_name: str) -> str:
        """Get the prompt for a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT prompt_text FROM system_prompts WHERE module_name = ?',
                         (module_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                raise ValueError(f"No prompt found for module: {module_name}")
    
    def set_prompt(self, module_name: str, prompt: str):
        """Set a prompt for a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_prompts (module_name, prompt_text, last_modified)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (module_name, prompt))
            conn.commit()
    
    def list_modules(self) -> list:
        """List all available prompt modules"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT module_name FROM system_prompts')
            return [row[0] for row in cursor.fetchall()]
    
    def get_prompt_info(self, module_name: str) -> Dict:
        """Get prompt info for a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT module_name, prompt_text, last_modified
                FROM system_prompts
                WHERE module_name = ?
            ''', (module_name,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'module_name': result[0],
                    'prompt': result[1],
                    'last_modified': result[2]
                }
            else:
                raise ValueError(f"No prompt found for module: {module_name}")
