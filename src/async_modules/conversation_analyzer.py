from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

class ConversationAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Initialize smaller LLM for conversation analysis
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # Faster model for conversation analysis
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4  # Balanced temperature for analysis
        )
    
    async def process(self, chat_history: List[Dict[str, str]], extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation using chat history and extracted information"""
        # Prepare context from chat history and extracted info
        context = self._prepare_context(chat_history, extracted_info)
        
        # Create analysis prompt
        prompt = f"""Analyze this conversation and extracted information. Consider:
1. Conversation quality and engagement level
2. Cultural learning progress
3. Areas where cultural guidance might be needed
4. Potential topics for proactive discussion

Context:
{context}

Provide analysis in a structured format."""
        
        # Get analysis from LLM
        response = await self.llm.ainvoke(prompt)
        
        # TODO: Parse response into structured format
        analysis = {
            "engagement_level": "medium",
            "cultural_learning": [],
            "guidance_needed": [],
            "suggested_topics": []
        }
        
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