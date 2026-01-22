import streamlit as st
from app.state_manager import get_global_audit_result, get_sections
from app.state_manager import update_section_audit_result, update_global_audit_result
from backend.graph.workflow import run_batch_audit

def render_global_feedback():
    """
    Renders the Global Consistency Results (Logic Check) at the top of the editor.
    Also provides the Button to trigger the check.
    """
    
    # --- ACTION BUTTON ---
    # Placed top-right to inspire action
    col_info, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("Review Document", type="primary", use_container_width=True):
            current_sections = get_sections()
            if not current_sections:
                st.warning("Please create a document (select template) first.")
            else:
                with st.spinner("Analyzing entire document logic..."):
                    # 1. Run the Batch Audit
                    results = run_batch_audit(current_sections)
                    
                    # 2. Update Sections
                    for sec_id, audit_res in results["section_results"].items():
                        update_section_audit_result(sec_id, audit_res)
                    
                    # 3. Update Global Logic Result
                    update_global_audit_result(results["global_result"])
                    
                    st.rerun()

    # --- RESULTS DISPLAY ---
    global_result = get_global_audit_result()

    if not global_result:
        # If no results yet, just return (or show a spacer)
        st.divider()
        return

    st.markdown("### 📋 Document Review Summary")

    is_consistent = global_result.get("is_consistent")
    issues = global_result.get("global_issues", [])

    if is_consistent and not issues:
        st.success("✅ **Excellent**: The document is consistent and coherent throughout.")
        st.divider()
        return

    # SUMMARY DASHBOARD
    st.warning(f"Found **{len(issues)}** Items for Review")
    
    # Render Issues
    for issue in issues:
        with st.container(border=True):
            col_icon, col_desc = st.columns([1, 12])
            with col_icon:
                st.markdown("⚠️")
            with col_desc:
                st.markdown(f"**{issue['title']}**")
                st.markdown(f"{issue['description']}")
                
                # Render "Jump to" links
                if issue.get('related_sections'):
                    links = []
                    sections = get_sections()
                    for sec_name in issue['related_sections']:
                        # Find the ID for this section name
                        target_sec = next((s for s in sections if s['meta']['title'] == sec_name), None)
                        if target_sec:
                            # Streamlit anchor link format: [Text](#anchor)
                            # Note: Streamlit's markdown anchors might need a refresh to work perfectly, 
                            # but purely client-side anchors work if the element exists.
                            links.append(f"[{sec_name}](#section-{target_sec['id']})")
                        else:
                            links.append(sec_name)
                    
                    st.markdown(f"👉 **Affects:** {' | '.join(links)}")

    st.divider()
