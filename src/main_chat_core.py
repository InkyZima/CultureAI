import os
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

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

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        
        # Initialize database and load chat history
        self.init_database()
        self.chat_history = self.load_chat_history()
        
        # Initialize Gemini through LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
    
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
        
    def process_message(self, message):
        # Add user message to chat history and database
        self.chat_history.append({"role": "user", "content": message})
        self.save_message("user", message)
        
        # Convert chat history to LangChain message format
        langchain_messages = [SystemMessage(content=self.system_prompt)]  # Always include system prompt
        for msg in self.chat_history[1:]:  # Skip the stored system message when converting
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        # Get response from LLM
        response = self.llm.invoke(langchain_messages)
        response_text = response.content
        
        # Add AI response to chat history and database
        self.chat_history.append({"role": "assistant", "content": response_text})
        self.save_message("assistant", response_text)
        
        return response_text 