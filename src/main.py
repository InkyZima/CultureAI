import gradio as gr
from src.main_chat_core import MainChatCore
from src.prompt_manager import PromptManager
import asyncio

async def create_app():
    chat_core = MainChatCore()
    prompt_manager = PromptManager()
    print("Initializing chat core...")
    await chat_core.initialize()
    print("Initialization completed")
    
    async def user_message(message, history):
        # Process user message through MainChatCore
        response = await chat_core.process_message(message)
        return response
    
    def load_prompt_settings():
        """Load all prompt settings for the UI"""
        modules = prompt_manager.list_modules()
        return [prompt_manager.get_prompt_info(module) for module in reversed(modules)]
    
    def save_prompt(module_name: str, new_prompt: str):
        """Save updated prompt and return success message"""
        try:
            prompt_manager.set_prompt(module_name, new_prompt)
            
            # Immediately refresh the prompt in the relevant module
            if module_name == 'main_chat':
                chat_core.refresh_system_prompt()
            elif module_name == 'instruction_generator' and chat_core.task_manager:
                chat_core.task_manager.instr_generator.refresh_system_prompt()
            elif module_name == 'information_extractor' and chat_core.task_manager:
                chat_core.task_manager.info_extractor.refresh_system_prompt()
            elif module_name == 'conversation_analyzer' and chat_core.task_manager:
                chat_core.task_manager.conv_analyzer.refresh_system_prompt()
            
            return f"Successfully updated prompt for {module_name}"
        except Exception as e:
            return f"Error updating prompt: {str(e)}"
    
    def reset_prompt(module_name: str):
        """Reset prompt to default and return the default prompt"""
        try:
            prompt_manager.reset_prompt(module_name)
            
            # Immediately refresh the prompt in the relevant module
            if module_name == 'main_chat':
                chat_core.refresh_system_prompt()
            elif module_name == 'instruction_generator':
                chat_core.task_manager.instruction_generator.refresh_system_prompt()
            elif module_name == 'information_extractor':
                chat_core.task_manager.information_extractor.refresh_system_prompt()
            elif module_name == 'conversation_analyzer':
                chat_core.task_manager.conversation_analyzer.refresh_system_prompt()
            
            return (f"Successfully reset prompt for {module_name}",
                   prompt_manager.get_prompt(module_name))
        except Exception as e:
            return f"Error resetting prompt: {str(e)}", None
    

    css = """
#chatbot { 
    flex-grow: 1 !important; 
    height: calc(100vh - 300px) !important; /* Adjust based on header/footer height */
    overflow: auto !important; 
}
"""

    # Create Gradio interface with tabs
    with gr.Blocks(css=css, theme="soft", fill_height=True) as interface:
        gr.Markdown("# Cultural AI Companion")
        
        with gr.Tabs():
            # Chat Tab
            with gr.Tab("Chat"):
                chat_interface = gr.ChatInterface(
                    user_message,
                    fill_height=True,
                    chatbot=gr.Chatbot(elem_id="chatbot", type="messages"),
                    type="messages"
                )
            
            # Settings Tab
            with gr.Tab("Settings"):
                gr.Markdown("## System Prompts")
                gr.Markdown("Edit the system prompts used by different components of the AI.")
                
                with gr.Accordion("Prompt Settings", open=False):
                    for module_info in load_prompt_settings():
                        with gr.Group():
                            gr.Markdown(f"### {module_info['module_name']}")
                            prompt_text = gr.Textbox(
                                value=module_info['prompt'],
                                label="Current Prompt",
                                lines=5
                            )
                            save_btn = gr.Button(f"Save {module_info['module_name']} Prompt")
                            status_text = gr.Textbox(label="Status")
                            save_btn.click(
                                save_prompt,
                                inputs=[gr.Textbox(value=module_info['module_name'], visible=False), prompt_text],
                                outputs=status_text
                            )
    
    return interface

if __name__ == "__main__":
    # Create and run the app in the event loop
    app = asyncio.run(create_app())
    # Now app is the actual interface, not a coroutine
    app.launch()