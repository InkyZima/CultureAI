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
from flask_cors import CORS  # Import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
import message_injector
import llm_invocation
from async_stuff import do_async_stuff
import streamlit_formatter

app = Flask(__name__)
CORS(app) # Enable CORS for all routes - important for local frontend to access backend

# Initialize LLM (replace with your actual API key)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key='AIzaSyDoIKnOZv7XHqfbHGeyG9YB3lq2OnSRFfU')

@app.route('/chat', methods=['POST'])
def chat():
    print('Received message.')
    user_message = request.json.get('message') # Get message from frontend
    # sanitize, reformat, handle errors, etc.
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    print('User message before injection: ', user_message)
    
    
    # -- business-logic relevant message injections
    # add (date)time, so that the LLM is aware at which time of day the user is writing
    user_message_injected = message_injector.inject_datetime(user_message)

    # System instruction injection: We check whether we want to inject a system message into / at the end of the user message, which will then be considered in the following llm invocation. This happens synchronously.
    user_message_injected = message_injector.inject_system_message(user_message_injected)

    # invoke the llm and do related taksks (save to db)
    llm_response = llm_invocation.invoke_llm(user_message_injected)

    do_async_stuff()

    return llm_response

@app.route('/chat_history', methods=['GET'])
def chat_history():

    history = llm_invocation.get_chat_history() # This fetches the history from memory. This is in langchain format
    formatted_history = streamlit_formatter.reformat_history(history)
    return jsonify({"history": formatted_history})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1') # Run Flask backend on port 5000