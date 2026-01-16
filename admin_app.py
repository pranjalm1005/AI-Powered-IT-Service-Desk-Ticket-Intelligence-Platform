import json
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from lambda_client import (
    classify_ticket,
    get_all_tickets,
    update_ticket_status,
    get_ticket_by_id,
    get_resolved_tickets,
    generate_resolution_suggestion,     # NEW
    generate_it_summary                  # NEW
)

from utils import (
    validate_status,
    get_status_class,
    format_status_display,
    safe_get_ticket_field,
    normalize_ticket_data,
    parse_response_body,
    format_datetime,
    calculate_resolution_time,
    format_resolution_block,
    smart_format_ai_output
)

def smart_format_ai_output(output):
    """Clean and bullet-format AI output safely."""

    if not output:
        return "<p>No data returned.</p>"

    # If output is already a list → perfect
    if isinstance(output, list):
        bullets = "".join([f"<li>{str(item).strip()}</li>" for item in output])
        return f"<ul>{bullets}</ul>"

    # Try to convert string list → real list
    if isinstance(output, str):
        txt = output.strip()

        # Case 1: Looks like ["a","b","c"]
        if txt.startswith("[") and txt.endswith("]"):
            try:
                import ast
                parsed = ast.literal_eval(txt)
                if isinstance(parsed, list):
                    bullets = "".join([f"<li>{str(item).strip()}</li>" for item in parsed])
                    return f"<ul>{bullets}</ul>"
            except:
                pass

        # Case 2: Long text → split into lines
        lines = [l.strip("-• ").strip() for l in txt.split("\n") if l.strip()]
        bullets = "".join([f"<li>{line}</li>" for line in lines])
        return f"<ul>{bullets}</ul>"

    # Fallback
    return f"<p>{str(output)}</p>"

