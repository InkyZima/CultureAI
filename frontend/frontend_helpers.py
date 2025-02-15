import datetime
import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:5000/"  # URL of your Flask backend

def chat_history_is_empty():
    try:
        history_response = requests.get(f"{BACKEND_URL}/chat_history_today")
        if history_response.status_code == 200:
            if len(history_response.json().get('history')) > 0:
                print("Chat history today NOT empty.")
                return False
            else:
                return True
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load chat history from backend: {e}")

def display_introduction_static():
    # Display cultureAI introduction. Static introduction just returns the <culture>_intro.txt, while non-static/default returns a llm response (to the prompt "Please introduce yourself.")
    try:
        llm_introduction = requests.get(f"{BACKEND_URL}/introduction_static")
        llm_introduction = llm_introduction.json().get('introduction')
        if llm_introduction is not None:
            with st.chat_message("assistant"):
                st.markdown(llm_introduction)
    except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with backend: {e}")
            llm_introduction = "Error communicating with backend."

# TODO
def display_introduction_dynamic():
    # Display cultureAI introduction. Static introduction just returns the <culture>_intro.txt, while non-static/default returns a llm response (to the prompt "Please introduce yourself.")
    try:
        llm_introduction = requests.get(f"{BACKEND_URL}/introduction")
        #llm_introduction = requests.get(f"{BACKEND_URL}/introduction")

        llm_introduction.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        llm_introduction_data = llm_introduction.json()
        llm_introduction_msg = llm_introduction_data.get('response', "Error: No response from backend")

        with st.chat_message("assistant"):
            st.markdown(llm_introduction_msg)
    except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with backend: {e}")
            llm_introduction_msg = "Error communicating with backend."


def display_chat_history():
    if len(st.session_state.chat_history) == 0:
        # Fetch initial chat history from backend when frontend starts
        try:
            history_response = requests.get(f"{BACKEND_URL}/chat_history")
            if history_response.status_code == 200:
                st.session_state.chat_history = history_response.json().get('history', [])
        except requests.exceptions.RequestException as e:
            st.error(f"Could not load chat history from backend: {e}")
    # Display chat history from session state
    for message_turn in st.session_state.chat_history:
        if 'user_message' in message_turn and message_turn['user_message']:
            with st.chat_message("user"):
                st.markdown(message_turn['user_message'])
        if 'llm_response' in message_turn and message_turn['llm_response']:
            with st.chat_message("assistant"):
                st.markdown(message_turn['llm_response'])

def last_user_message_when(): # history_response.json().get('timestamp')
    try:
        history_response = requests.get(f"{BACKEND_URL}/chat_history")
        if history_response.status_code == 200:
            history = history_response.json().get('history', [])
            now = datetime.datetime.now()
            last_message_timestamp = datetime.datetime.fromisoformat(history[-1]['timestamp'])
            time_diff = (now - last_message_timestamp).total_seconds() / 60
            print("Last message was %s minutes ago" % time_diff)
            return time_diff
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load chat history from backend: {e}")

def display_welcome_back():

    return ""
