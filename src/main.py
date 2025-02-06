import gradio as gr
from src.main_chat_core import MainChatCore

def create_app():
    chat_core = MainChatCore()
    
    def user_message(message, history):
        # Process user message through MainChatCore
        response = chat_core.process_message(message)
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
    app = create_app()
    app.launch() 