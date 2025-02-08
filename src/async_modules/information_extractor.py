import sqlite3
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from src.prompt_manager import PromptManager

class InformationExtractor:
    def __init__(self):
        load_dotenv()
        
        # Initialize prompt manager and get system prompt
        self.prompt_manager = PromptManager()
        self.system_prompt = self.prompt_manager.get_prompt('information_extractor')
        
        # Initialize database connection
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        self.init_database()
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3  # Lower temperature for more focused extraction
        )
    
    def init_database(self):
        """Initialize the database table for extracted information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_information (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    category TEXT NOT NULL,
                    item TEXT NOT NULL,
                    source_messages TEXT NOT NULL  -- Store IDs of messages this was extracted from
                )
            ''')
            conn.commit()
    
    async def process(self, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract relevant information from chat history"""
        # Convert recent chat history to a format suitable for the LLM
        context = self._prepare_context(chat_history)
        
        # Create extraction prompt using proper chat message format
        user_prompt = f"Please analyze this conversation:\n{context}"
        
        # Get extraction from LLM using chat messages format
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        ai_response = response.generations[0][0].text
        
        # Parse the response into structured format
        extracted_info = self._parse_llm_response(ai_response)
        
        # Save extracted information to database
        self._save_to_database(extracted_info, chat_history[-5:])  # Save with reference to recent messages
        
        print("Extracted Info:", extracted_info)  # For debugging
        return extracted_info
    
    def _save_to_database(self, extracted_info: Dict[str, List[str]], source_messages: List[Dict[str, str]]):
        """Save extracted information to the database"""
        # Create a string of message IDs that were analyzed
        source_msg_ids = ','.join([str(i) for i in range(len(source_messages))])  # Placeholder IDs for now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for category, items in extracted_info.items():
                for item in items:
                    cursor.execute(
                        'INSERT INTO extracted_information (category, item, source_messages) VALUES (?, ?, ?)',
                        (category, item, source_msg_ids)
                    )
            conn.commit()
    
    def _parse_llm_response(self, response: str) -> Dict[str, List[str]]:
        """Parse LLM response into structured format"""
        sections = {
            "cultural_topics": [],
            "user_interests": [],
            "questions": [],
            "personal_information": [],
            "commitments": []
        }
        
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if "Cultural Topics:" in line:
                current_section = "cultural_topics"
            elif "User Interests:" in line:
                current_section = "user_interests"
            elif "Questions:" in line:
                current_section = "questions"
            elif "Personal Information:" in line:
                current_section = "personal_information"
            elif "Commitments:" in line:
                current_section = "commitments"
            # Add items to current section
            elif line.startswith('- ') and current_section:
                item = line[2:].strip()  # Remove '- ' prefix
                if item:
                    sections[current_section].append(item)
        
        return sections
    
    def _prepare_context(self, chat_history: List[Dict[str, str]]) -> str:
        """Prepare chat history for LLM processing"""
        # For now, just take the last few messages
        recent_messages = chat_history[-5:]  # Last 5 messages
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])
        return context 
    
    def refresh_system_prompt(self):
        """Refresh the system prompt"""
        self.system_prompt = self.prompt_manager.get_prompt('information_extractor')
    
    async def process_chat_history(self, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process chat history and extract information"""
        # Refresh system prompt before processing
        self.refresh_system_prompt()
        
        # Prepare conversation context
        context = self._prepare_context(chat_history)
        
        # Create extraction prompt using proper chat message format
        user_prompt = f"Please analyze this conversation:\n{context}"
        
        # Get extraction from LLM using chat messages format
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        ai_response = response.generations[0][0].text
        
        # Parse the response into structured format
        extracted_info = self._parse_llm_response(ai_response)
        
        # Save extracted information to database
        self._save_to_database(extracted_info, chat_history[-5:])  # Save with reference to recent messages
        
        print("Extracted Info:", extracted_info)  # For debugging
        return extracted_info