import os
import sqlite3
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.async_modules.async_task_manager import AsyncTaskManager
from src.prompt_manager import PromptManager

class MainChatCore:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()
        
        # Initialize chat history with system prompt
        self.system_prompt = self.prompt_manager.get_prompt('main_chat')
        self.chat_history = [SystemMessage(content=self.system_prompt)]

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        
        # Initialize database and load chat history
        self.init_database()
        stored_history = self.load_chat_history()
        
        # Add stored messages to chat history
        for msg in stored_history:
            if msg['role'] == 'human':
                self.chat_history.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'ai':
                self.chat_history.append(AIMessage(content=msg['content']))
        
        # Initialize async task manager
        self.task_manager = AsyncTaskManager()
        
        # Initialize Gemini through LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )

    async def initialize(self):
        """Async initialization method"""
        print("Initializing AsyncTaskManager...")
        await self.task_manager.start()
        print("AsyncTaskManager initialized")

    def init_database(self):
        """Initialize SQLite database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instruction TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    executed BOOLEAN NOT NULL DEFAULT FALSE,
                    execution_time DATETIME
                )
            ''')
            
            # Only insert system prompt if messages table is completely empty
            cursor.execute('SELECT COUNT(*) FROM messages')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                             ("system", self.system_prompt))
            conn.commit()
    
    def load_chat_history(self):
        """Load chat history from SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Only load actual messages, skip loading any previous system prompts
            cursor.execute('''
                SELECT role, content 
                FROM messages 
                WHERE role != 'system'
                ORDER BY id
            ''')
            return [{"role": role, "content": content} for role, content in cursor.fetchall()]
    
    def save_message(self, role, content):
        """Save a new message to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                         (role, content))
            conn.commit()
        
    def get_latest_instruction(self):
        """Fetch the latest unexecuted instruction from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, instruction FROM generated_instructions 
                WHERE executed = FALSE 
                ORDER BY priority DESC, timestamp DESC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                # Mark instruction as executed
                instruction_id, instruction = result
                cursor.execute('''
                    UPDATE generated_instructions 
                    SET executed = TRUE, execution_time = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (instruction_id,))
                conn.commit()
                return instruction
            return None

    def refresh_system_prompt(self):
        """Refresh the system prompt and update chat history"""
        new_prompt = self.prompt_manager.get_prompt('main_chat')
        if new_prompt != self.system_prompt:
            self.system_prompt = new_prompt
            # Update the system message in chat history
            if self.chat_history and isinstance(self.chat_history[0], SystemMessage):
                self.chat_history[0] = SystemMessage(content=self.system_prompt)
            else:
                # Insert system message at the beginning if not present
                self.chat_history.insert(0, SystemMessage(content=self.system_prompt))

    async def process_message(self, message: str) -> str:
        """Process a message and return the response"""
        # Refresh system prompt before processing
        self.refresh_system_prompt()
        
        # Add message to chat history
        self.chat_history.append(HumanMessage(content=message))
        
        # Only check for instructions if this isn't the first user message
        # We count messages after the system prompt
        if len(self.chat_history) > 2:  # System prompt + at least one exchange
            instruction = self.get_latest_instruction()
            if instruction:
                # Append instruction to the last user message
                self.chat_history[-1] = HumanMessage(
                    content=f"{message}\n[System instruction: {instruction}]"
                )
        
        # Get response from LLM
        response = await self.llm.agenerate([self.chat_history])
        ai_message = response.generations[0][0].text
        
        # Add response to chat history
        self.chat_history.append(AIMessage(content=ai_message))
        
        # Save to database - save original message without instruction
        self.save_message("human", message)
        self.save_message("ai", ai_message)
        
        # Add task to async manager - passing as a single task object
        await self.task_manager.add_task(
            "process_chat",
            chat_history=self.chat_history
        )
        
        return ai_message