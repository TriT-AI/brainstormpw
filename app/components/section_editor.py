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

    st.subheader(f"Document Editor ({len(sections)} Sections)")

    # Iterate through sections
    for i, section in enumerate(sections):
        sec_id = section["id"]
        meta = section["meta"]
        user_data = section["user_data"]

        # --- Card Container ---
        with st.container():
            # Navigation Anchor
            st.markdown(f"<span id='section-{sec_id}'></span>", unsafe_allow_html=True)
            st.markdown(f"### {meta['title']}")

            # SPLIT LAYOUT: 1 part Instructions, 2 parts Editor
            col_rules, col_editor = st.columns([1, 2], gap="medium")

            # --- LEFT COLUMN: The "Source of Truth" ---
            with col_rules:
                st.info(f"**Guidance:**\n\n{meta['criteria']}")

                st.caption("📋 **Required Format (Copy/Paste if needed):**")
                st.code(meta["template_structure"], language="text")

            # --- RIGHT COLUMN: The Workspace ---
            with col_editor:
                # 1. HEADER & ACTION (Top-Right)
                col_label, col_action = st.columns([2, 1])
                with col_label:
                    st.markdown(f"**Content**")
                
                with col_action:
                     if st.button(
                        "Review",
                        key=f"btn_audit_{sec_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        with st.spinner("Reviewing your draft..."):
                            # --- AI BACKEND CALL ---
                            inputs = {
                                "section_title": meta["title"],
                                "criteria": meta["criteria"],
                                "template_structure": meta["template_structure"],
                                "user_content": user_data["content"], # Use stat value as text_area not rendered yet? No, careful. 
                                # Wait, if I click button, the text_area value might not be updated in 'user_data' yet if I just typed it.
                                # Streamlit updates widget state on rerun. 
                                # If I move button ABOVE text_area, I need to make sure I pull the latest value.
                                # Actually, standard Streamlit pattern: widgets update state.
                                # But if I type and immediately click button above?
                                # The button click triggers rerun. The text_area value in `st.session_state` (if key used) or return value will be updated?
                                # Actually, if button is clicked, the script reruns. The text_area value *should* be available in session state if key is used.
                                # Let's check if `user_data["content"]` is safe. `user_data` comes from `get_sections`. 
                                # The text_area updates `user_data` in the `if current_content != ...` block *after* the text area is rendered.
                                # So if button is BEFORE text_area, we might rely on stale data if we aren't careful.
                                                                
                                # BETTER APPROACH:
                                # Render text area first? No, user wants button ABOVE.
                                # In Streamlit, render order matters for layout. 
                                # Logic: 
                                # 1. Render Button. 
                                # 2. Render Text Area.
                                # If button clicked:
                                #    The `user_data["content"]` is from previous run? 
                                #    Issue: If user types "abc" and clicks button immediately.
                                #    Rerun starts. Button returns True. 
                                #    Text area hasn't run yet this rerun.
                                #    `user_data["content"]` is old.
                                #    SOLUTIONS:
                                #    A) Use `st.session_state[f"editor_{sec_id}"]` if it exists.
                                "issues": [],
                                "is_compliant": False,
                                "target_issue": None,
                            }
                            
                            # Fetch latest content from session state if available (since text_area uses key)
                            # This handles the "Type -> Click" race condition for widgets rendered later
                            current_val = st.session_state.get(f"editor_{sec_id}", user_data["content"])
                            inputs["user_content"] = current_val

                            # Run Graph (Auditor Node)
                            config = {"configurable": {"thread_id": sec_id}}
                            result = graph.invoke(inputs, config)

                            # Save Results to State
                            update_section_audit_result(sec_id, result)
                            st.rerun()

                # 2. TEXT AREA
                # We use a unique key based on ID to preserve state across reruns
                current_content = st.text_area(
                    label=f"Content for {meta['title']}",
                    value=user_data["content"],
                    height=250,
                    key=f"editor_{sec_id}",
                    placeholder=meta["template_structure"],  # Ghost text hint
                    help="Write your content here. Click Review to get feedback.",
                )

                # Sync content to state if changed
                if current_content != user_data["content"]:
                    update_section_content(sec_id, current_content)

                # (Action Bar moved to top)

                # 3. AUDIT RESULTS AREA
                # This function (from the next file) renders the Alerts and Fix Buttons
                if user_data.get("last_audit"):
                    render_audit_results(section)

        st.divider()
