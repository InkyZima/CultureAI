"""
This code contains the chat llm invocation logic. It is used by the Flask API server. For data persistence, sqlite is used.
"""





from flask import jsonify
import logging
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from utils import db_utils # Import the db_utils.py file
import core_logic.prompt_template_manager as prompt_template_manager # Import the prompt template manager

logging.basicConfig(level=logging.WARNING)

load_dotenv()


client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


db_utils.create_table() # Run on startup to ensure table exists
history = db_utils.load_history() # load history on startup
prompt_templates = prompt_template_manager.prompt_templates # Load prompt templates

def with_model_config(template_name="Pirate"):
  prompt_template = prompt_template_manager.get_template_by_name(prompt_templates, template_name)
  model_config = types.GenerateContentConfig(
    system_instruction=prompt_template.template,
    temperature=0,
  )
  return model_config


def get_chat_history():
    return history

def save_history(history):
    db_utils.save_history(history) # Use the save_history function from db_utils

    
def invoke_llm(user_message, template_name=os.environ.get("DEFAULT_PROMPT_TEMPLATE")):
  """Invokes the llm with the user message and does related tasks (such as save chat history to db).
  """
  try:

    sample_contents=[
        types.Content(role='user', parts=[types.Part.from_text(text='Hi')]),
        types.Content(role='model', parts=[types.Part.from_text(text='Hi, how can i help you today?')]),
        types.Content(role='user', parts=[types.Part.from_text(text="What's the capital of France?")])
    ]

    print(get_chat_history())

    history.append(types.Content(role='user', parts=[types.Part.from_text(text=user_message)]))

    ai_response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=[get_chat_history(), types.Content(role='user', parts=[types.Part.from_text(text=user_message)])],
        config=with_model_config("Elementarist")
    )
    print(ai_response.text)
    
    # TODO use the rest of this object for logging / observability
    save_to_history()

    return jsonify({"response": ai_response.text})
  except Exception as e:
    logging.error(f"Error generating response: {e}")
    return jsonify({"error": f"Error generating response: {e}"}), 500