# app/components/global_audit.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from html import escape as html_escape
from typing import Any, Dict, List, Tuple

import streamlit as st

from app.state_manager import (
    get_global_audit_result,
    get_sections,
    update_global_audit_result,
    update_section_audit_result,
)
from backend.graph.workflow import run_batch_audit


SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
SEVERITY_STYLE = {
    "High": {"cls": "ga-high", "label": "HIGH"},
    "Medium": {"cls": "ga-med", "label": "MEDIUM"},
    "Low": {"cls": "ga-low", "label": "LOW"},
}


def _inject_styles() -> None:
    st.markdown(
        """
<style>
/* Keep styles scoped by prefix "ga-" */
.ga-shell { padding: 0.25rem 0; }

.ga-header {
  border: 1px solid rgba(49, 51, 63, 0.15);
  border-radius: 12px;
  padding: 14px 14px 10px 14px;
  background: rgba(255,255,255,0.6);
}

.ga-card {
  border: 1px solid rgba(49, 51, 63, 0.15);
  border-radius: 10px;
  padding: 12px 12px;
  margin: 8px 0;
  background: #ffffff;
}

.ga-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ga-badge {
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(49,51,63,0.18);
}

.ga-high { background: rgba(237, 0, 7, 0.10); border-color: rgba(237, 0, 7, 0.25); }
.ga-med  { background: rgba(245, 166, 35, 0.14); border-color: rgba(245, 166, 35, 0.30); }
.ga-low  { background: rgba(0, 122, 255, 0.12); border-color: rgba(0, 122, 255, 0.25); }

.ga-title {
  font-weight: 650;
  color: rgba(49, 51, 63, 0.95);
}

.ga-desc {
  margin-top: 6px;
  color: rgba(49, 51, 63, 0.85);
  line-height: 1.35;
}

.ga-meta {
  margin-top: 6px;
  color: rgba(49, 51, 63, 0.60);
  font-size: 0.85rem;
}

.ga-divider { margin: 0.35rem 0 0.2rem 0; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _collect_section_issues(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for sec in sections:
        last_audit = (sec.get("user_data") or {}).get("last_audit")
        if not last_audit:
            continue
        if last_audit.get("is_compliant") is True:
            continue

        for issue in last_audit.get("issues", []) or []:
            enriched = dict(issue)
            enriched["_section_title"] = (sec.get("meta") or {}).get("title", "Untitled section")
            enriched["_section_id"] = sec.get("id")
            issues.append(enriched)
    return issues


def _sort_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        issues,
        key=lambda x: (
            SEVERITY_ORDER.get(x.get("severity", "Low"), 2),
            (x.get("_section_title") or ""),
            (x.get("issue_description") or x.get("description") or ""),
        ),
    )


def _render_issue_card(
    *,
    severity: str,
    title: str,
    description: str,
    link_text: str | None = None,
    link_href: str | None = None,
    meta: str | None = None,
) -> None:
    sev = severity if severity in SEVERITY_STYLE else "Low"
    badge = SEVERITY_STYLE[sev]["label"]
    cls = SEVERITY_STYLE[sev]["cls"]

    title_html = html_escape(title)
    desc_html = html_escape(description)

    link_html = ""
    if link_text and link_href:
        link_html = f' • <a href="{html_escape(link_href)}">{html_escape(link_text)}</a>'

    meta_html = f'<div class="ga-meta">{html_escape(meta)}{link_html}</div>' if meta else (f'<div class="ga-meta">{link_html[3:]}</div>' if link_html else "")

    st.markdown(
        f"""
<div class="ga-card">
  <div class="ga-row">
    <span class="ga-badge {cls}">{badge}</span>
    <div class="ga-title">{title_html}</div>
  </div>
  <div class="ga-desc">{desc_html}</div>
  {meta_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def _run_global_audit(sections: List[Dict[str, Any]]) -> None:
    st.session_state["ga_running"] = True
    try:
        with st.spinner("Reviewing the entire document…"):
            results = run_batch_audit(sections)

        for sec_id, audit_res in (results.get("section_results") or {}).items():
            update_section_audit_result(sec_id, audit_res)

        update_global_audit_result(results.get("global_result") or {})
        st.session_state["ga_last_run"] = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    finally:
        st.session_state["ga_running"] = False

    st.rerun()


def render_global_feedback() -> None:
    _inject_styles()

    if "ga_running" not in st.session_state:
        st.session_state["ga_running"] = False

    sections = get_sections() or []
    global_result = get_global_audit_result() or {}

    section_issues = _collect_section_issues(sections)
    global_issues = global_result.get("global_issues", []) or []
    is_consistent = bool(global_result.get("is_consistent"))

    total_issues = len(section_issues) + len(global_issues)
    critical_count = sum(1 for i in section_issues if i.get("severity") == "High")
    affected_sections = len({i.get("_section_id") for i in section_issues if i.get("_section_id")})

    # ---- Header (action + context) ----
    with st.container():
        st.markdown('<div class="ga-header">', unsafe_allow_html=True)
        left, right = st.columns([5, 2], vertical_alignment="center")

        with left:
            st.subheader("Document review")
            st.caption("Run a full review across all sections (completeness + cross-section consistency).")
            last_run = st.session_state.get("ga_last_run")
            if last_run:
                st.caption(f"Last run: {last_run}")

        with right:
            disabled = (not sections) or st.session_state["ga_running"]
            if st.button(
                "Review document",
                type="primary",
                use_container_width=True,
                disabled=disabled,
            ):
                _run_global_audit(sections)

            if not sections:
                st.caption("Create/load a template to enable review.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Empty state ----
    if total_issues == 0 and not global_result:
        st.info("No review results yet. Click “Review document” when your sections are ready.")
        st.divider()
        return

    # ---- Success state ----
    if total_issues == 0 and is_consistent:
        st.success("No issues found. The document looks consistent across sections.")
        st.divider()
        return

    # ---- Results container (Expandable) ----
    with st.expander("Analysis Results", expanded=True):
        # ---- Metrics (fast scan) ----
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total issues", total_issues)
        m2.metric("High severity", critical_count)
        m3.metric("Logic issues", len(global_issues))
        m4.metric("Sections affected", affected_sections)

        # ---- Controls ----
        c1, c2, c3 = st.columns([2, 2, 3], vertical_alignment="center")
        with c1:
            sev_filter = st.multiselect(
                "Severity",
                options=["High", "Medium", "Low"],
                default=["High", "Medium", "Low"],
            )
        with c2:
            show_only_actionable = st.toggle("Only items with a section link", value=False)
        with c3:
            query = st.text_input("Search issues", placeholder="e.g., placeholder, empty, contradiction…").strip().lower()

        # ---- Tabs for mental model ----
        tab_all, tab_logic, tab_sections = st.tabs(
            [
                f"All ({total_issues})",
                f"Logic ({len(global_issues)})",
                f"By section ({affected_sections})",
            ]
        )

        # ---- ALL ----
        with tab_all:
            merged: List[Tuple[str, Dict[str, Any]]] = []
            for gi in global_issues:
                merged.append(("global", gi))
            for si in section_issues:
                merged.append(("section", si))

            # Normalize severity for global issues
            normalized: List[Dict[str, Any]] = []
            for kind, item in merged:
                if kind == "global":
                    normalized.append(
                        {
                            "kind": "global",
                            "severity": "Medium",  # default; adjust if your global issues have severity later
                            "title": item.get("title", "Logic issue"),
                            "description": item.get("description", ""),
                            "related_sections": item.get("related_sections") or [],
                        }
                    )
                else:
                    normalized.append(
                        {
                            "kind": "section",
                            "severity": item.get("severity", "Low"),
                            "title": item.get("_section_title", "Section issue"),
                            "description": item.get("issue_description") or item.get("description") or "",
                            "section_id": item.get("_section_id"),
                        }
                    )

            # Apply filters
            filtered: List[Dict[str, Any]] = []
            for it in normalized:
                if it["severity"] not in sev_filter:
                    continue

                if show_only_actionable and it.get("kind") == "global" and not it.get("related_sections"):
                    continue
                if show_only_actionable and it.get("kind") == "section" and not it.get("section_id"):
                    continue

                blob = f'{it.get("title","")} {it.get("description","")}'.lower()
                if query and query not in blob:
                    continue

                filtered.append(it)

            filtered.sort(key=lambda x: SEVERITY_ORDER.get(x.get("severity", "Low"), 2))

            if not filtered:
                st.info("No issues match the current filters.")
            else:
                for it in filtered:
                    if it["kind"] == "section":
                        sec_id = it.get("section_id")
                        _render_issue_card(
                            severity=it["severity"],
                            title=it["title"],
                            description=it["description"],
                            link_text="Jump to section" if sec_id else None,
                            link_href=f"#section-{sec_id}" if sec_id else None,
                            meta="Section finding",
                        )
                    else:
                        related = it.get("related_sections") or []
                        # Try to map related section titles -> anchors
                        links = []
                        for sec_name in related:
                            target = next((s for s in sections if (s.get("meta") or {}).get("title") == sec_name), None)
                            if target and target.get("id"):
                                links.append(f'<a href="#section-{html_escape(target["id"])}">{html_escape(sec_name)}</a>')
                            else:
                                links.append(html_escape(sec_name))

                        meta = "Logic finding"
                        if links:
                            meta = f"Logic finding • Affects: " + " | ".join(links)
                        
                        _render_issue_card(
                            severity="Medium",
                            title=it["title"],
                            description=it["description"],
                            meta=meta,
                        )

        # ---- LOGIC ----
        with tab_logic:
            if not global_issues:
                st.info("No cross-section logic issues detected.")
            else:
                for gi in global_issues:
                    title = gi.get("title", "Logic & consistency issue")
                    desc = gi.get("description", "")
                    related = gi.get("related_sections") or []

                    links_txt = None
                    links_href = None
                    if related:
                        # If exactly one related section, provide a direct jump
                        if len(related) == 1:
                            target = next((s for s in sections if (s.get("meta") or {}).get("title") == related[0]), None)
                            if target and target.get("id"):
                                links_txt = f"Jump to “{related[0]}”"
                                links_href = f"#section-{target['id']}"

                    _render_issue_card(
                        severity="Medium",
                        title=title,
                        description=desc,
                        link_text=links_txt,
                        link_href=links_href,
                        meta=("Affects: " + ", ".join(related)) if related else "Affects: (not mapped to a section)",
                    )

        # ---- BY SECTION ----
        with tab_sections:
            if not section_issues:
                st.info("No section-level issues detected.")
            else:
                grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                title_by_id: Dict[str, str] = {}
                for it in section_issues:
                    sec_id = it.get("_section_id") or "unknown"
                    grouped[sec_id].append(it)
                    title_by_id[sec_id] = it.get("_section_title", "Untitled section")

                # Sort sections by worst severity
                def worst_rank(items: List[Dict[str, Any]]) -> int:
                    return min(SEVERITY_ORDER.get(i.get("severity", "Low"), 2) for i in items)

                sec_items = sorted(grouped.items(), key=lambda kv: (worst_rank(kv[1]), title_by_id.get(kv[0], "")))

                for sec_id, items in sec_items:
                    items_sorted = _sort_issues(items)
                    worst = items_sorted[0].get("severity", "Low") if items_sorted else "Low"
                    sec_title = title_by_id.get(sec_id, "Untitled section")
                    count = len(items_sorted)

                    with st.expander(f"{sec_title} • {count} issue(s) • Worst: {worst}", expanded=(worst == "High")):
                        if sec_id != "unknown":
                            st.markdown(f'[Jump to section](#section-{sec_id})')
                        for it in items_sorted:
                            _render_issue_card(
                                severity=it.get("severity", "Low"),
                                title=it.get("_section_title", sec_title),
                                description=it.get("issue_description") or it.get("description") or "",
                                link_text="Jump to section" if sec_id != "unknown" else None,
                                link_href=f"#section-{sec_id}" if sec_id != "unknown" else None,
                                meta="Section finding",
                            )

    st.divider()
