import streamlit as st
from dotenv import load_dotenv

# Import our components
from app.state_manager import initialize_session
from app.components.sidebar import render_sidebar
from app.components.section_editor import render_section_editor
from app.components.chat_overlay import render_chat_widget

# --- 1. CONFIGURATION ---
load_dotenv()  # Optional now, but good to keep if you dev locally

st.set_page_config(
    page_title="Project Charter AI Auditor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- 2. AUTHENTICATION LOGIC ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the user has already validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.text_input(
        "Please enter the access password:",
        type="password",
        on_change=password_entered,
        key="password",
    )

    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")

    return False


# --- 3. HELPER: LOAD SECRETS ---
def load_secrets_if_available():
    """
    Checks .streamlit/secrets.toml for OpenAI credentials and pre-fills session state.
    This allows the Sidebar to pick them up automatically as default values.
    """
    # Mapping: Secrets Key -> Session State Key (used by Sidebar & LLM Factory)
    mapping = {
        "OPENAI_API_KEY": "user_api_key",
        "OPENAI_MODEL_NAME": "user_model_name",
        "OPENAI_BASE_URL": "user_base_url",
    }

    for secret_key, state_key in mapping.items():
        # Only load if the secret exists AND the state isn't already set
        if secret_key in st.secrets and state_key not in st.session_state:
            st.session_state[state_key] = st.secrets[secret_key]


# --- 4. GLOBAL STYLES (CSS) ---
def load_css():
    """Loads the custom CSS. Only called after authentication."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
            html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
            .supergraphic {
                height: 8px;
                background: linear-gradient(90deg, #942331 0%, #CB1517 15%, #88357F 25%, #14387F 35%, #0095B3 75%, #00A24C 90%, #00937D 100%);
                width: 100%;
                position: fixed;
                top: 0; left: 0; z-index: 99999;
            }
            .block-container { padding-top: 2rem; }
            .stTextArea textarea { background-color: #fcfcfc; border: 1px solid #e0e0e0; }
            div[data-testid="stVerticalBlock"] > button { margin-top: 10px; }
        </style>
        <div class="supergraphic"></div>
        """,
        unsafe_allow_html=True,
    )


# --- 5. APP EXECUTION FLOW ---
def main():
    # 1. Check Authentication first
    if not check_password():
        st.stop()  # Stop here if not authenticated

    # 2. Run the actual App (Only reaches here if logged in)
    load_css()
    initialize_session()

    # 3. Try to load OpenAI credentials from secrets (before Sidebar renders)
    load_secrets_if_available()

    render_sidebar()

    st.title("Project Charter AI Auditor")
    st.markdown(
        "Use the **Sidebar** to load a template, then edit and audit your sections below."
    )
    st.divider()

    render_section_editor()
    render_chat_widget()


if __name__ == "__main__":
    main()
