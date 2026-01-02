import streamlit as st
import uuid
import re
import base64
import os

# --- IMPORT GRAPH ---
try:
    from backend_graph import graph
except ImportError:
    st.error("backend_graph.py not found.")
    st.stop()


# --- ASSETS HELPER ---
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# --- THEME CONFIG ---
BOSCH_LOGO_PATH = "assets/bosch.png"
logo_b64 = get_base64_image(BOSCH_LOGO_PATH)

if logo_b64:
    LOGO_HTML = f'<img src="data:image/png;base64,{logo_b64}" height="35" style="margin-right: 15px;">'
else:
    LOGO_HTML = '<span style="font-weight:bold; color:#ed0007; font-size:24px; margin-right: 15px;">BOSCH</span>'

SUPERGRAPHIC_CSS = "background: linear-gradient(90deg, #942331 0%, #CB1517 15%, #88357F 25%, #14387F 35%, #0095B3 75%, #00A24C 90%, #00937D 100%);"

st.set_page_config(page_title="Project Charter Reviewer", layout="wide")

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Roboto', sans-serif; }}
        
        /* Header */
        .header-container {{ position: fixed; top: 0; left: 0; width: 100%; height: 60px; background-color: #fff; z-index: 999; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; }}
        .supergraphic-bar {{ width: 100%; height: 8px; {SUPERGRAPHIC_CSS} }}
        .logo-bar {{ padding: 10px 20px; display: flex; align-items: center; height: 52px; }}
        header[data-testid="stHeader"] {{ display: none; }}
        .main .block-container {{ padding-top: 80px; max-width: 1200px; }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{ background-color: #f5f5f5; border-right: 1px solid #e0e0e0; }}
        
        /* Custom Cards */
        .section-card {{
            background-color: white;
            border: 1px solid #e0e0e0;
            border-left: 5px solid #00629a; /* Bosch Blue */
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            position: relative;
        }}
        
        .instruction-box {{
            background-color: #eff1f2;
            padding: 12px;
            font-size: 0.9em;
            color: #555;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 3px solid #bfc0c2;
        }}
        
        /* Alert Boxes */
        .alert-box {{
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .alert-high {{ background-color: #fdecea; border-left: 4px solid #ed0007; color: #b70006; }}
        .alert-medium {{ background-color: #fff4e5; border-left: 4px solid #ffaa00; color: #663c00; }}
        .alert-pass {{ background-color: #edf7ed; border-left: 4px solid #00a24c; color: #1e4620; }}

    </style>
""",
    unsafe_allow_html=True,
)

# Render Header
st.markdown(
    f"""
    <div class="header-container">
        <div class="supergraphic-bar"></div>
        <div class="logo-bar">
            {LOGO_HTML}
            <span style="font-size: 18px; color: #555; padding-left: 15px; border-left: 1px solid #ccc;">
                Project Charter AI Auditor
            </span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)


# --- 2. TEMPLATE DATABASE (MOCK) ---
TEMPLATES = {
    "Standard Project Charter": [
        {
            "title": "1. Reviewers",
            "criteria": "Reviewers: <Add here the name of the Q-PAR (for non-Focus Projects) or EPQ (for Focus Projects) as mandatory reviewer> (Q-PAR/EPQ). The author can decide to add additional reviewers.",
            "content": "Reviewers: <Add Name Here> (Q-PAR/EPQ)\nAdditional Reviewers: <Add Optional Name>",
        },
        {
            "title": "2. Problem Statement",
            "criteria": "Describe the current situation, the pain points, and the impact of the problem.",
            "content": "Current Situation: <Describe current process>\nPain Points: <List pain points>\nImpact: <Describe business impact>",
        },
        {
            "title": "3. Objectives",
            "criteria": "Define SMART goals. Must include at least one measurable KPI.",
            "content": "Goal 1: <Specific Goal>\nKPI: <Measurable Metric>\nTimeline: <Date>",
        },
    ],
    "Simple Document": [
        {
            "title": "1. Summary",
            "criteria": "Provide a brief summary of the document.",
            "content": "<Write summary here>",
        }
    ],
}


# --- 3. LOGIC FUNCTIONS ---
def load_template(template_name):
    """Loads a template into the session state."""
    st.session_state.sections = []
    if template_name in TEMPLATES:
        for tpl in TEMPLATES[template_name]:
            st.session_state.sections.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": tpl["title"],
                    "criteria": tpl["criteria"],
                    "content": tpl["content"],
                    "result": None,
                }
            )


def delete_section(index):
    """Removes a section by index."""
    if 0 <= index < len(st.session_state.sections):
        st.session_state.sections.pop(index)


def add_manual_section(title, criteria, content):
    """Adds a single user-defined section."""
    st.session_state.sections.append(
        {
            "id": str(uuid.uuid4()),
            "title": title,
            "criteria": criteria,
            "content": content,
            "result": None,
        }
    )


# --- 4. STATE MANAGEMENT ---
if "sections" not in st.session_state:
    st.session_state.sections = []

# --- 5. SIDEBAR (ACTIONS) ---
with st.sidebar:
    st.subheader("🛠️ Actions")

    tab_new, tab_manual = st.tabs(["📄 New from Template", "➕ Custom Section"])

    # TAB 1: TEMPLATE SELECTION
    with tab_new:
        selected_template = st.selectbox("Choose Template:", list(TEMPLATES.keys()))
        if st.button("Create Document", type="primary", use_container_width=True):
            with st.spinner("Loading Template..."):
                load_template(selected_template)
                st.rerun()

        st.info("⚠️ Creating a new document will clear current work.")

    # TAB 2: MANUAL CREATE
    with tab_manual:
        with st.form("create_section_form", clear_on_submit=True):
            new_title = st.text_input("Section Header", placeholder="e.g. 4.0 Risks")
            new_instr = st.text_area(
                "Instructions", placeholder="e.g. List top 3 risks...", height=100
            )
            new_content = st.text_area(
                "Content Template", placeholder="Risk 1: ...", height=100
            )

            if st.form_submit_button(
                "Add Section", type="primary", use_container_width=True
            ):
                if new_title:
                    add_manual_section(new_title, new_instr, new_content)
                    st.rerun()
                else:
                    st.error("Title is required.")

    st.divider()

    # CLEAR ALL
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.sections = []
        st.rerun()


# --- 6. MAIN CONTENT DASHBOARD ---
if not st.session_state.sections:
    st.info("👈 Please **Create a New Document** from the Sidebar to start.")

    st.markdown(
        """
    <div style="text-align: center; color: #ccc; margin-top: 50px;">
        <h3>No Document Loaded</h3>
        <p>Select a template to begin.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

else:
    st.subheader(f"Document Workspace ({len(st.session_state.sections)} Sections)")

    # Loop through sections
    for i, section in enumerate(st.session_state.sections):
        # --- SECTION CARD CONTAINER ---
        with st.container():
            st.markdown(
                f"""
            <div class="section-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#002742;">{section["title"]}</h3>
                </div>
                <div class="instruction-box">
                    <strong>Instructions & Criteria:</strong><br/>
                    {section["criteria"]}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Layout: Content (Left) | Actions (Right)
            c1, c2 = st.columns([2, 1])

            with c1:
                # EDITABLE CONTENT AREA
                st.markdown("**✏️ Content Editor:**")
                updated_content = st.text_area(
                    f"Content editor {i}",
                    value=section["content"],
                    height=200,
                    label_visibility="collapsed",
                    key=f"content_{section['id']}",
                )
                # Sync edits back to state immediately
                section["content"] = updated_content

            with c2:
                col_btn1, col_btn2 = st.columns([3, 1])

                with col_btn1:
                    # AUDIT BUTTON
                    if st.button(
                        f"🔍 Audit Section",
                        key=f"check_{section['id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        with st.spinner("Analyzing..."):
                            config = {"configurable": {"thread_id": section["id"]}}
                            # Input for Audit: No target_issue
                            inputs = {
                                "section_title": section["title"],
                                "document_text": section["content"],
                                "criteria": section["criteria"],
                                "issues": [],
                                "is_compliant": False,
                                "target_issue": None,
                            }
                            result = graph.invoke(inputs, config)
                            section["result"] = result
                            st.rerun()

                with col_btn2:
                    if st.button(
                        "❌", key=f"del_{section['id']}", help="Remove section"
                    ):
                        delete_section(i)
                        st.rerun()

                # --- DISPLAY RESULTS & AUTO-FIX UI ---
                if section.get("result"):
                    res = section["result"]

                    # If Fixer ran, it returns 'document_text' but maybe not full audit structure
                    # We need to handle the case where result is just text update (although graph returns state)

                    # 1. COMPLIANT STATE
                    if res.get("is_compliant", False):
                        st.markdown(
                            '<div class="alert-box alert-pass">✅ <strong>Compliant</strong></div>',
                            unsafe_allow_html=True,
                        )

                    # 2. ISSUES FOUND
                    elif res.get("issues"):
                        for issue in res["issues"]:
                            severity_class = (
                                "alert-high"
                                if issue["severity"] == "High"
                                else "alert-medium"
                            )

                            with st.container():
                                st.markdown(
                                    f"""
                                <div class="alert-box {severity_class}">
                                    <strong>⚠️ {issue["severity"]}</strong>: {issue["issue_description"]}<br>
                                    <em style="font-size:0.85em;">💡 {issue["recommendation"]}</em>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                # AUTO-FIX BUTTON
                                if st.button(
                                    "✨ Auto-Fix",
                                    key=f"fix_{section['id']}_{issue['id']}",
                                    use_container_width=True,
                                ):
                                    with st.spinner("Applying AI Fix..."):
                                        config = {
                                            "configurable": {"thread_id": section["id"]}
                                        }

                                        # Input for Fixer: Provide target_issue
                                        inputs = {
                                            "section_title": section["title"],
                                            "document_text": section["content"],
                                            "criteria": section["criteria"],
                                            "issues": [],  # Not needed for fixer but required by state
                                            "is_compliant": False,
                                            "target_issue": issue,  # <--- TRIGGER FIX
                                        }

                                        # Run Graph (routes to Fixer)
                                        fixed_result = graph.invoke(inputs, config)

                                        # Update Content
                                        section["content"] = fixed_result[
                                            "document_text"
                                        ]

                                        # Clear previous results so user sees the new text clearly
                                        section["result"] = None
                                        st.rerun()
