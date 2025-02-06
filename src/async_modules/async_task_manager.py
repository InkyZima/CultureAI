import asyncio
from typing import Dict, Any, Optional
from .information_extractor import InformationExtractor
from .conversation_analyzer import ConversationAnalyzer
from langchain.schema import HumanMessage, AIMessage

class AsyncTaskManager:
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.info_extractor = InformationExtractor()
        self.conv_analyzer = ConversationAnalyzer()
        
    async def start(self):
        """Start the task worker"""
        asyncio.create_task(self._worker())
    
    async def _worker(self):
        """Process tasks from the queue"""
        while True:
            task = await self.task_queue.get()
            try:
                if task["type"] == "process_chat":
                    # Convert LangChain messages to dict format for extractor
                    chat_history = []
                    for msg in task["chat_history"]:
                        if isinstance(msg, (HumanMessage, AIMessage)):
                            role = "user" if isinstance(msg, HumanMessage) else "assistant"
                            chat_history.append({
                                "role": role,
                                "content": msg.content
                            })
                    
                    await self._process_chat_history(chat_history)
            except Exception as e:
                print(f"Error processing task: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                self.task_queue.task_done()
    
    async def _process_chat_history(self, chat_history: list):
        """Process chat history through the async modules"""
        print("\nProcessing chat history:", chat_history)  # Debug print
        # Extract information first
        extracted_info = await self.info_extractor.process(chat_history)
        print("\nExtracted info:", extracted_info)  # Debug print
        
        # Then analyze conversation using extracted info
        analysis = await self.conv_analyzer.process(chat_history, extracted_info)
        
        # TODO: Generate instructions based on analysis
        return analysis
    
    async def add_task(self, task_type: str, **kwargs):
        """Add a task to the queue"""
        print(f"Adding task: {task_type} with kwargs: {kwargs}")
        await self.task_queue.put({"type": task_type, **kwargs}) 