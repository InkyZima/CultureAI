"""
This is the API server. Pre-processing data coming from the front-end to be properly formatted for langchain shall be moved to an extra file at a later point.
/chat: 
    user messages shall be injected with further system instructions; the logic for that shall be in another file.
    Langchain shall handle the llm invocation, memory management, context (window) management.
    After llm invocation, dispatch a "process_chat" task to the async task processor to do further backend stuff (asynchonously)
    return the llm response. 

/chat_history:

"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
import core_logic.message_injector as message_injector
import core_logic.llm_invocation as llm_invocation
from core_logic.async_logic.async_logic import check_for_secondary_objectives, background_loop_logic
from utils import streamlit_formatter
import os
from dotenv import load_dotenv
from core_logic.async_logic.notification_manager import send_notification
from socket_instance import app, socketio, get_socketio_instance
# Remove the Flask and SocketIO initialization code
# Keep the rest of the imports and code the same

import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING) # Or logging.CRITICAL to suppress more logs

app = Flask(__name__)
app.config['SECRET_KEY'] = '$%#^hgf*&(&)'
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins="*")

load_dotenv(override=True)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.environ.get("GOOGLE_API_KEY"))

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message_from_backend', {'data': 'Connected to server'}) # Send message on connection

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/chat', methods=['POST'])
def chat():
    print('Received message.')
    user_message = request.json.get('message') # Get message from frontend
    # sanitize, reformat, handle errors, etc.
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # -- business-logic relevant message injections
    # add (date)time, so that the LLM is aware at which time of day the user is writing
    user_message_injected = message_injector.inject_datetime(user_message)

    history = llm_invocation.get_chat_history()
    formatted_history = streamlit_formatter.reformat_history(history)

    if len(formatted_history) % 8 == 6:
        check_for_secondary_objectives(os.environ.get("DEFAULT_PROMPT_TEMPLATE"),"secondary_objectives.txt")

    # System instruction injection: We check whether we want to inject a system message into / at the end of the user message, which will then be considered in the following llm invocation. This happens synchronously.
    if not len(formatted_history) < 2  and len(formatted_history) % 8 == 0:
        user_message_injected = message_injector.inject_system_message(user_message_injected)

    print('User message after injection: ', user_message_injected)

    # invoke the llm and do related taksks (save to db)
    llm_response = llm_invocation.invoke_llm(user_message_injected, os.environ.get("DEFAULT_PROMPT_TEMPLATE"))


    return llm_response

@app.route('/chat_history', methods=['GET'])
def chat_history():
    from utils.db_utils import load_history
    chat_history = load_history()
    formatted_history = streamlit_formatter.reformat_history(chat_history)
    return jsonify({"history": formatted_history})

@app.route('/chat_history_today', methods=['GET'])
def chat_history_today():
    from utils.db_utils import load_history_today
    chat_history_today = load_history_today()
    formatted_history = streamlit_formatter.reformat_history(chat_history_today)
    return jsonify({"history": formatted_history})

@app.route('/reset_conversation', methods=['GET'])
def reset_conversation():
    from utils.db_utils import clear_history
    clear_history()
    return jsonify({"message": "Conversation reset successfully."}), 200
    
@app.route('/introduction', methods=['GET'])
def introduction():
    llm_response = llm_invocation.invoke_llm("Please introduce yourself.", os.environ.get("DEFAULT_PROMPT_TEMPLATE"), with_history=True)
    return llm_response   


@app.route('/notification_test', methods=['GET'])
def notification_test():
    socketio.emit('message_from_backend', {'data': "notification_test websocket emission."})
    background_loop_logic()
    return jsonify({"message": "Notification test successful."}), 200

@app.route('/introduction_static', methods=['GET'])
def introduction_static():
    template_name = os.environ.get("DEFAULT_PROMPT_TEMPLATE")

    from core_logic.prompt_template_manager import get_template_introduction
    template_introduction = get_template_introduction(template_name)

    return jsonify({"introduction": template_introduction}), 200

def get_socketio_instance():
    if socketio:
        return socketio
    else:
        return None

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='127.0.0.1') # Run Flask backend on port 5000

    