"""
This is the app frontend.
Responsibilities: Display information to the user. Allow the user to change settings and parameters.
The frontend is not responsible for any business logic or any reformatting of data other than for the purpose of diplaying it.
The frontend also does not enrich data received from the user. It just passes whatever the user passes.
"""

# streamlit run frontend_app.py

import streamlit as st
import requests  # To make HTTP requests to backend

BACKEND_URL = "http://127.0.0.1:5000/"  # URL of your Flask backend

# --- Configure sidebar to be collapsed by default ---
st.set_page_config(initial_sidebar_state="collapsed")
# --- End sidebar configuration ---


st.title("CultureAI")


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
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
