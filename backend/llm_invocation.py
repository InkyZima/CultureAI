"""
This code contains the chat llm invocation logic. It is used by the Flask API server. For data persistence, sqlite is used.
"""


from flask import jsonify
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
import db_utils # Import the db_utils.py file

logging.basicConfig(level=logging.WARNING)

load_dotenv()

# Initialize LLM (replace with your actual API key)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.environ.get("GOOGLE_API_KEY"))


db_utils.create_table() # Run on startup to ensure table exists
history = db_utils.load_history() # load history on startup


def get_chat_history():
    return history

def save_history(history):
    db_utils.save_history(history) # Use the save_history function from db_utils

def invoke_llm(user_message_injected):
    """Invokes the llm with the user message and does related tasks (such as save chat history to db).
    """
    try:
        user_message_1 = HumanMessage(content=user_message_injected)
        history.append(HumanMessage(content=user_message_injected))
        ai_response_1 = llm.invoke(history)
        history.append(ai_response_1)
        save_history(history) # Use the save_history function from db_utils
        return jsonify({"response": ai_response_1.content})
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return jsonify({"error": f"Error generating response: {e}"}), 500