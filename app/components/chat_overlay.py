import streamlit as st
from app.state_manager import get_sections, update_section_content
from backend.chat import get_chat_response


def render_chat_widget():
    """
    Renders a polished, floating AI Assistant widget.
    Includes: Pulse Animation, Clear History, and Smart Sync.
    """
    # 1. Initialize State
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {
                "role": "assistant",
                "content": "👋 **Hello!** I'm reading your draft. Ask me to summarize it, find missing gaps, or suggest improvements.",
            }
        ]

    # 2. Advanced CSS Styling
    # [FIX]: Removed the global button override that broke the Audit button
    st.markdown(
        """
    <style>
    /* --- 1. Floating Action Button (FAB) --- */
    [data-testid="stPopover"] {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 99999;
        background: linear-gradient(135deg, #00629a 0%, #004e7a 100%); /* Bosch Blue Gradient */
        color: white;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
        border: 2px solid white;
        transition: transform 0.2s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
        /* animation removed for professional look */
    }

    /* --- FIX: Remove default Streamlit button "white box" inside popover trigger --- */
    [data-testid="stPopover"] button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        padding: 0 !important;

        /* ensure the clickable area matches your FAB */
        width: 60px !important;
        height: 60px !important;
        min-height: unset !important;
        border-radius: 50% !important;
    }

    [data-testid="stPopover"] button:hover,
    [data-testid="stPopover"] button:active,
    [data-testid="stPopover"] button:focus,
    [data-testid="stPopover"] button:focus-visible {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Some Streamlit versions wrap the label in spans/divs; keep them transparent too */
    [data-testid="stPopover"] button * {
        background: transparent !important;
    }

    /* Fix Icon Alignment inside the Circle */
    [data-testid="stPopover"] > div {
        font-size: 28px !important;
        margin-top: -2px; /* Optical center adjustment */
        margin-left: 0px;
    }

    /* --- 2. Chat Window Tweaks --- */

    /* Message Bubbles */
    .stChatMessage {
        background-color: #f9f9f9;
        border-radius: 10px;
        border: 1px solid #eee;
        margin-bottom: 10px;
    }

    /* Pulse animation removed for subtler appearance */

    /* Header Title Styling */
    .chat-header-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #004e7a;
        margin: 0;
        padding: 0;
        line-height: 1.5;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # 3. The Chat Interface
    with st.popover("💬", help="Open Project Companion", type="tertiary"):
        # --- HEADER: Aligned Flex Layout ---
        c_title, c_btn = st.columns([5, 1])

        with c_title:
            st.markdown(
                '<p class="chat-header-title">🧠 Project Brain</p>',
                unsafe_allow_html=True,
            )
            st.caption("Context-aware Q&A")

        with c_btn:
            # We use a standard button here to avoid global CSS conflicts
            if st.button("🗑️", help="Clear History", use_container_width=True):
                st.session_state["chat_history"] = [
                    {"role": "assistant", "content": "History cleared. What's next?"}
                ]
                st.rerun()

        st.divider()

        # --- CHAT HISTORY ---
        chat_container = st.container(height=350)

        for msg in st.session_state["chat_history"]:
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with chat_container.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        # --- SUGGESTED CHIPS ---
        if len(st.session_state["chat_history"]) < 3:
            st.caption("Suggested:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Summarize", use_container_width=True):
                    _handle_chat_submit("Summarize my current draft so far.")
            with col2:
                if st.button("🔍 Find Gaps", use_container_width=True):
                    _handle_chat_submit("What is missing from this charter?")

        # --- INPUT AREA ---
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Message",
                placeholder="Ask about your project...",
                label_visibility="collapsed",
            )

            if st.form_submit_button(
                "Send Message ➤", use_container_width=True, type="primary"
            ):
                if user_input.strip():
                    _handle_chat_submit(user_input)
                else:
                    st.warning("Please type a question first.")


def _handle_chat_submit(user_input):
    """
    Handles the chat submission with Force-Sync.
    """
    # 1. Force Sync: Ensure 'sections' in state matches what's on screen
    sections = get_sections()
    for sec in sections:
        widget_key = f"editor_{sec['id']}"
        if widget_key in st.session_state:
            current_text = st.session_state[widget_key]
            update_section_content(sec["id"], current_text)

    # 2. Add User Message
    st.session_state["chat_history"].append({"role": "user", "content": user_input})

    # 3. Get Answer
    with st.spinner("Thinking..."):
        latest_sections = get_sections()
        response_text = get_chat_response(
            st.session_state["chat_history"], latest_sections
        )

    # 4. Add AI Message
    st.session_state["chat_history"].append(
        {"role": "assistant", "content": response_text}
    )

    st.rerun()
