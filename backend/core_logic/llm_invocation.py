"""
This code contains the chat llm invocation logic. It is used by the Flask API server. For data persistence, sqlite is used.
"""


from flask import jsonify
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import os
from dotenv import load_dotenv
from utils import db_utils # Import the db_utils.py file
import core_logic.prompt_template_manager as prompt_template_manager # Import the prompt template manager

logging.basicConfig(level=logging.WARNING)

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


db_utils.create_tables() # Run on startup to ensure table exists
history = db_utils.load_history() # load history on startup
prompt_templates = prompt_template_manager.prompt_templates # Load prompt templates


def get_chat_history():
    return db_utils.load_history()


def get_chat_history_today():
    return db_utils.load_history_today()

def save_history(history):
    db_utils.save_history(history) # Use the save_history function from db_utils

def invoke_llm(user_message, template_name, with_history=True, save_user_message=True):
    """Invokes the llm with the user message and does related tasks (such as save chat history to db).
    """
    print("User message: %s" % user_message)
    try:
        history = []
        history = db_utils.load_history() # if user deletes history, we need to fetch the update here, or else we would be stuck with the old history
        history.append(HumanMessage(content=user_message))

        prompt_template = prompt_template_manager.get_template_by_name(prompt_templates, template_name)

        if prompt_template:
            # Format the prompt template
            formatted_prompt = prompt_template.format()
            messages_for_llm = [SystemMessage(content=formatted_prompt)] # Use SystemMessage to incorporate the prompt
            messages_for_llm.extend(history) # Append chat history
            ai_response = llm.invoke(messages_for_llm)
        else:
            # Fallback to no prompt template if default is not found
            ai_response = llm.invoke(history)
        if not save_user_message:
            history.pop()
        history.append(ai_response)
        save_history(history) # Use the save_history function from db_utils
        return jsonify({"response": ai_response.content})
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return jsonify({"error": f"Error generating response: {e}"}), 500