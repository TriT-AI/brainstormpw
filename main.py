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

    # --- Enhanced Login Page Styling ---
    st.markdown(
        """
        <style>
            /* Hide sidebar on login page */
            [data-testid="stSidebar"] { display: none; }
            
            /* Center the login container */
            .login-container {
                max-width: 420px;
                margin: 80px auto 0 auto;
                padding: 40px;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                border: 1px solid #e9ecef;
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 32px;
            }
            
            .login-title {
                font-size: 1.75rem;
                font-weight: 700;
                color: #1a1a2e;
                margin: 0 0 8px 0;
            }
            
            .login-subtitle {
                font-size: 0.95rem;
                color: #6c757d;
                margin: 0;
            }
            
            .login-divider {
                height: 4px;
                background: linear-gradient(90deg, #942331 0%, #CB1517 25%, #14387F 50%, #0095B3 75%, #00A24C 100%);
                border-radius: 2px;
                margin: 24px 0;
            }
            
            .login-footer {
                text-align: center;
                margin-top: 24px;
                font-size: 0.85rem;
                color: #adb5bd;
            }
        </style>
        
        <div class="login-container">
            <div class="login-header">
                <h1 class="login-title">Project Charter Auditor</h1>
                <p class="login-subtitle">AI-powered document compliance review</p>
            </div>
            <div class="login-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Create centered columns for the input
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.text_input(
            "Access Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter your password",
        )

        if "password_correct" in st.session_state:
            st.error("Incorrect password. Please try again.")
        
        st.caption("Contact your administrator if you need access.")

    return False


# --- 3. HELPER: LOAD SECRETS ---
def load_secrets_if_available():
    """
    Checks .streamlit/secrets.toml for OpenAI credentials.
    Stores them in 'system_*' keys to avoid exposing them in the UI text inputs.
    """
    # Mapping: Secrets Key -> Session State Key (Hidden System Keys)
    mapping = {
        "OPENAI_API_KEY": "system_api_key",
        "OPENAI_MODEL_NAME": "system_model_name",
        "OPENAI_BASE_URL": "system_base_url",
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

    from app.components.global_audit import render_global_feedback
    render_global_feedback()

    render_section_editor()
    render_chat_widget()


if __name__ == "__main__":
    main()
