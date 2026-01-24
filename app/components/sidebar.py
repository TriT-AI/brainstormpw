import streamlit as st
from app.state_manager import (
    load_template_into_state,
    load_imported_sections_into_state,
    clear_workspace,
    get_sections,
)
from data.template_registry import get_available_templates
from backend.ingestion import parse_charter_pdf, get_pdf_stats


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🗂️ Project Workspace")

        with st.expander("⚙️ OpenAI Settings", expanded=True):
            # Check if system key is available (loaded from secrets)
            has_system_key = "system_api_key" in st.session_state

            if has_system_key:
                st.success("✅ System Credentials Loaded")
                key_placeholder = "Using loaded system key..."
                key_help = "A system key is loaded securely. Type here to override it with your own."
            else:
                st.caption("Enter your standard OpenAI API Key.")
                key_placeholder = "sk-..."
                key_help = "Your sk-... API Key"

            # 1. API KEY INPUT (Empty by default if system key exists)
            user_key = st.text_input(
                "API Key",
                type="password",
                key="user_api_key",
                placeholder=key_placeholder,
                help=key_help,
            )

            # 2. MODEL NAME INPUT
            # Default to system model or gpt-4o
            default_model = st.session_state.get("system_model_name", "gpt-4o")

            st.text_input(
                "Model Name",
                key="user_model_name",
                value=default_model,
                placeholder="gpt-4o, gpt-4-turbo, etc.",
                help="The model to use (e.g., gpt-4o)",
            )

            # 3. BASE URL (Optional)
            st.text_input(
                "Base URL (Optional)",
                key="user_base_url",
                placeholder="Leave empty for standard OpenAI",
                help="Only required if using a proxy.",
            )

            # VALIDATION FEEDBACK
            if user_key or has_system_key:
                # If either user input OR system key is present, we are good
                pass
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

        # --- TAB 2: IMPORT PDF ---
        with st.expander("📂 Import Charter (PDF)", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload Project Charter",
                type=["pdf"],
                key="pdf_uploader",
            )

            if uploaded_file and st.button("Process & Load", type="primary", key="process_pdf_btn"):
                # Check for API Key
                api_key = st.session_state.get("user_api_key") or st.session_state.get(
                    "system_api_key"
                )
                model_name = st.session_state.get("user_model_name") or st.session_state.get(
                    "system_model_name", "gpt-4o"
                )
                base_url = st.session_state.get("user_base_url") or st.session_state.get(
                    "system_base_url"
                )

                if not api_key:
                    st.error("Please provide an OpenAI API Key first.")
                else:
                    with st.spinner("🔍 Reading PDF & Structuring Data..."):
                        try:
                            # 1. Parse PDF
                            sections = parse_charter_pdf(
                                uploaded_file, api_key, model_name, base_url
                            )

                            # 2. Load to State
                            load_imported_sections_into_state(sections)

                            st.success(
                                f"✅ Charter imported successfully! Found {len(sections)} sections."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing PDF: {str(e)}")

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
