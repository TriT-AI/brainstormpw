import streamlit as st
from app.state_manager import (
    load_template_into_state,
    clear_workspace,
    get_sections,
)
from data.template_registry import get_available_templates


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🗂️ Project Workspace")

        with st.expander("⚙️ OpenAI Settings", expanded=True):
            st.caption("Enter your standard OpenAI API Key.")

            st.text_input(
                "API Key",
                type="password",
                key="user_api_key",
                help="Your sk-... API Key",
            )

            st.text_input(
                "Model Name",
                key="user_model_name",
                value="gpt-4o",
                placeholder="gpt-4o, gpt-4-turbo, etc.",
                help="The model to use (e.g., gpt-4o)",
            )

            # Made optional
            st.text_input(
                "Base URL (Optional)",
                key="user_base_url",
                placeholder="Leave empty for standard OpenAI",
                help="Only required if using a proxy.",
            )

            if st.session_state.get("user_api_key"):
                st.success("Credentials set!")
            else:
                st.warning("Please enter API Key.")

        st.divider()

        # --- TAB 1: CREATE NEW ---
        with st.expander("📄 New Document", expanded=False):
            templates = get_available_templates()
            selected_template = st.selectbox("Select Template", templates)

            if st.button(
                "Create from Template", type="primary", use_container_width=True
            ):
                if get_sections():
                    st.warning("This will overwrite your current work.")

                with st.spinner("Loading Template..."):
                    load_template_into_state(selected_template)
                    st.rerun()

        st.divider()

        # --- TAB 2: HEALTH DASHBOARD (TOC) ---
        sections = get_sections()

        if not sections:
            st.info("👈 Select a template to begin.")
        else:
            st.markdown("### 📊 Document Health")

            total = len(sections)
            compliant_count = sum(
                1 for s in sections if s["user_data"]["status"] == "compliant"
            )
            progress = compliant_count / total if total > 0 else 0

            st.progress(progress, text=f"Readiness: {int(progress * 100)}%")

            st.markdown("---")
            st.caption("Navigation & Status")

            for section in sections:
                status = section["user_data"]["status"]
                title = section["meta"]["title"]

                if status == "compliant":
                    icon = "🟢"
                elif status == "flagged":
                    icon = "🔴"
                else:
                    icon = "⚪"

                st.markdown(f"{icon} **{title}**")

        st.divider()

        # --- TAB 3: DANGER ZONE ---
        if st.button("🗑️ Clear Workspace", use_container_width=True):
            clear_workspace()
            st.rerun()
