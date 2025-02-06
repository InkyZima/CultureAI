from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sqlite3
from dotenv import load_dotenv

class ConversationAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Initialize database connection
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        self.init_database()
        
        # Initialize smaller LLM for conversation analysis
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # Faster model for conversation analysis
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4  # Balanced temperature for analysis
        )
    
    def init_database(self):
        """Initialize the database table for conversation analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    engagement_level TEXT NOT NULL,
                    cultural_learning TEXT,
                    guidance_needed TEXT,
                    suggested_topics TEXT,
                    analyzed_messages TEXT  -- Store IDs of analyzed messages
                )
            ''')
            conn.commit()
    
    async def process(self, chat_history: List[Dict[str, str]], extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation using chat history and extracted information"""
        # Prepare context from chat history and extracted info
        context = self._prepare_context(chat_history, extracted_info)
        
        # Create analysis prompt
        prompt = f"""Analyze this conversation and extracted information. Consider:
1. Conversation quality and engagement level (high/medium/low)
2. Cultural learning progress - list specific cultural topics or concepts learned
3. Areas where cultural guidance might be needed - list specific areas
4. Potential topics for proactive discussion - list specific topics

Format your response exactly like this:
Engagement Level: [level]
Cultural Learning:
- [learning point 1]
- [learning point 2]
Guidance Needed:
- [area 1]
- [area 2]
Suggested Topics:
- [topic 1]
- [topic 2]

Context:
{context}"""
        
        # Get analysis from LLM
        response = await self.llm.ainvoke(prompt)
        
        # Parse response into structured format
        analysis = self._parse_llm_response(response.content)
        
        # Store analysis in database
        self._save_to_database(analysis, chat_history)
        
        return analysis
    
    def _prepare_context(self, chat_history: List[Dict[str, str]], extracted_info: Dict[str, Any]) -> str:
        """Prepare context for LLM processing"""
        # Combine recent chat history and extracted info
        recent_messages = chat_history[-5:]  # Last 5 messages
        chat_context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent_messages
        ])
        
        info_context = f"""
Extracted Information:
- Cultural Topics: {', '.join(extracted_info['cultural_topics'])}
- User Interests: {', '.join(extracted_info['user_interests'])}
- Questions: {', '.join(extracted_info['questions'])}
- Commitments: {', '.join(extracted_info['commitments'])}
"""
        
        return f"{chat_context}\n\n{info_context}" 
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        lines = response.strip().split('\n')
        analysis = {
            "engagement_level": "medium",
            "cultural_learning": [],
            "guidance_needed": [],
            "suggested_topics": []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('Engagement Level:'):
                analysis['engagement_level'] = line.split(':')[1].strip().lower()
            elif line.startswith('Cultural Learning:'):
                current_section = 'cultural_learning'
            elif line.startswith('Guidance Needed:'):
                current_section = 'guidance_needed'
            elif line.startswith('Suggested Topics:'):
                current_section = 'suggested_topics'
            elif line.startswith('- ') and current_section:
                analysis[current_section].append(line[2:])
        
        return analysis
    
    def _save_to_database(self, analysis: Dict[str, Any], chat_history: List[Dict[str, str]]):
        """Save analysis results to the database"""
        # Create a string of message IDs that were analyzed
        analyzed_msgs = ','.join([str(i) for i in range(len(chat_history))])  # Placeholder IDs for now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_analysis 
                (engagement_level, cultural_learning, guidance_needed, suggested_topics, analyzed_messages)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                analysis['engagement_level'],
                '\n'.join(analysis['cultural_learning']),
                '\n'.join(analysis['guidance_needed']),
                '\n'.join(analysis['suggested_topics']),
                analyzed_msgs
            ))
            conn.commit()