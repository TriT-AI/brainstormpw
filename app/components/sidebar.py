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
        st.markdown("## Project Workspace")

        # Get sections early to determine default expander states
        sections = get_sections()
        has_document = bool(sections)

        # =================================================================
        # SECTION 1: CREATE / IMPORT (Primary PM Actions)
        # =================================================================
        
        with st.expander("New Document", expanded=not has_document):
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

        with st.expander("Import Charter", expanded=not has_document):
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
                    st.error("Please configure AI connection in the Administration section below.")
                else:
                    with st.spinner("Reading PDF & Structuring Data..."):
                        try:
                            # 1. Parse PDF
                            sections = parse_charter_pdf(
                                uploaded_file, api_key, model_name, base_url
                            )

                            # 2. Load to State
                            load_imported_sections_into_state(sections)

                            st.success(
                                f"Charter imported successfully! Found {len(sections)} sections."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing PDF: {str(e)}")

        st.divider()

        # =================================================================
        # SECTION 2: DOCUMENT HEALTH (Status Dashboard)
        # =================================================================

        if not sections:
            st.info("Select a template or import a document to begin.")
        else:
            st.markdown("### Document Health")

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

        # =================================================================
        # SECTION 3: ADMINISTRATION (Advanced Options - Collapsed)
        # =================================================================
        
        st.caption("Administration")

        with st.expander("AI Connection", expanded=False):
            # Check if system key is available (loaded from secrets)
            has_system_key = "system_api_key" in st.session_state

            if has_system_key:
                st.success("System credentials loaded")
                
                # Progressive disclosure: hide full form behind toggle
                show_advanced = st.checkbox("Show advanced settings", value=False, key="show_ai_advanced")
                
                if show_advanced:
                    st.caption("Override system credentials (optional):")
                    _render_credential_inputs(
                        key_placeholder="Using system key...",
                        key_help="Leave empty to use system key, or enter your own to override."
                    )
            else:
                st.warning("No system key configured. Please enter your credentials.")
                _render_credential_inputs(
                    key_placeholder="sk-...",
                    key_help="Your OpenAI API Key"
                )

        with st.expander("Workspace Actions", expanded=False):
            st.caption("Danger zone")
            if st.button("Clear Workspace", use_container_width=True, type="secondary"):
                clear_workspace()
                st.rerun()


def _render_credential_inputs(key_placeholder: str, key_help: str):
    """Helper to render API credential input fields."""
    # 1. API KEY INPUT
    st.text_input(
        "API Key",
        type="password",
        key="user_api_key",
        placeholder=key_placeholder,
        help=key_help,
    )

    # 2. MODEL NAME INPUT
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
