import gradio as gr
from src.main_chat_core import MainChatCore
import asyncio

async def create_app():
    chat_core = MainChatCore()
    print("Calling initialize()...")
    await chat_core.initialize()
    print("Initialize completed")
    
    async def user_message(message, history):
        # Process user message through MainChatCore
        response = await chat_core.process_message(message)
        return response
    
    # Create Gradio chat interface
    chat_interface = gr.ChatInterface(
        user_message,
        title="Cultural AI Companion",
        description="Your AI companion for cultural guidance and conversation.",
        theme="soft"
    )
    
    return chat_interface

if __name__ == "__main__":
    # Create and run the app in the event loop
    app = asyncio.run(create_app())
    # Now app is the actual chat interface, not a coroutine
    app.launch() 