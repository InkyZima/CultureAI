import asyncio
from typing import Dict, Any, Optional
from .information_extractor import InformationExtractor
from .conversation_analyzer import ConversationAnalyzer
from .instruction_generator import InstructionGenerator
from langchain.schema import HumanMessage, AIMessage
import sqlite3

class AsyncTaskManager:
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.info_extractor = InformationExtractor()
        self.conv_analyzer = ConversationAnalyzer()
        self.instr_generator = InstructionGenerator()
        self.db_path = 'data/chat.db'
        
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT is_enabled FROM feature_toggles WHERE feature_name = ?',
                (feature_name,)
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    async def start(self):
        """Start the task worker"""
        asyncio.create_task(self._worker())
    
    async def _worker(self):
        """Process tasks from the queue"""
        print("Worker started and waiting for tasks...")
        while True:
            task = await self.task_queue.get()
            print(f"Worker received task: {task['type']}")
            try:
                if task["type"] == "process_chat":
                    print("Converting messages to chat history...")
                    # Convert LangChain messages to dict format for extractor
                    chat_history = []
                    for msg in task["chat_history"]:
                        if isinstance(msg, (HumanMessage, AIMessage)):
                            role = "user" if isinstance(msg, HumanMessage) else "assistant"
                            chat_history.append({
                                "role": role,
                                "content": msg.content
                            })
                    
                    print(f"Processing {len(chat_history)} messages...")
                    await self._process_chat_history(chat_history)
            except Exception as e:
                print(f"Error processing task: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                self.task_queue.task_done()
    
    async def _process_chat_history(self, chat_history: list):
        """Process chat history through the async modules"""
        # Print just the last few messages for debugging
        print("\nProcessing recent messages:")
        for msg in chat_history[-3:]:  # Show last 3 messages
            print(f"- {msg['role']}: {msg['content'][:50]}...")  # Truncate long messages
        
        # Extract information first if enabled
        extracted_info = {}
        if self.is_feature_enabled('information_extractor'):
            extracted_info = await self.info_extractor.process(chat_history)
            print("\nExtracted info:")
            for category, items in extracted_info.items():
                if items:  # Only show non-empty categories
                    print(f"- {category}:", items)
        
        # Then analyze conversation using extracted info if enabled
        analysis = {}
        if self.is_feature_enabled('conversation_analyzer'):
            analysis = await self.conv_analyzer.process(chat_history, extracted_info)
        
        # Generate instructions based on conversation analysis if enabled
        if self.is_feature_enabled('instruction_generator'):
            await self.instr_generator.process_user_triggered(chat_history, analysis)
        
        # TODO: Remove this line after instruction generation is implemented
        # return analysis
    
    async def add_task(self, task_type: str, **kwargs):
        """Add a task to the queue"""
        print(f"\nAdding task: {task_type}")
        await self.task_queue.put({"type": task_type, **kwargs}) 