# ============================================================
#  ADMIN HEADER
# ============================================================
def render_admin_header():
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 2, 1])

    with left:
        st.image("static/nsight_logo.png", width=150)

    with center:
        st.markdown(
            "<h2 style='text-align:center; margin-top: 10px; color: #2c3e50;'>Nsight ITSM AI Assistant</h2>",
            unsafe_allow_html=True
        )

    with right:
        st.image(
            "https://download.logo.wine/logo/Amazon_Web_Services/Amazon_Web_Services-Logo.wine.png",
            width=150,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- GLOBAL SEARCH BAR ----------------
    col1, col2 = st.columns([4, 1])

    with col1:
        search_query = st.text_input(
            "🔎 Search Ticket",
            placeholder="Search by ID, Title, Email, Category, or Status...",
            key="admin_search_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("🔍 Search", use_container_width=True):
            if search_query and search_query.strip():
                st.session_state["search_triggered"] = True
                st.session_state["search_query"] = search_query.strip()
                st.rerun()


# ============================================================
#  GLOBAL SEARCH HANDLER
# ============================================================
def handle_global_search(query):
    tickets = st.session_state.get("admin_df", [])
    if not tickets:
        st.warning("No ticket data loaded.")
        return

    df = pd.DataFrame(tickets)
    q = query.lower()

    results = df[
        df.apply(
            lambda r: q in str(r.get("id", "")).lower()
            or q in str(r.get("title", "")).lower()
            or q in str(r.get("description", "")).lower()
            or q in str(r.get("user_email", "")).lower()
            or q in str(r.get("category", "")).lower()
            or q in str(r.get("status", "")).lower(),
            axis=1
        )
    ]

    if results.empty:
        st.warning(f"No results for **{query}**")
        return

    # Auto open if only one result
    if len(results) == 1:
        st.session_state["selected_ticket_id"] = results.iloc[0]["id"]
        st.session_state["show_ticket_modal"] = True
        st.session_state["search_triggered"] = False
        st.rerun()

    # Otherwise show results
    st.success(f"Found **{len(results)}** matching tickets")
    st.markdown("---")

    for _, row in results.iterrows():
        status = row.get("status", "open")
        if status not in ["open", "in_progress", "resolved"]:
            status = "open"

        status_class = f"status-{status.replace('_', '-')}"

        st.markdown(f"""
            <div class='ticket-card'>
                <div class='ticket-id'>🎫 {row['id']}</div>
                <div class='ticket-title'>{row['title']}</div>
                <div class='ticket-meta'>
                    <span>📧 {row['user_email']}</span> |
                    <span>📂 {row['category']}</span> |
                    <span class='status-badge {status_class}'>{status.upper()}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("👁️ View Details", key=f"search_view_{row['id']}"):
            st.session_state["selected_ticket_id"] = row["id"]
            st.session_state["show_ticket_modal"] = True
            st.session_state["search_triggered"] = False
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
#  ADMIN DASHBOARD VIEW
# ============================================================
def admin_dashboard():
    tickets = st.session_state.get("admin_df", [])
    df = pd.DataFrame(tickets)

    st.markdown("## 📊 Dashboard Analytics")

    if df.empty:
        st.info("No ticket data found.")
        return

    # ---------------- STATS CARDS ----------------
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
        <div class='metric-card'>
            <h3>Total Tickets</h3>
            <h1>{len(df)}</h1>
        </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
        <div class='metric-card'>
            <h3>Open</h3>
            <h1>{len(df[df.status=='open'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
        <div class='metric-card'>
            <h3>In Progress</h3>
            <h1>{len(df[df.status=='in_progress'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
        <div class='metric-card'>
            <h3>Resolved</h3>
            <h1>{len(df[df.status=='resolved'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- GRAPHS ----------------
    colA, colB = st.columns(2)

    with colA:
        st.markdown("### By Category")
        st.bar_chart(df["category"].value_counts())

    with colB:
        st.markdown("### Status Distribution")
        st.bar_chart(df["status"].value_counts())

    # ---------------- RECENT TICKETS ----------------
    st.markdown("### 🕒 Recent Tickets")
    recent = df.sort_values("created_at", ascending=False).head(5)

    for _, row in recent.iterrows():
        status = row.get("status", "open")
        if status not in ["open", "in_progress", "resolved"]:
            status = "open"

        status_class = f"status-{status.replace('_', '-')}"

        st.markdown(f"""
            <div class='ticket-card'>
                <div class='ticket-id'>🎫 {row['id']}</div>
                <div class='ticket-title'>{row['title']}</div>
                <div class='ticket-meta'>
                    <span>📧 {row['user_email']}</span> |
                    <span>📂 {row['category']}</span> |
                    <span class='status-badge {status_class}'>{status.upper()}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("👁️ View Details", key=f"recent_{row['id']}"):
            st.session_state["selected_ticket_id"] = row["id"]
            st.session_state["show_ticket_modal"] = True
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
#  TICKET MODAL — FULL DETAILS + AI PANELS
# ============================================================
def show_ticket_modal():
    ticket_id = st.session_state.get("selected_ticket_id")
    tickets_data = st.session_state.get("admin_df", [])

    if not ticket_id or not tickets_data:
        st.error("No ticket selected or data unavailable.")
        st.session_state["show_ticket_modal"] = False
        return

    # Load selected ticket
    df = pd.DataFrame(tickets_data)
    ticket_row = df[df["id"] == ticket_id]

    if ticket_row.empty:
        st.error(f"⚠ Ticket {ticket_id} not found")
        st.session_state["show_ticket_modal"] = False
        return

    ticket = normalize_ticket_data(ticket_row.iloc[0].to_dict())

    # ---------------- HEADER ----------------
    st.markdown(f"""
        <div class='ticket-header'>
            <h2 style='margin:0;'>🎫 Ticket Details</h2>
            <p style='margin:0; opacity:0.9;'>{ticket['id']}</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("✖ Close", key="close_modal", use_container_width=False):
        st.session_state["show_ticket_modal"] = False
        st.rerun()

    st.markdown("<div class='detail-container'>", unsafe_allow_html=True)

    # ============================================================
    # STATUS SECTION
    # ============================================================
    st.subheader("⚙️ Status Controls")

    col1, col2, col3 = st.columns([1.4, 1.4, 1])

    # --- Change Status ---
    with col1:
        current_status = ticket["status"]
        options = ["open", "in_progress", "resolved"]

        new_status = st.selectbox(
            "Update Status",
            options,
            index=options.index(current_status),
            key=f"status_editor_{ticket_id}"
        )

    # --- Apply Update ---
    with col2:
        st.write("")
        st.write("")  # spacing
        if st.button("💾 Save Status"):
            with st.spinner("Saving..."):
                update_ticket_status(ticket_id, new_status, st.session_state.email)
                st.success("✔ Status updated")

                # reload tickets
                resp = get_all_tickets()
                body = parse_response_body(resp)
                st.session_state["admin_df"] = body.get("tickets", [])
                st.rerun()

    # --- Refresh ---
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh"):
            resp = get_all_tickets()
            body = parse_response_body(resp)
            st.session_state["admin_df"] = body.get("tickets", [])
            st.rerun()

    st.markdown("---")

    # ============================================================
    # BASIC TICKET INFO
    # ============================================================
    st.subheader("📋 Ticket Information")

    colA, colB = st.columns(2)

    with colA:
        st.markdown(f"<div class='info-box'><strong>Title:</strong><br> {ticket['title']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'><strong>User Email:</strong><br> {ticket['user_email']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'><strong>Category:</strong><br> <code>{ticket['category']}</code></div>", unsafe_allow_html=True)

    with colB:
        status_class = f"status-{ticket['status'].replace('_','-')}"
        st.markdown(f"""
            <div class='info-box'>
                <strong>Status:</strong><br>
                <span class='status-badge {status_class}'>{ticket['status'].upper()}</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'><strong>Created At:</strong><br> {ticket['created_at']}</div>", unsafe_allow_html=True)

        resolved_val = ticket["resolved_at"] or "Not resolved"
        st.markdown(f"""
            <div class='info-box'>
                <strong>Resolved At:</strong><br> {resolved_val}
            </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # DESCRIPTION
    # ============================================================
    st.subheader("📝 Description")
    st.markdown(f"""
        <div style='background:#f8f9fa; padding:1rem; border-radius:8px; border:1px solid #ddd;'>
            {ticket['description']}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    #  AI — SIMILAR TICKETS
    # ============================================================
    st.subheader("🤖 Similar Tickets (AI Powered)")

    with st.spinner("Searching similar tickets..."):
        sim_resp = classify_ticket(ticket["description"])
        sim_body = parse_response_body(sim_resp)
        similar = sim_body.get("similar_tickets", [])

    if similar:
        for idx, sim in enumerate(similar[:5]):
            with st.expander(f"🎫 {sim['ticket_id']} — {sim['title']}  (Similarity: {round(sim['similarity'],2)})"):
                st.markdown(f"**Category:** {sim['category']}")
                st.markdown(f"**Description:** {sim['description'][:200]}...")

                if st.button(f"Open {sim['ticket_id']}", key=f"open_sim_btn_{idx}"):
                    st.session_state["selected_ticket_id"] = sim["ticket_id"]
                    st.rerun()
    else:
        st.info("No similar tickets found.")

    st.markdown("---")

    # ============================================================
    #  Utility: Clean + Format AI Output
    # ============================================================
    def clean_and_format_ai_output(text):
        """
        Fixes messy AI output:
        - Converts stringified list -> real list
        - Removes UUID prefixes
        - Splits long text into bullet points
        """
        import ast
        import re

        # ---------- Convert list-like strings ----------
        if isinstance(text, str) and text.strip().startswith("[") and text.strip().endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, list):
                    items = parsed
                else:
                    items = [text]
            except:
                items = [text]

        elif isinstance(text, list):
            items = text

        else:
            # Split long text by sentence or newlines
            items = re.split(r"\.\s+|\n+", text)

        # ---------- Clean items ----------
        cleaned = []
        for item in items:
            item = item.strip()
            if not item:
                continue

            # Remove UUID-like keys e.g. [6f2afd46-2db7-...]
            item = re.sub(r"\[[0-9a-fA-F\-]{36}\]", "", item).strip()

            cleaned.append(item)

        # ---------- Convert to HTML bullets ----------
        bullets = "".join([f"<li>{c}</li>" for c in cleaned])
        return f"<ul>{bullets}</ul>"


    # ============================================================
    #  AI — AUTOMATED RESOLUTION
    # ============================================================
    st.subheader("🔧 AI — Suggested Resolution")

    if st.button("⚡ Generate Resolution Suggestion", use_container_width=True):

        with st.spinner("Calling AI Model..."):
            res_resp = generate_resolution_suggestion(ticket_id)
            res_body = parse_response_body(res_resp)

            suggestion = (
                res_body.get("suggested_resolution")
                or res_body.get("suggestion")
                or res_body.get("resolution")
                or res_body.get("ai_suggestion")
                or "No suggestion generated."
            )

        st.success("AI Resolution Generated")

        formatted = smart_format_ai_output(suggestion)

        st.markdown(f"""
            <div style='background:#eef7ee;padding:1rem;border-radius:8px;
            border-left:4px solid #28a745;'>
                {formatted}
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")


    # ============================================================
    #  AI — IT SUMMARY
    # ============================================================
    st.subheader("🛠 IT Summary (AI Generated)")

    if st.button("📄 Generate IT Summary", use_container_width=True):
        with st.spinner("Generating IT Summary..."):

            it_resp = generate_it_summary(ticket_id)
            it_body = parse_response_body(it_resp)

            summary = (
                it_body.get("summary")
                or it_body.get("suggested_resolution")
                or it_body.get("ai_summary")
                or "No summary available."
            )

        st.success("IT Summary Ready")

        formatted_summary = smart_format_ai_output(summary)

        st.markdown(f"""
            <div style='background:#e9f3ff;padding:1rem;border-radius:8px;
            border-left:4px solid #3498db;'>
                {formatted_summary}
            </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # PAST RESOLVED CASES
    # ============================================================
    st.subheader("📚 Past Resolutions")

    with st.spinner("Fetching resolved tickets..."):
        r_resp = get_resolved_tickets()
        r_body = parse_response_body(r_resp)

    resolved_list = r_body.get("tickets", [])

    if resolved_list:
        for r in resolved_list[:5]:
            r = normalize_ticket_data(r)
            block = format_resolution_block(r)

            with st.expander(f"📁 {block['ticket_id']} — {block['title']}"):
                st.markdown(f"**User Steps:** {block['user_resolution_steps']}", unsafe_allow_html=True)
                st.markdown(f"**IT Steps:** {block['it_resolution_steps']}", unsafe_allow_html=True)
                st.markdown(f"**Resolved At:** {block['resolved_at']}")
                st.markdown(f"**Resolution Time:** {block['resolution_time']}")
    else:
        st.info("No resolved tickets found.")

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
#  ADMIN DASHBOARD
# ============================================================
def admin_dashboard():
    tickets = st.session_state.get("admin_df", [])
    df = pd.DataFrame(tickets)

    st.markdown("## 📊 Dashboard Analytics")

    if df.empty:
        st.info("No tickets available.")
        return

    # ------------------- KPI CARDS -------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
        <div class='metric-card'>
            <h3>Total Tickets</h3>
            <h1>{len(df)}</h1>
        </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
        <div class='metric-card' style='border-left-color:#ff9800;'>
            <h3>Open</h3>
            <h1>{len(df[df['status']=='open'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
        <div class='metric-card' style='border-left-color:#2196f3;'>
            <h3>In Progress</h3>
            <h1>{len(df[df['status']=='in_progress'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
        <div class='metric-card' style='border-left-color:#4caf50;'>
            <h3>Resolved</h3>
            <h1>{len(df[df['status']=='resolved'])}</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ------------------- CHARTS -------------------
    colA, colB = st.columns(2)

    with colA:
        st.markdown("### 📌 Tickets by Category")
        st.bar_chart(df["category"].value_counts())

    with colB:
        st.markdown("### 📈 Status Distribution")
        st.bar_chart(df["status"].value_counts())

    st.markdown("---")

    # ------------------- RECENT TICKETS -------------------
    st.markdown("### 🕒 Recent Tickets")
    recent = df.sort_values("created_at", ascending=False).head(6)

    for _, row in recent.iterrows():
        status = row.get("status", "open")
        if status not in ["open", "in_progress", "resolved"]:
            status = "open"

        status_class = f"status-{status.replace('_', '-')}"
        ticket_id = row["id"]

        st.markdown(f"""
            <div class='ticket-card'>
                <div class='ticket-id'>🎫 {ticket_id}</div>
                <div class='ticket-title'>{row['title']}</div>
                <div class='ticket-meta'>
                    <span>📧 {row['user_email']}</span> |
                    <span>📂 {row['category']}</span> |
                    <span class='status-badge {status_class}'>{status.upper()}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("👁️ View Details", key=f"dash_view_{ticket_id}"):
            st.session_state["selected_ticket_id"] = ticket_id
            st.session_state["show_ticket_modal"] = True
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
#  ADMIN TICKET LIST (AG GRID)
# ============================================================
def admin_ticket_list():
    st.title("🗂 All Tickets")

    resp = get_all_tickets()
    body = parse_response_body(resp)
    tickets = body.get("tickets", [])

    if not tickets:
        st.info("No tickets found.")
        return

    df = pd.DataFrame(tickets)
    st.session_state["admin_df"] = tickets

    # Format timestamps
    for c in ["created_at", "resolved_at"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.slice(0, 19)

    # Rename display columns
    df_display = df.rename(columns={
        "id": "Ticket ID",
        "title": "Title",
        "description": "Description",
        "category": "Category",
        "status": "Status",
        "user_email": "User Email",
        "created_at": "Created At",
        "resolved_at": "Resolved At",
        "resolved_by": "Resolved By",
    })

    gb = GridOptionsBuilder.from_dataframe(df_display)

    # Editable Status field
    gb.configure_column(
        "Status",
        editable=True,
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": ["open", "in_progress", "resolved"]},
        width=150
    )

    gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)
    gb.configure_grid_options(rowHeight=45, headerHeight=40)
    gb.configure_selection("single", use_checkbox=True)

    grid_options = gb.build()

    grid = AgGrid(
        df_display,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        theme="balham",
        fit_columns_on_grid_load=True,
    )

    updated_df = grid["data"]
    selected_rows = grid.get("selected_rows", [])

    # Normalize selected rows
    if isinstance(selected_rows, pd.DataFrame):
        selected_rows = selected_rows.to_dict("records")
    elif isinstance(selected_rows, dict):
        selected_rows = [selected_rows]
    elif not isinstance(selected_rows, list):
        selected_rows = []

    # Open ticket when clicking row
    if len(selected_rows) > 0:
        selected = selected_rows[0]
        selected_id = selected.get("Ticket ID")
        st.session_state["selected_ticket_id"] = selected_id
        st.session_state["show_ticket_modal"] = True
        st.rerun()

    # Save all changes
    if st.button("💾 Save All Changes", type="primary"):
        for _, row in updated_df.iterrows():
            update_ticket_status(row["Ticket ID"], row["Status"], st.session_state.email)

        st.success("✔ All changes saved!")
        st.rerun()


# ============================================================
#  ADMIN NAVIGATION
# ============================================================
# Add this to your admin_app.py file to replace the existing admin_navigation function

def admin_navigation():
    """
    Enhanced sidebar navigation for admin panel with icons and styling
    """
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);'>
            <h2 style='margin: 0; font-size: 1.4rem; font-weight: 600;'>
                🛠️ Admin Panel
            </h2>
            <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.7;'>
                Manage your ITSM platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation options with icons
    nav_options = {
        "🏠 Dashboard": {
            "icon": "📊",
            "label": "Dashboard",
            "description": "Overview & Analytics"
        },
        "🗂 All Tickets": {
            "icon": "🎫",
            "label": "All Tickets",
            "description": "Manage all tickets"
        }
    }
    
    # Store current selection
    if "admin_current_nav" not in st.session_state:
        st.session_state.admin_current_nav = "🏠 Dashboard"
    
    st.sidebar.markdown("### 📍 Navigation")
    
    selection = st.sidebar.radio(
        "Navigate to",
        list(nav_options.keys()),
        key="admin_nav_radio",
        label_visibility="collapsed",
        index=list(nav_options.keys()).index(st.session_state.admin_current_nav)
    )
    
    st.session_state.admin_current_nav = selection
    
    st.sidebar.markdown("---")
    
    # Admin info section
    st.sidebar.markdown("### 👤 Admin Info")
    st.sidebar.markdown(f"""
        <div style='background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; font-size: 0.85rem;'>
            <strong>Email:</strong><br>
            {st.session_state.email}
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Quick Stats in Sidebar
    st.sidebar.markdown("### 📈 Quick Stats")
    
    tickets = st.session_state.get("admin_df", [])
    if tickets:
        import pandas as pd
        df = pd.DataFrame(tickets)
        
        open_count = len(df[df['status'] == 'open'])
        progress_count = len(df[df['status'] == 'in_progress'])
        resolved_count = len(df[df['status'] == 'resolved'])
        
        st.sidebar.metric("Open Tickets", open_count, delta=None)
        st.sidebar.metric("In Progress", progress_count, delta=None)
        st.sidebar.metric("Resolved", resolved_count, delta=None)
    
    st.sidebar.markdown("---")
    
    # Help Section
    st.sidebar.markdown("### 💡 Quick Help")
    with st.sidebar.expander("📖 User Guide"):
        st.markdown("""
        **Dashboard:**
        - View ticket analytics
        - Monitor recent activity
        
        **All Tickets:**
        - Edit ticket status
        - View detailed information
        - Use AI-powered features
        """)
    
    with st.sidebar.expander("🔧 Features"):
        st.markdown("""
        - ✅ AI Ticket Classification
        - ✅ Similar Ticket Detection
        - ✅ Resolution Suggestions
        - ✅ IT Summary Generation
        - ✅ Search & Filter
        """)
    
    return selection

# ============================================================
#  ADMIN ROUTER — FINAL
# ============================================================
def admin_router():

    # Always fetch fresh tickets on first load
    resp = get_all_tickets()
    body = parse_response_body(resp)
    st.session_state["admin_df"] = body.get("tickets", [])

    # 1️⃣ Check if modal should open
    if st.session_state.get("show_ticket_modal"):
        show_ticket_modal()
        return

    # 2️⃣ Handle search mode
    if st.session_state.get("search_triggered", False):
        query = st.session_state.get("search_query", "")
        st.markdown(f"## 🔍 Search Results for: '{query}'")
        st.markdown("---")

        handle_global_search(query)

        if st.button("⬅ Back to Dashboard"):
            st.session_state["search_triggered"] = False
            st.session_state["search_query"] = ""
            st.rerun()
        return

    # 3️⃣ Sidebar Navigation
    section = admin_navigation()

    if section == "🏠 Dashboard":
        admin_dashboard()
    elif section == "🗂 All Tickets":
        admin_ticket_list()
