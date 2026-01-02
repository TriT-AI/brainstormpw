import streamlit as st
from dotenv import load_dotenv

# Import our components
from app.state_manager import initialize_session
from app.components.sidebar import render_sidebar
from app.components.section_editor import render_section_editor
from app.components.chat_overlay import render_chat_widget

# --- 1. CONFIGURATION ---
# Load environment variables (API keys)
load_dotenv()

# Set Streamlit Page Config
st.set_page_config(
    page_title="Project Charter AI Auditor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. GLOBAL STYLES (CSS) ---
# We inject this here to ensure it applies to all components
st.markdown(
    """
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        /* Apply Font */
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }

        /* Supergraphic Top Bar (Bosch Brand Colors) */
        .supergraphic {
            height: 8px;
            background: linear-gradient(90deg, #942331 0%, #CB1517 15%, #88357F 25%, #14387F 35%, #0095B3 75%, #00A24C 90%, #00937D 100%);
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            z-index: 99999;
        }

        /* Adjust top padding so content doesn't hide behind the bar */
        .block-container {
            padding-top: 2rem;
        }

        /* Card Styling for Section Editors */
        .stTextArea textarea {
            background-color: #fcfcfc;
            border: 1px solid #e0e0e0;
        }
        
        /* Audit Button Styling */
        div[data-testid="stVerticalBlock"] > button {
            margin-top: 10px;
        }
    </style>
    <div class="supergraphic"></div>
    """,
    unsafe_allow_html=True,
)

# --- 3. APP EXECUTION FLOW ---


def main():
    # A. Initialize Session State
    # Ensures 'sections' list exists before we try to render anything
    initialize_session()

    # B. Render Sidebar
    # Handles Template Loading and Navigation
    render_sidebar()

    # C. Render Main Content
    # Handles the Split View Editor
    st.title("Project Charter AI Auditor")
    st.markdown(
        "Use the **Sidebar** to load a template, then edit and audit your sections below."
    )
    st.divider()

    render_section_editor()
    render_chat_widget()


if __name__ == "__main__":
    main()
