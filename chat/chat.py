import datetime
import os

# Fall back to our custom wrapper for Python 3.7
from chat.gemini_wrapper import GeminiModule as genai
print("Using custom Gemini wrapper for Python 3.7 compatibility")
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with the API key from .env
api_key = os.getenv("GOOGLE_API_KEY")
chat_model = os.getenv("CHAT_MODEL")

if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not found. Please check your .env file.")

if not chat_model:
    chat_model = os.getenv("chat_model")
    if not chat_model:
        chat_model = "gemini-2.0-flash"  # Fallback model if not specified
        print(f"Neither CHAT_MODEL nor chat_model not specified. Using fallback model: {chat_model}")

# Configure the Gemini API
genai.configure(key=api_key)

# Read the system prompt from file
SYSTEM_PROMPT_PATH = os.path.join("system_prompts", "system_prompt.txt")
SYSTEM_PROMPT_PREFLIGHT_PATH = os.path.join("system_prompts", "system_prompt_preflight.txt")
INJECTION_STRING_PATH = os.path.join("system_prompts", "injection_string.txt")

def get_system_prompt():
    """Read the system prompt from file. Returns a default if file doesn't exist."""
    try:
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
                print(f"Loaded system prompt from {SYSTEM_PROMPT_PATH}")
                return system_prompt
        else:
            default_prompt = "You are a helpful assistant in a chat application."
            print(f"System prompt file not found at {SYSTEM_PROMPT_PATH}. Using default prompt.")
            return default_prompt
    except Exception as e:
        print(f"Error reading system prompt: {e}. Using default prompt.")
        return "You are a helpful assistant in a chat application."

