import streamlit as st
from langchain_openai import ChatOpenAI


def get_user_llm():
    """
    Attempts to create a ChatOpenAI instance using credentials
    entered by the user in the Streamlit Sidebar.
    Returns None if credentials are missing.
    """
    api_key = st.session_state.get("user_api_key")
    base_url = st.session_state.get("user_base_url")
    deployment = st.session_state.get("user_deployment_name")

    if not api_key or not base_url or not deployment:
        return None

    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=deployment,
        )
        return llm
    except Exception as e:
        st.error(f"Error initializing LLM: {e}")
        return None
