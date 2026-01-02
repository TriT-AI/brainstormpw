import streamlit as st
from app.state_manager import (
    load_template_into_state,
    clear_workspace,
    get_sections,
)
from data.template_registry import get_available_templates


def render_sidebar():
    """
    Renders the sidebar with:
    1. Template Selection (New Document)
    2. Document Health Dashboard (TOC with Status Indicators)
    3. Global Actions (Clear)
    """
    with st.sidebar:
        st.markdown("## 🗂️ Project Workspace")

        # --- TAB 1: CREATE NEW ---
        with st.expander("📄 New Document", expanded=False):
            templates = get_available_templates()
            selected_template = st.selectbox("Select Template", templates)

            if st.button(
                "Create from Template", type="primary", use_container_width=True
            ):
                # Warning if work exists
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

            # Progress Bar logic
            total = len(sections)
            compliant_count = sum(
                1 for s in sections if s["user_data"]["status"] == "compliant"
            )
            progress = compliant_count / total if total > 0 else 0

            st.progress(progress, text=f"Readiness: {int(progress * 100)}%")

            # Table of Contents with Status Icons
            st.markdown("---")
            st.caption("Navigation & Status")

            for section in sections:
                status = section["user_data"]["status"]
                title = section["meta"]["title"]

                # Icon Logic
                if status == "compliant":
                    icon = "🟢"
                elif status == "flagged":
                    icon = "🔴"
                else:
                    icon = "⚪"  # Draft

                # We use a markdown link or simple text.
                # Note: Streamlit native anchor linking is limited, so we visually display it.
                # In a more advanced app, clicking this could set a 'focused_section' state.
                st.markdown(f"{icon} **{title}**")

        st.divider()

        # --- TAB 3: DANGER ZONE ---
        if st.button("🗑️ Clear Workspace", use_container_width=True):
            clear_workspace()
            st.rerun()
