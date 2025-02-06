import os
import sqlite3
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.async_modules.async_task_manager import AsyncTaskManager

class MainChatCore:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize chat history with system prompt
        self.system_prompt = """You are a friendly and knowledgeable cultural AI companion. Your role is to:
1. Engage in natural, warm conversations while sharing cultural insights
2. Help users understand and appreciate different cultural perspectives
3. Provide guidance on cultural practices, traditions, and etiquette
4. Share interesting cultural stories and historical context when relevant
5. Be respectful and sensitive when discussing cultural topics
6. Encourage cultural learning and cross-cultural understanding

Remember to maintain a supportive and engaging tone while being accurate in your cultural knowledge."""
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
            
            # Check if system prompt exists, if not insert it
            cursor.execute('SELECT COUNT(*) FROM messages WHERE role = "system"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                             ("system", self.system_prompt))
            conn.commit()
    
    def load_chat_history(self):
        """Load chat history from SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role, content FROM messages ORDER BY id')
            return [{"role": role, "content": content} for role, content in cursor.fetchall()]
    
    def save_message(self, role, content):
        """Save a new message to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                         (role, content))
            conn.commit()
        
    async def process_message(self, message: str) -> str:
        """Process a message and return the response"""
        # Add message to chat history
        self.chat_history.append(HumanMessage(content=message))
        
        # Get response from LLM
        response = await self.llm.agenerate([self.chat_history])
        ai_message = response.generations[0][0].text
        
        # Add response to chat history
        self.chat_history.append(AIMessage(content=ai_message))
        
        # Save to database
        self.save_message("human", message)
        self.save_message("ai", ai_message)
        
        # Add task to async manager - passing as a single task object
        await self.task_manager.add_task(
            "process_chat",
            chat_history=self.chat_history
        )
        
        return ai_message 