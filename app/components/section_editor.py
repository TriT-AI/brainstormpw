import streamlit as st
from app.state_manager import (
    get_sections,
    update_section_content,
    update_section_audit_result,
)

# We will create this next. It handles the Alerts, Fix Buttons, and Diff Logic.
from app.components.audit_alerts import render_audit_results
from backend.graph.workflow import graph


def render_section_editor():
    """
    Iterates through the active sections and renders the Split View Editor.
    Layout:
    [ Left Col: Rules & Template ]  |  [ Right Col: User Editor ]
    """
    sections = get_sections()

    if not sections:
        st.markdown(
            """
            <div style="text-align: center; padding: 50px; color: #666;">
                <h3>👋 Ready to start?</h3>
                <p>Select a <strong>Template</strong> from the sidebar to create a new document.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.subheader(f"📝 Document Editor ({len(sections)} Sections)")

    # Iterate through sections
    for i, section in enumerate(sections):
        sec_id = section["id"]
        meta = section["meta"]
        user_data = section["user_data"]

        # --- Card Container ---
        with st.container():
            st.markdown(f"### {meta['title']}")

            # SPLIT LAYOUT: 1 part Instructions, 2 parts Editor
            col_rules, col_editor = st.columns([1, 2], gap="medium")

            # --- LEFT COLUMN: The "Source of Truth" ---
            with col_rules:
                st.info(f"**Instructions:**\n\n{meta['criteria']}")

                st.caption("📋 **Required Format (Copy/Paste if needed):**")
                st.code(meta["template_structure"], language="text")

            # --- RIGHT COLUMN: The Workspace ---
            with col_editor:
                # 1. TEXT AREA
                # We use a unique key based on ID to preserve state across reruns
                current_content = st.text_area(
                    label=f"Content for {meta['title']}",
                    value=user_data["content"],
                    height=250,
                    key=f"editor_{sec_id}",
                    placeholder=meta["template_structure"],  # Ghost text hint
                    help="Write your content here. Click Audit to check compliance.",
                )

                # Sync content to state if changed
                if current_content != user_data["content"]:
                    update_section_content(sec_id, current_content)

                # 2. ACTION BAR (Audit Button)
                col_actions, _ = st.columns([1, 3])
                with col_actions:
                    if st.button(
                        "🔍 Audit Section",
                        key=f"btn_audit_{sec_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        with st.spinner("Analyzing against criteria..."):
                            # --- AI BACKEND CALL ---
                            inputs = {
                                "section_title": meta["title"],
                                "criteria": meta["criteria"],
                                "template_structure": meta["template_structure"],
                                "user_content": current_content,
                                "issues": [],
                                "is_compliant": False,
                                "target_issue": None,
                            }

                            # Run Graph (Auditor Node)
                            config = {"configurable": {"thread_id": sec_id}}
                            result = graph.invoke(inputs, config)

                            # Save Results to State
                            update_section_audit_result(sec_id, result)
                            st.rerun()

                # 3. AUDIT RESULTS AREA
                # This function (from the next file) renders the Alerts and Fix Buttons
                if user_data.get("last_audit"):
                    render_audit_results(section)

        st.divider()
