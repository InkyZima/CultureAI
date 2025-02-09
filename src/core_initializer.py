"""Module responsible for initializing core components of the chat system."""

import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from src.prompt_manager import PromptManager
from src.async_modules.async_task_manager import AsyncTaskManager

class CoreInitializer:
    """Handles initialization of core components for the chat system."""
    
    @staticmethod
    def init_llm():
        """Initialize and return the LangChain LLM."""
        load_dotenv()
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=1
        )
    
    @staticmethod
    def init_database(db_path: str):
        """Initialize SQLite database and create necessary tables."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create feature toggles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_toggles (
                    feature_name TEXT PRIMARY KEY,
                    is_enabled INTEGER NOT NULL DEFAULT 1,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create generated instructions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instruction TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    executed BOOLEAN DEFAULT FALSE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    execution_time DATETIME
                )
            ''')
            
            # Initialize feature toggles if not exists
            features = [
                'information_extractor',
                'conversation_analyzer',
                'instruction_generator'
            ]
            
            for feature in features:
                cursor.execute('''
                    INSERT OR IGNORE INTO feature_toggles (feature_name, is_enabled)
                    VALUES (?, 1)
                ''', (feature,))
            
            conn.commit()
    
    @staticmethod
    def load_chat_history(db_path: str):
        """Load chat history from SQLite database and return as LangChain message objects."""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content 
                FROM messages 
                WHERE role != 'system'
                ORDER BY id
            ''')
            messages = []
            for role, content in cursor.fetchall():
                if role == 'human':
                    messages.append(HumanMessage(content=content))
                elif role == 'ai':
                    messages.append(AIMessage(content=content))
            return messages
    
    @staticmethod
    async def init_task_manager():
        """Initialize and start the AsyncTaskManager."""
        task_manager = AsyncTaskManager()
        await task_manager.start()
        return task_manager