def get_system_prompt_preflight():
    """Read the system prompt from file. Returns a default if file doesn't exist."""
    try:
        if os.path.exists(SYSTEM_PROMPT_PREFLIGHT_PATH):
            with open(SYSTEM_PROMPT_PREFLIGHT_PATH, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
                print(f"Loaded system prompt from {SYSTEM_PROMPT_PREFLIGHT_PATH}")
                return system_prompt
        else:
            default_prompt = "You are a helpful assistant in a chat application."
            print(f"System prompt file not found at {SYSTEM_PROMPT_PREFLIGHT_PATH}. Using default prompt.")
            return default_prompt
    except Exception as e:
        print(f"Error reading system prompt: {e}. Using default prompt.")
        return "You are a helpful assistant in a chat application."

def get_injection_string():
    """Read the injection string from file. Returns an empty string if file doesn't exist."""
    try:
        if os.path.exists(INJECTION_STRING_PATH):
            with open(INJECTION_STRING_PATH, 'r', encoding='utf-8') as f:
                injection_string = f.read().strip()
                print(f"Loaded injection string from {INJECTION_STRING_PATH}")
                return injection_string
        else:
            print(f"Injection string file not found at {INJECTION_STRING_PATH}. Using empty string.")
            return ""
    except Exception as e:
        print(f"Error reading injection string: {e}. Using empty string.")
        return ""

class ChatProcessor:
    def __init__(self, socketio, db=None):
        """Initialize the chat processor with SocketIO instance and optional database."""
        self.socketio = socketio
        self.db = db
        self.chat_model = chat_model
        self.model = genai.GenerativeModel(chat_model)
        self.chat_sessions = {}  # Store chat sessions by user id/session
        self.system_prompt = get_system_prompt()
        self.system_prompt_preflight = get_system_prompt_preflight()
        self.injection_string = get_injection_string()
        print(f"ChatProcessor initialized with model: {chat_model}")
    
    def set_database(self, db):
        """Set the database instance."""
        self.db = db
    
    def process_message(self, message_data, message_history=None, injections=None):
        """
        Process a user message:
        - Send it to Google Gemini LLM with message history context
        - Get the LLM response
        - Send it back via the WebSocket
        
        Args:
            message_data (dict): The new message data
            message_history (list): The full history of messages for context
            injections (list): Available injections to apply
        """
        # Extract message content and other data
        user_message = message_data.get('message', '')
        timestamp = message_data.get('timestamp', datetime.datetime.now().isoformat())
        session_id = message_data.get('session_id', 'default')  # Use default if not provided
        
        # Initialize default values for mutable arguments
        if message_history is None:
            message_history = []
        if injections is None:
            injections = []
        
        try:
            # Get or create a chat session for this user
            chat_session = self._get_or_create_chat_session(session_id, withPreFlight=False)
            
            # Include relevant message history as context
            context = self._format_history_for_context(message_history)
            if context:
                # Include a summary of the conversation history for context if available
                print(f"Including {len(context.split('\n'))} messages of history for context")
            
            # Send message to Gemini and get response
            response = self._send_message_to_gemini(chat_session, user_message, timestamp, injections)
            
            # Log the processed message
            print(f"chat.py: received response from Gemini LLM: '{response['message'][:100]}...'")
            
            # Save to database if available
            if self.db:
                self.db.save_message(response)
            
            # Send the message back to all clients
            self.socketio.emit('message', response)
            
            return response
            
        except Exception as e:
            return self._handle_error(e, timestamp)
    
    def _get_or_create_chat_session(self, session_id, withPreFlight):
        """Get an existing chat session or create a new one for the given session ID."""
        if session_id not in self.chat_sessions:
            # Initialize chat with system prompt
            self.chat_sessions[session_id] = self.model.start_chat(
                history=[
                    {"role": "user", "parts": [self.system_prompt]},
                    {"role": "model", "parts": [self.system_prompt_preflight if withPreFlight else "Understood."]}
                ]
            )
            print(f"Created new chat session for session_id: {session_id} with system prompt")
        
        return self.chat_sessions[session_id]
    
    def _send_message_to_gemini(self, chat_session, user_message, timestamp, injections=None):
        """Send a message to Gemini and return the response."""
        # Check for any pending injections in the database
        pending_injections = []
        if self.db:
            pending_injections = self.db.get_injections(consumed=False)
        
        # Also include injections passed as parameter
        if injections is None:
            injections = []
        all_injections = pending_injections + [inj for inj in injections if not inj.get('consumed', False)]
        
        # Use the first unconsumed injection if available
        custom_injection = None
        if all_injections:
            custom_injection = all_injections[0]
            print(f"Using injection from {custom_injection.get('role', 'Unknown')}")
            
            # Mark as consumed in memory
            custom_injection['consumed'] = True
            
            # Mark as consumed in database if it has an ID
            if self.db and 'id' in custom_injection:
                self.db.mark_injection_consumed(custom_injection['id'])
        
        # Format message to include timestamp and injection string (with further instruction for the LLM)
        injection_content = custom_injection.get('injection', self.injection_string) if custom_injection else self.injection_string
        
        # Fix for Raspberry Pi: Ensure timestamp is compatible with datetime.fromisoformat
        try:
            formatted_time = datetime.datetime.fromisoformat(timestamp).strftime('%H:%M')
        except (ValueError, TypeError):
            # Fallback for invalid timestamp formats
            print(f"Warning: Invalid timestamp format '{timestamp}', using current time")
            formatted_time = datetime.datetime.now().strftime('%H:%M')
            
        formatted_message = f"[{formatted_time}] [System instruction: {injection_content}] \n\n {user_message}"
        print(f"Sending message to Gemini: '{formatted_message}'")
        
        # Send to Gemini
        gemini_response = chat_session.send_message(formatted_message)
        
        # Extract the text response
        llm_response_text = gemini_response.text
        
        # Check if the response starts with a timestamp pattern like "[18:41]" and remove it
        import re
        llm_response_text = re.sub(r'^\s*\[\d{1,2}:\d{1,2}\]\s*', '', llm_response_text)
        
        # Create a response message
        # Ensure proper timezone handling for Raspberry Pi compatibility
        try:
            current_time = datetime.datetime.now().replace(microsecond=0).isoformat()
        except Exception:
            # Simple fallback if the above doesn't work
            current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
        response = {
            'message': llm_response_text,
            'timestamp': current_time,
            'role': 'Chat-AI',
            'model': self.chat_model
        }
        
        return response
    
    def _handle_error(self, exception, timestamp):
        """Handle errors during message processing."""
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error processing message: {str(exception)}")
        print(error_trace)
        
        # Ensure proper timestamp format for Raspberry Pi compatibility
        try:
            current_time = datetime.datetime.now().replace(microsecond=0).isoformat()
        except Exception:
            # Simple fallback
            current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
        error_response = {
            'message': f"Sorry, I encountered an error: {str(exception)}. Please try again later.",
            'timestamp': current_time,
            'role': 'System',
            'error': True
        }
        
        # Save error to database if available
        if self.db:
            self.db.save_message(error_response)
        
        # Send the error message back to all clients
        self.socketio.emit('message', error_response)
        
        return error_response
    
    def _format_history_for_context(self, message_history):
        """Format the message history into a concise context summary.
        
        Args:
            message_history (list): Complete message history
            
        Returns:
            str: Formatted context string
        """
        if not message_history or len(message_history) < 2:
            return ""
            
        # Get the last 10 messages for context (excluding the current message)
        recent_history = message_history[-11:-1] if len(message_history) > 10 else message_history[:-1]
        
        # Format the history into a readable context
        context_lines = []
        for msg in recent_history:
            role = msg.get('role', 'Unknown')
            content = msg.get('message', '')
            context_lines.append(f"{role}: {content}")
            
        return "\n".join(context_lines)
        
if __name__ == "__main__":
    print("This file should not be run directly. Import it from app.py instead.")
