"""
This code contains the chat llm invocation logic, with an alternative persistence (json file). It is used by the Flask API server. It is currently not in use (; sqlite persistence is used instead).
"""


from flask import jsonify
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
import json
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.WARNING)

load_dotenv()

# Initialize LLM (replace with your actual API key)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.environ.get("GOOGLE_API_KEY"))

history_file = "../data/conversation_history.json"


def load_history():
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            print(f)
            history_data = json.load(f)
            history = []
            for message_data in history_data:
                if message_data["type"] == "human":
                    history.append(HumanMessage(**message_data["data"]))
                elif message_data["type"] == "ai":
                    history.append(AIMessage(**message_data["data"]))
            return history
    return []

# load history on startup
history = load_history()

def get_chat_history():
    return history

def save_history(history):
    history_data = []
    for message in history:
        if isinstance(message, HumanMessage):
            history_data.append({"type": "human", "data": message.model_dump()})
        elif isinstance(message, AIMessage):
            history_data.append({"type": "ai", "data": message.model_dump()})
    logging.debug(f"history_data: {history_data}")
    with open(history_file, "w") as f:
        json.dump(history_data, f)
    logging.debug("history saved to file")

def invoke_llm(user_message_injected):
    """Invokes the llm with the user message and does related tasks (such as save chat history to db).
    """
    try:
        user_message_1 = HumanMessage(content=user_message_injected)
        history.append(HumanMessage(content=user_message_injected))
        ai_response_1 = llm.invoke(history)
        history.append(ai_response_1)
        save_history(history)
        return jsonify({"response": ai_response_1.content})
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return jsonify({"error": f"Error generating response: {e}"}), 500

