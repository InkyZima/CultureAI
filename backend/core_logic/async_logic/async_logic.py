"""
This file contains all async logic, i.e. everything that runs async of the main chat conversation logic between user and llm 
"""

import threading
import time
import os
import sys
from pathlib import Path
import sqlite3
from core_logic.llm_invocation import invoke_llm
from core_logic.async_logic.notification_manager import send_notification
import datetime

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
from utils.streamlit_formatter import reformat_history

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

def check_for_secondary_objectives(template_name,system_prompt):
    thread = threading.Thread(target=check_for_secondary_objectives_logic, args=(template_name,system_prompt,)) # Create a thread
    thread.daemon = True
    thread.start() # Start the thread

def check_for_secondary_objectives_logic(template_name, system_prompt):
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
              'prompt_templates', system_prompt), 'r') as f:
        system_prompt_template = f.read()
    
    # Read the objectives file
    objectives_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'prompt_templates', template_name, f'{template_name}_secondary.txt')
    objectives = ""
    if os.path.exists(objectives_path):
        with open(objectives_path, 'r') as f:
            objectives = f.read()
        
    # Create the prompt
    if system_prompt == 'secondary_objectives.txt':
        prompt = PromptTemplate(
            input_variables=["conversation_history", "objectives"],
            template=system_prompt_template
        )
            # Format the prompt with the conversation history and objectives
        formatted_prompt = prompt.format(
            conversation_history=history_str,
            objectives=objectives
        )
    elif system_prompt == 'background_loop.txt':
        prompt = PromptTemplate(
            input_variables=["conversation_history", "objectives", "current_time", "last_user_message_minutes"],
            template=system_prompt_template
        )
        now = datetime.datetime.now()
        formatted_history = reformat_history(conversation_history)
        last_message_timestamp = datetime.datetime.fromisoformat(formatted_history[-1]['timestamp'])
        time_diff = (now - last_message_timestamp).total_seconds() / 60
        formatted_prompt = prompt.format(
            conversation_history=history_str,
            objectives=objectives,
            current_time=now.strftime("%H:%M"),
            last_user_message_minutes=time_diff
        )

    
    try:
        # Invoke the LLM using langchain
        result = llm.invoke(formatted_prompt)
        if system_prompt == 'secondary_objectives.txt':
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
    thread = threading.Thread(target=check_for_secondary_objectives, args=(os.environ.get("DEFAULT_PROMPT_TEMPLATE"),"secondary_objectives.txt")) # Create a thread
    thread.daemon = True
    thread.start() # Start the thread



def background_loop_logic():
    print("Hello from background_loop_logic.")
    llm_response = check_for_secondary_objectives_logic(template_name=os.environ.get("DEFAULT_PROMPT_TEMPLATE"), system_prompt='background_loop.txt')
    decision, instruction = llm_response.split(": ", 1)
    decision = True if decision == "Yes" else False
    print("LLM response: %s" % llm_response)
    if decision:
        print("Background loop decided to prompt the user.")
        formatted_instruction = "[System instruction: " + instruction + "]"
        # result = invoke Elementarist with Elementarist system prompt and user_message = [System instruction]. save only the resulting AI message to db.
        template_llm_answer = invoke_llm(formatted_instruction, os.environ.get("DEFAULT_PROMPT_TEMPLATE"), with_history=True, save_user_message=False)
        print("template_llm_answer: %s" % str(template_llm_answer))
        send_notification(template_llm_answer.json().response)
    else:
        print("Background loop decided NOT to prompt the user.")
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
