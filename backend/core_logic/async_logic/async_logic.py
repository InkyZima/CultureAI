"""
This file contains all async logic, i.e. everything that runs async of the main chat conversation logic between user and llm 
"""

import threading
import time
import os
import sys
from pathlib import Path
import sqlite3

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from backend.utils.db_utils import load_history
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from utils.db_utils import save_injection_message

load_dotenv()

# Initialize LLM (replace with your actual API key)
llm = ChatGoogleGenerativeAI(
  model="gemini-2.0-flash", 
  google_api_key=os.environ.get("GOOGLE_API_KEY"), 
  temperature=0,
  top_p=0.95,
  top_k=40,
  max_output_tokens=8192
)

def check_for_secondary_objectives(template_name):
    thread = threading.Thread(target=check_for_secondary_objectives_logic, args=(template_name,)) # Create a thread
    thread.daemon = True
    thread.start() # Start the thread

def check_for_secondary_objectives_logic(template_name):
    """
    Analyzes conversation history and suggests next actions based on secondary objectives.
    
    Args:
        template_name: Name of the template to use for secondary objectives
        
    Returns:
        str: Suggested next action for the AI assistant
    """
    # Get conversation history from the database
    conversation_history = load_history()
    
    # Convert history to a formatted string for the prompt
    history_str = "\n".join([
        f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"Assistant: {msg.content}"
        for msg in conversation_history
    ])
    
    # Read the system prompt template
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
              'prompt_templates', 'secondary_objectives.txt'), 'r') as f:
        system_prompt_template = f.read()
    
    # Read the objectives file
    objectives_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'prompt_templates', template_name, f'{template_name}_secondary.txt')
    with open(objectives_path, 'r') as f:
        objectives = f.read()
    
    # Create the prompt
    prompt = PromptTemplate(
        input_variables=["conversation_history", "objectives"],
        template=system_prompt_template
    )
    
    # Format the prompt with the conversation history and objectives
    formatted_prompt = prompt.format(
        conversation_history=history_str,
        objectives=objectives
    )
    
    try:
        # Invoke the LLM using langchain
        result = llm.invoke(formatted_prompt)
        save_injection_message(result.content)
        return result.content
    except Exception as e:
        print(f"Error in secondary objectives: {e}")
    

    

def do_async_stuff():
    """Does all the other async stuff concurrently to the main chat flow.
    
    
    Creates system instructions to be injected into user messages, based on: 
        Current time + 
        Analysis of current chat conversation + 
        static chat objectives list.  
    """
    thread = threading.Thread(target=check_for_secondary_objectives, args=(os.environ.get("DEFAULT_PROMPT_TEMPLATE"),)) # Create a thread
    thread.daemon = True
    thread.start() # Start the thread

def background_loop_logic():
    print("Hello from background_loop_logic.")
    return True

def background_loop(interval_minutes):
    while True:
        background_loop_logic()
        time.sleep(interval_minutes * 60)

def run_background_loop(interval_minutes=os.environ.get("RUN_EVERY_X_MINUTES")):
    if interval_minutes is None:
        interval_minutes = 30
    thread = threading.Thread(target=background_loop, args=(interval_minutes,))
    thread.daemon = True
    thread.start()
