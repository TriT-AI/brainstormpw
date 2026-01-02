import streamlit as st
from app.state_manager import update_section_content, update_section_audit_result
from backend.graph.workflow import graph


def render_audit_results(section):
    """
    Renders the results of the AI Audit.
    - If Compliant: Shows Green Success Box.
    - If Issues: Iterates through issues and shows specific Alerts.
    - Logic: Checks 'fixable' flag to toggle between 'Auto-Fix' and 'Manual Input Needed'.
    """
    sec_id = section["id"]
    audit_data = section["user_data"].get("last_audit")

    if not audit_data:
        return

    # --- CASE 1: SUCCESS ---
    if audit_data.get("is_compliant"):
        st.success(
            "✅ **Section Compliant:** All criteria and formatting rules are met."
        )
        return

    # --- CASE 2: ISSUES FOUND ---
    issues = audit_data.get("issues", [])

    st.caption(f"Found {len(issues)} issue(s):")

    for issue in issues:
        # Determine Color based on Severity
        severity = issue.get("severity", "Medium")
        if severity == "High":
            box_color = "#fdecea"  # Red tint
            border_color = "#ed0007"
            icon = "🔴"
        else:
            box_color = "#fff4e5"  # Orange tint
            border_color = "#ffaa00"
            icon = "⚠️"

        # Render Custom Alert Box using HTML/CSS for better control
        st.markdown(
            f"""
            <div style="
                background-color: {box_color}; 
                border-left: 5px solid {border_color};
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 10px;
                color: #333;
            ">
                <div style="font-weight: bold; margin-bottom: 5px;">
                    {icon} {severity}: {issue.get("issue_description")}
                </div>
                <div style="font-size: 0.9em; margin-bottom: 10px;">
                    💡 <em>{issue.get("recommendation")}</em>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- ACTION BUTTONS (The Logic Gate) ---
        col_space, col_btn = st.columns([3, 2])

        with col_btn:
            # Check the Boolean Flag from the Backend
            # This is the "Smart" logic that prevents AI hallucinations
            is_fixable = issue.get("fixable", False)

            if is_fixable:
                # SHOW AUTO-FIX BUTTON
                # [FIX]: We use on_click callback to safely handle state updates
                st.button(
                    "✨ Auto-Fix",
                    key=f"fix_{sec_id}_{issue['id']}",
                    help="AI will rewrite this section to fix the formatting/grammar.",
                    use_container_width=True,
                    on_click=_handle_fix_request,  # <--- Callback
                    args=(section, issue),  # <--- Pass Data
                )

            else:
                # SHOW BLOCKED STATE (Input Required)
                # Shown when data is missing (e.g. missing name, missing date)
                st.button(
                    "⛔ Input Required",
                    key=f"blocked_{sec_id}_{issue['id']}",
                    disabled=True,  # User cannot click this
                    help="You must manually type the missing information (e.g. Names, Dates) before the AI can format it.",
                    use_container_width=True,
                )


def _handle_fix_request(section, target_issue):
    """
    Callback function executed when 'Auto-Fix' is clicked.
    Running in a callback allows us to safely modify st.session_state["editor_..."]
    before the widget is re-instantiated in the next run.
    """
    sec_id = section["id"]
    meta = section["meta"]
    user_data = section["user_data"]

    # Run the AI Graph
    # Note: st.spinner may not render fully inside a callback,
    # but the app will show a 'Running...' indicator in the top right.
    inputs = {
        "section_title": meta["title"],
        "criteria": meta["criteria"],
        "template_structure": meta["template_structure"],
        "user_content": user_data["content"],
        "issues": [],
        "is_compliant": False,
        "target_issue": target_issue,
    }

    config = {"configurable": {"thread_id": sec_id}}
    result = graph.invoke(inputs, config)

    if "user_content" in result:
        new_text = result["user_content"]

        # 1. Update the Data Store (Backend State)
        update_section_content(sec_id, new_text)

        # 2. Update the Widget State (Frontend Cache)
        # This prevents the "StreamlitAPIException"
        widget_key = f"editor_{sec_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = new_text

        # 3. Reset Audit Status (Force re-check)
        update_section_audit_result(sec_id, {})
