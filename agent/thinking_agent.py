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

# Import placeholder handler for template processing
from .placeholder_handler import process_template

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
    
    def __init__(self, prompt_path: Optional[str] = None):
        """
        Initialize the ThinkingAgent with Google Generative AI client.
        
        Args:
            prompt_path (Optional[str]): Custom path to prompt template file.
                If None, uses the default agent_prompt.txt
        """
        # Configure the model
        self.model_name = THINKING_MODEL
        print(f"ThinkingAgent initialized with model: {self.model_name}")
        
        # Get tool specifications from the registry for reference
        self.tools_registry = tools_registry
        self.tool_specs = self.tools_registry.get_all_tool_specs()
        
        # Path to the system prompt template
        if prompt_path is None:
            self.prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "system_prompts", "agent_prompt.txt")
        else:
            self.prompt_path = prompt_path
    
    def process_message(self, custom_prompt: Optional[str] = None, custom_prompt_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process context information and determine whether to use a tool and which one.
        Returns a textual decision, not a JSON tool call.
        
        Args:
            custom_prompt (Optional[str]): Custom prompt text. If None, uses the template file
            custom_prompt_path (Optional[str]): Path to a custom prompt template file.
                Overrides self.prompt_path and is used only if custom_prompt is None.
                
        Returns:
            Dict[str, Any]: A dictionary containing the decision text and metadata
        """
        try:
            # If custom prompt is not provided, read and format the template
            if custom_prompt is None:
                # If custom_prompt_path is provided, update self.prompt_path temporarily
                original_prompt_path = self.prompt_path
                if custom_prompt_path is not None:
                    self.prompt_path = custom_prompt_path
                
                # Prepare the prompt from the template
                prompt = self._prepare_prompt_from_template()
                
                # Restore the original prompt path if it was temporarily changed
                if custom_prompt_path is not None:
                    self.prompt_path = original_prompt_path
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
        Read the prompt template from file and process all placeholders.
        
        Returns:
            str: The formatted prompt with all placeholders replaced
        """
        try:
            # Read the template
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Process the template using the placeholder handler
            formatted_prompt = process_template(template)
            
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
    # Test code that runs when this module is executed directly
    agent = ThinkingAgent()
    decision = agent.process_message()
    print(f"Decision: {decision['decision']}")
