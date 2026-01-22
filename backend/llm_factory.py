import streamlit as st
from langchain_openai import ChatOpenAI


def get_user_llm():
    """
    Attempts to create a ChatOpenAI instance.
    Priority: User Input > System Secret > None
    """
    # 1. Get values from the User Interface (might be empty)
    api_key = st.session_state.get("user_api_key")
    model_name = st.session_state.get("user_model_name")
    base_url = st.session_state.get("user_base_url")

    # 2. FALLBACK: If User Input is empty, check for Hidden System Secrets
    if not api_key:
        api_key = st.session_state.get("system_api_key")

    # Fallback for Base URL (only if user left it blank)
    if not base_url:
        base_url = st.session_state.get("system_base_url")

    # Fallback for Model Name (though Sidebar usually defaults this)
    if not model_name:
        model_name = st.session_state.get("system_model_name", "gpt-4o")

    # 3. Final Validation: Do we have a key now?
    if not api_key:
        return None

    try:
        # Prepare arguments
        kwargs = {"api_key": api_key, "model": model_name, "temperature": 0}

        # Only add base_url if it exists and is not empty
        if base_url and base_url.strip():
            kwargs["base_url"] = base_url

        llm = ChatOpenAI(**kwargs)
        return llm
    except Exception as e:
        st.error(f"Error initializing LLM: {e}")
        return None
