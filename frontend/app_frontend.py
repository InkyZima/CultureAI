"""
This is the app frontend.
Responsibilities: Display information to the user. Allow the user to change settings and parameters.
The frontend is not responsible for any business logic or any reformatting of data other than for the purpose of diplaying it.
The frontend also does not enrich data received from the user. It just passes whatever the user passes.

# User experience logic:

Come to page first time OR for the first time this day:
Get a static greeting,
converse.

Come to page (refresh) later same day:
if last_user_message < 1 hour: 
    user just sees the chat_history
if last_user_message >= 1 hour: 
    user sees chat_history + welcome_back_message generated by llm (with inputs chat_history and injected system instruction "The user was away for a while and has now come back. Welcome them back.")
    OR
    handle it via async proactive messenger
converse.


"""

# streamlit run frontend_app.py

import streamlit as st
import requests  # To make HTTP requests to backend
import datetime

BACKEND_URL = "http://127.0.0.1:5000/"  # URL of your Flask backend

# --- Configure sidebar to be collapsed by default ---
st.set_page_config(initial_sidebar_state="collapsed")

st.title("CultureAI")


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


        print(llm_introduction_msg)
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

# load chat logic

first_time_here = chat_history_is_empty()
st.session_state.chat_history = []

if first_time_here:
    print("First time here.")
    display_introduction_static()
else:
    print("NOT first time here.")
    display_chat_history()
    if last_user_message_when() and last_user_message_when() >= 60: # user was away over one hour
        display_welcome_back()

user_message = st.chat_input("Say something")
if user_message:
    with st.chat_message("user"):
        st.markdown(user_message)

    # Send user message to backend API
    try:
        backend_response = requests.post(f"{BACKEND_URL}/chat", json={"message": user_message})
        backend_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        llm_response_data = backend_response.json()
        llm_response = llm_response_data.get('response', "Error: No response from backend")

        with st.chat_message("assistant"):
            st.markdown(llm_response)
        st.session_state.chat_history.append({"user_message": user_message, "llm_response": llm_response})

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {e}")
        llm_response = "Error communicating with backend."


with st.sidebar:
    st.header("Settings")
    st.write("Settings content managed by backend API...")
    # You can add settings widgets here in the sidebar later
    if st.button("Reset conversation"):
        try:
            reset_response = requests.get(f"{BACKEND_URL}/reset_conversation")
            reset_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            st.session_state.chat_history = []
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"Error resetting conversation: {e}")
    if st.button("Notification Test"):
        try:
            reset_response = requests.get(f"{BACKEND_URL}/notification_test")
            reset_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            st.error(f"Error resetting conversation: {e}")