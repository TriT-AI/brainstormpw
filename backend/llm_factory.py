import streamlit as st
from langchain_openai import ChatOpenAI


def get_user_llm():
    """
    Attempts to create a ChatOpenAI instance using credentials
    entered by the user in the Streamlit Sidebar.
    Returns None if credentials are missing.
    """
    api_key = st.session_state.get("user_api_key")
    model_name = st.session_state.get("user_model_name", "gpt-4.1")
    base_url = st.session_state.get("user_base_url")

    if not api_key:
        return None

    try:
        kwargs = {"api_key": api_key, "model": model_name}

        if base_url and base_url.strip():
            kwargs["base_url"] = base_url

        llm = ChatOpenAI(**kwargs)
        return llm
    except Exception as e:
        st.error(f"Error initializing LLM: {e}")
        return None
