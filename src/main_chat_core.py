"""Main chat core module for handling chat interactions."""

import os
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.prompt_manager import PromptManager
from src.core_initializer import CoreInitializer

class MainChatCore:
    """Core class for handling chat interactions."""
    
    def __init__(self):
        """Initialize MainChatCore with necessary components."""
        # Initialize prompt manager
        self.prompt_manager = PromptManager()
        
        # Get initial system prompt
        system_prompt = self.prompt_manager.get_prompt('main_chat')
        
        # Create chat prompt template
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Initialize chat history
        self.chat_history = []

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/chat.db'
        
        # Initialize components using CoreInitializer
        CoreInitializer.init_database(self.db_path)
        self.chat_history = CoreInitializer.load_chat_history(self.db_path)
        
        # Initialize LLM
        self.llm = CoreInitializer.init_llm()

        # Task manager will be initialized asynchronously in initialize()
        self.task_manager = None

    async def initialize(self):
        """Initialize async components."""
        if self.task_manager is None:
            self.task_manager = await CoreInitializer.init_task_manager()

    def update_system_prompt(self, new_prompt: str):
        """Update the system prompt in the database and refresh the chat template."""
        # Update the prompt in the database
        self.prompt_manager.set_prompt('main_chat', new_prompt)
        
        # Update the chat prompt template
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", new_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    def refresh_system_prompt(self):
        """Refresh the system prompt from the database and update chat template."""
        # Get current system prompt from database
        system_prompt = self.prompt_manager.get_prompt('main_chat')
        
        # Update the chat prompt template
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    def save_message(self, role, content):
        """Save a new message to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO messages (role, content) VALUES (?, ?)',
                         (role, content))
            conn.commit()
        
    def get_latest_instruction(self):
        """Fetch the latest unexecuted instruction from the database."""
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

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT is_enabled FROM feature_toggles WHERE feature_name = ?',
                (feature_name,)
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    async def process_message(self, message: str) -> str:
        """Process a message and return the response."""
        # Create HumanMessage from input
        human_message = HumanMessage(content=message)
        
        # Add message to chat history
        self.chat_history.append(human_message)
        
        # Only check for instructions if this isn't the first user message
        if len(self.chat_history) > 1:  # At least one previous exchange
            instruction = self.get_latest_instruction()
            if instruction:
                # Format message with instruction
                message_with_instruction = HumanMessage(content=f"{message}\n[System instruction: {instruction}]")
                self.chat_history[-1] = message_with_instruction
        
        # Format prompt with chat history and current message
        # For the first message, don't include any chat history to avoid double system prompt
        prev_messages = self.chat_history[:-1] if len(self.chat_history) > 1 else []
        messages = self.chat_prompt.format_messages(
            chat_history=prev_messages,  # Previous messages, empty for first message
            input=message  # Current message
        )
        
        # Get response from LLM using invoke instead of agenerate
        response = await self.llm.ainvoke(messages)
        ai_message = AIMessage(content=response.content)
        
        # Add response to chat history
        self.chat_history.append(ai_message)
        
        # Save to database
        self.save_message("human", message)
        self.save_message("ai", ai_message.content)

        # Add task to async manager if it's initialized
        if self.task_manager is not None:
            await self.task_manager.add_task(
                "process_chat",
                chat_history=self.chat_history
            )
        
        return ai_message.content