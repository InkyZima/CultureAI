
from langchain.schema import HumanMessage, AIMessage
import re

def reformat_history(langchain_history):
    """
    Reformats a Langchain chat history (list of HumanMessage and AIMessage objects)
    into a list of dictionaries suitable for Streamlit's chat display.

    This version extracts user messages and LLM responses from consecutive pairs
    of messages in the Langchain history. Timestamps are not included as
    Langchain message objects do not directly contain timestamps.

    Args:
        langchain_history: A list of Langchain HumanMessage and AIMessage objects
                           (e.g., obtained from get_chat_history()).

    Returns:
        A list of dictionaries, where each dictionary represents a turn
        in the conversation and has keys 'user_message' and 'llm_response'.
    """
    streamlit_history = []
    user_message = None
    llm_response = None
    user_prefix_regex = r"^User on \d{2}:\d{2}:\s*"

    for i, message in enumerate(langchain_history):
        if isinstance(message, HumanMessage):
            user_message = message.content
            user_message = re.sub(user_prefix_regex, "", message.content) # remove timestamp
        elif isinstance(message, AIMessage):
            llm_response = message.content

        if user_message is not None and llm_response is not None:
            streamlit_history.append({
                "user_message": user_message,
                "llm_response": llm_response,
                # "timestamp":  You would need to add timestamp logic here if available
            })
            user_message = None  # Reset for the next turn
            llm_response = None   # Reset for the next turn

    return streamlit_history