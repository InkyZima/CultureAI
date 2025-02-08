import os
import sqlite3
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
from src.prompt_manager import PromptManager

class InstructionGenerator:
    def __init__(self):
        load_dotenv()
        
        # Initialize database connection
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        self.init_database()
        
        # Initialize prompt manager and get system prompt
        self.prompt_manager = PromptManager()
        self.system_prompt = self.prompt_manager.get_prompt('instruction_generator')
        
        # Initialize smaller LLM for instruction generation
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # Faster model for instruction generation
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4  # Balanced temperature for instruction generation
        )
    
    def init_database(self):
        """Initialize the database table for generated instructions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trigger_type TEXT NOT NULL,  -- 'user' or 'timed'
                    instruction TEXT NOT NULL,
                    priority INTEGER NOT NULL,   -- 1 (high) to 5 (low)
                    context_messages TEXT NOT NULL,  -- IDs of messages that led to this instruction
                    executed BOOLEAN DEFAULT FALSE,  -- Whether this instruction has been executed
                    execution_time DATETIME     -- When the instruction was executed
                )
            ''')
            conn.commit()
    
    async def process_user_triggered(self, chat_history: List[Dict[str, str]], conversation_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process chat history and generate instructions based on user interaction"""
        # Refresh system prompt before processing
        self.refresh_system_prompt()
        
        # Format chat history for LLM
        formatted_history = "\n".join([
            f"{msg['role'].title()}: {msg['content']}"
            for msg in chat_history[-5:]  # Only use last 5 messages for context
        ])
        
        # Format conversation analysis
        analysis_str = "\n".join([
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in conversation_analysis.items()
        ])
        
        # Create prompt for instruction generation
        prompt = f"""Based on the following chat history and conversation analysis, generate 2-3 instructions for engaging with the user.
Each instruction should be specific, actionable, and culturally relevant.

Chat History:
{formatted_history}

Conversation Analysis:
{analysis_str}

Generate instructions in the following format:
Instructions:
- Instruction: [specific instruction]
  Priority: [1-5, where 5 is highest]
  Reason: [brief reason for this instruction]
"""
        
        # Generate instructions using LLM
        response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
        instructions = self._parse_llm_response(response.generations[0][0].text)
        
        # Save instructions to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for instr in instructions:
                cursor.execute('''
                    INSERT INTO generated_instructions 
                    (trigger_type, instruction, priority, context_messages, executed)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    'user',
                    instr['instruction'],
                    instr['priority'],
                    json.dumps({
                        'chat_history': chat_history[-5:],
                        'analysis': conversation_analysis,
                        'reason': instr.get('reason', '')
                    }),
                    False
                ))
        
        return instructions
    
    def _prepare_context(self, chat_history: List[Dict[str, str]], conversation_analysis: Dict[str, Any]) -> str:
        """Prepare chat history and analysis for LLM processing"""
        # Format chat history
        formatted_history = "\nChat History:\n"
        for msg in chat_history[-5:]:  # Only use last 5 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted_history += f"{role}: {content}\n"
        
        # Format conversation analysis
        analysis_str = "\nConversation Analysis:\n"
        for key, value in conversation_analysis.items():
            analysis_str += f"{key}: {value}\n"
        
        return formatted_history + analysis_str
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured format"""
        instructions = []
        current_instruction = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line or line == "Instructions:":
                continue
                
            if line.startswith('- Instruction'):
                if current_instruction:
                    instructions.append(current_instruction)
                # Extract instruction text, removing quotes and colons
                instruction_text = line.split(':', 1)[1].strip().strip('"\'')
                current_instruction = {'instruction': instruction_text}
            elif line.startswith('Priority') and current_instruction:
                try:
                    priority_text = line.split(':', 1)[1].strip()
                    current_instruction['priority'] = int(priority_text)
                except (ValueError, KeyError, IndexError):
                    current_instruction['priority'] = 3  # Default priority
            elif line.startswith('Reason') and current_instruction:
                reason_text = line.split(':', 1)[1].strip()
                current_instruction['reason'] = reason_text
        
        # Add the last instruction if present
        if current_instruction:
            instructions.append(current_instruction)
        
        return instructions
    
    def _save_to_database(self, instructions: List[Dict[str, Any]], trigger_type: str, chat_history: List[Dict[str, str]]):
        """Save generated instructions to the database"""
        # Create a string of message IDs that were analyzed
        context_msg_ids = ','.join([str(i) for i in range(len(chat_history))])  # Placeholder IDs for now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for instruction in instructions:
                cursor.execute('''
                    INSERT INTO generated_instructions 
                    (trigger_type, instruction, priority, context_messages) 
                    VALUES (?, ?, ?, ?)
                ''', (
                    trigger_type,
                    instruction['instruction'],
                    instruction['priority'],
                    context_msg_ids
                ))
            conn.commit()
    
    def refresh_system_prompt(self):
        """Refresh the system prompt"""
        self.system_prompt = self.prompt_manager.get_prompt('instruction_generator')
