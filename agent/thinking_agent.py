import datetime
import os
import json
from typing import Dict, Any, Optional

import google.generativeai as genai
from dotenv import load_dotenv

# Import database for accessing message and injection history
try:
    from database import MessageDatabase
    db = MessageDatabase()
except ImportError:
    # When running from a test script in a different directory
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import MessageDatabase
    db = MessageDatabase()

# Import tools registry to get available tools
from .tools.tools_registry import tools_registry

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with the API key from .env
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")

# Use a thinking-specialized model if available, otherwise fallback
THINKING_MODEL = os.getenv("THINKING_MODEL", "gemini-2.0-flash")

# Configure the Gemini API
genai.configure(api_key=api_key)

class ThinkingAgent:
    """
    Agent that analyzes the context and decides if and which tool to use, 
    returning a textual description of its decision rather than a JSON object.
    """
    
    def __init__(self):
        """Initialize the ThinkingAgent with Google Generative AI client."""
        # Configure the model
        self.model_name = THINKING_MODEL
        print(f"ThinkingAgent initialized with model: {self.model_name}")
        
        # Get tool specifications from the registry for reference
        self.tools_registry = tools_registry
        self.tool_specs = self.tools_registry.get_all_tool_specs()
        
        # Path to the system prompt template
        self.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "system_prompts", "agent_prompt.txt")
    
    def process_message(self, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Process context information and determine whether to use a tool and which one.
        Returns a textual decision, not a JSON tool call.
        
        Args:
            custom_prompt (Optional[str]): Custom prompt text. If None, uses agent_prompt.txt
            
        Returns:
            Dict[str, Any]: A dictionary containing the decision text and metadata
        """
        try:
            # If custom prompt is not provided, read and format the template from agent_prompt.txt
            if custom_prompt is None:
                prompt = self._prepare_prompt_from_template()
            else:
                prompt = custom_prompt
            
            # Create a timestamp for logging
            timestamp = datetime.datetime.now().isoformat()
            
            # Append specific thinking instructions to the prompt
            thinking_instructions = """
            Based on the above context, decide if you should use a tool, and if so, which one.
            
            Your response should be in the following format:
            - If you decide NOT to use any tool: "No: I don't need to use any tools at this moment because [reason]"
            - If you decide to use the inject_instruction tool: "Yes: Call the inject_instruction tool with instruction '[your instruction text]' because [reason]"
            - If you decide to use the send_notification tool: "Yes: Call the send_notification tool with message '[your notification text]' because [reason]"
            
            Only return this specific format without any additional text, preamble, or explanation.
            """
            
            full_prompt = f"{prompt}\n\n{thinking_instructions}"
            
            # Log the thinking prompt (for debugging)
            # print(f"Thinking prompt: {full_prompt}")
            
            # Call the model to make a decision
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(full_prompt)
            
            # Extract the decision text
            decision_text = None
            try:
                decision_text = response.text.strip()
            except (ValueError, AttributeError) as e:
                print(f"Warning: Could not extract text from thinking response: {e}")
                decision_text = "No: I couldn't determine if a tool is needed due to an error in processing."
            
            # Log the thinking process
            self._log_thinking_process(timestamp, full_prompt, decision_text)
            
            return {
                "decision": decision_text,
                "timestamp": timestamp
            }
            
        except Exception as e:
            # Log the error
            error_message = f"Error in thinking agent: {str(e)}"
            print(f"Error: {error_message}")
            import traceback
            print(traceback.format_exc())
            
            return {
                "decision": "No: I encountered an error while trying to make a decision.",
                "error": error_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def _prepare_prompt_from_template(self) -> str:
        """
        Read the prompt template from file and fill in the placeholders.
        
        Returns:
            str: The formatted prompt
        """
        try:
            # Read the template
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                message_template = f.read()
            
            # Get chat history from database and format it
            messages = db.get_messages(limit=20)  # Get last 20 messages
            messages.reverse()  # Display in chronological order
            
            chat_history_str = ""
            for msg in messages:
                role = msg.get('role', '')
                text = msg.get('message', '')
                timestamp = msg.get('timestamp', '')
                # Format with timestamp if available
                if timestamp:
                    chat_history_str += f"[{timestamp}] {role}: {text}\n\n"
                else:
                    chat_history_str += f"{role}: {text}\n\n"
            
            # Replace the {chat_history} placeholder
            if not chat_history_str:
                chat_history_str = "No chat history available yet."
            
            # Get unconsumed injections from database and format them
            injections = db.get_injections(consumed=False)
            unconsumed_injections_str = ""
            for injection in injections:
                instruction = injection.get('injection', '')
                timestamp = injection.get('timestamp', '')
                if timestamp and instruction:
                    unconsumed_injections_str += f"[{timestamp}] {instruction}\n"
            
            # Replace the {unconsumed_injections} placeholder
            if not unconsumed_injections_str:
                unconsumed_injections_str = "No pending instructions."
            
            # Replace all placeholders in the template
            current_time = datetime.datetime.now().isoformat()
            formatted_prompt = message_template.replace("{chat_history}", chat_history_str)
            formatted_prompt = formatted_prompt.replace("{unconsumed_injections}", unconsumed_injections_str)
            formatted_prompt = formatted_prompt.replace("{timestamp}", current_time)
            
            return formatted_prompt
            
        except Exception as e:
            print(f"Error preparing prompt from template: {e}")
            # Return a minimalistic fallback prompt if there's an error
            return "You are an agent that decides whether to use tools based on context."
    
    def _log_thinking_process(self, timestamp: str, prompt: str, decision: str) -> None:
        """
        Log the thinking process for debugging and analysis.
        
        Args:
            timestamp (str): ISO-formatted timestamp
            prompt (str): The prompt sent to the model
            decision (str): The decision text returned by the model
        """
        try:
            # We can add database logging here if needed
            print(f"[{timestamp}] Thinking decision: {decision}")
        except Exception as e:
            print(f"Error logging thinking process: {e}")


if __name__ == "__main__":
    print("This file should not be run directly. Import it from agent_chain.py instead.")
