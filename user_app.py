import json
import streamlit as st
import pandas as pd

from lambda_client import (
    classify_ticket,
    create_ticket,
    get_user_tickets,
    get_ticket_by_id,
    search_similar_tickets,
)

from utils import (
    normalize_ticket_data,
    parse_response_body,
    format_resolution_block,
)

# -----------------------------------------------------
# KNOWLEDGE BASE (Self-help guidance)
# -----------------------------------------------------
SUGGESTION_KB = {
    "technical": [
        "Check VPN client version.",
        "Restart your network adapter.",
        "Try another network to rule out local issues.",
        "Attach VPN logs if problem persists.",
    ],
    "login_issue": [
        "Verify username & domain.",
        "Use the 'Forgot Password' link.",
        "Check MFA device connectivity.",
    ],
    "billing": [
        "Verify invoice & billing period.",
        "Check recent credits or discounts.",
        "Compare with previous month usage.",
    ],
    "refund": [
        "Verify refund eligibility.",
        "Confirm transaction ID & date.",
        "Prepare supporting documents.",
    ],
    "bug": [
        "Document steps to reproduce.",
        "Attach screenshots or logs.",
        "Check if bug occurs on another device.",
    ],
    "access_request": [
        "Ensure manager approval.",
        "Verify required security role.",
        "Specify App / Module / Access level.",
    ],
    "general_support": [
        "Check internal FAQ.",
        "Provide full issue details.",
    ],
}

# -----------------------------------------------------
# USER HEADER
# -----------------------------------------------------
def render_user_header():
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 2, 1])

    with left:
        st.image("static/nsight_logo.png", width=150)

    with center:
        st.markdown(
            "<h2 style='text-align:center;margin-top:10px;color:#2c3e50;'>"
            "Nsight ITSM AI Assistant"
            "</h2>",
            unsafe_allow_html=True,
        )

    with right:
        st.image(
            "https://download.logo.wine/logo/Amazon_Web_Services/"
            "Amazon_Web_Services-Logo.wine.png",
            width=150,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------
# NAVIGATION BAR
# -----------------------------------------------------
def render_nav():
    sim_count = len(st.session_state.get("similar_tickets", []))

    return st.radio(
        "Navigation",
        [
            "Raise Ticket",
            f"Similar Tickets ({sim_count})",
            "My Tickets",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

# -----------------------------------------------------
# TAB 1: RAISE NEW TICKET
# -----------------------------------------------------
def tab_raise_ticket():
    st.subheader("🎫 Raise New Ticket")

    user_email = st.session_state.email

    issue_text = st.text_area(
        "Describe your issue",
        height=180,
        placeholder="Explain the problem you are facing...",
    )

    # ---------------------------
    # AI CATEGORY + SIMILARITY CHECK
    # ---------------------------
    if st.button("🔍 Check Resolution", type="secondary"):

        if not issue_text.strip():
            st.error("Please enter an issue description.")
            return

        # 1️⃣ CLASSIFY TICKET CATEGORY
        with st.spinner("Analyzing issue using AI..."):
            resp = classify_ticket(issue_text)
            body = parse_response_body(resp)

        category = body.get("category", "general_support")

        st.session_state["last_category"] = category
        st.session_state["last_description"] = issue_text

        # 2️⃣ SIMILAR TICKET SEARCH (Embedding-based)
        similar_resp = search_similar_tickets(issue_text)
        sim_body = parse_response_body(similar_resp)

        st.session_state["similar_tickets"] = sim_body.get("similar_tickets", [])

        st.success(f"✓ Predicted Category: **{category}**")

        st.markdown("### 🛠 Troubleshooting Tips")
        for tip in SUGGESTION_KB.get(category, SUGGESTION_KB["general_support"]):
            st.markdown(f"- {tip}")

    # ---------------------------
    # TICKET CREATION AREA
    # ---------------------------
    st.markdown("---")
    st.markdown("### 📤 Submit Ticket")

    title = st.text_input(
        "Ticket Title",
        value=st.session_state.get("last_description", "")[:60],
    )

    final_category = st.session_state.get("last_category", "general_support")
    st.text_input("Category", value=final_category, disabled=True)

    if st.button("📨 Submit Ticket", type="primary"):

        if not st.session_state.get("last_description"):
            st.error("Please run **Check Resolution** first.")
            return

        if not title.strip():
            st.error("Please enter a ticket title.")
            return

        # CREATE THE TICKET
        with st.spinner("Creating ticket..."):
            resp = create_ticket(
                title,
                st.session_state["last_description"],
                final_category,
                user_email,
            )

        # ---- FIXED TICKET ID EXTRACTION ----
        ticket_id = "Unknown"
        try:
            if "body" in resp:
                body = resp["body"]
        
                # If body is JSON string → parse it
                if isinstance(body, str):
                    body = json.loads(body)
        
                # body is now dict
                ticket_id = body.get("ticket_id") or body.get("id") or "Unknown"
                
                st.success(f"🎉 Ticket Created Successfully! ID: **{ticket_id}**")
                
                # Clear the form
                st.session_state["last_category"] = None
                st.session_state["last_description"] = None
                st.session_state["similar_tickets"] = []
        
        except Exception as e:
            st.error(f"Error creating ticket: {e}")


# -----------------------------------------------------
# TAB 2 — SIMILAR TICKETS
# -----------------------------------------------------
def tab_similar_tickets():
    st.subheader("📑 Similar Tickets")

    similar_tickets = st.session_state.get("similar_tickets", [])

    if not similar_tickets:
        st.info("No similar tickets found. Please run 'Check Resolution' first.")
        return

    for idx, sim in enumerate(similar_tickets):
        tid = sim.get("ticket_id") or sim.get("id")
        title = sim.get("title", "No title")
        score = round(sim.get("similarity_score", 0), 2)

        with st.expander(f"🎫 {tid} — {title} (Similarity: {score})"):

            st.markdown(f"**Category:** `{sim.get('category', 'N/A')}`")
            st.markdown(f"**Description:** {sim.get('description', 'N/A')[:200]}...")

            # Troubleshooting Tips
            tips = SUGGESTION_KB.get(sim.get("category"), SUGGESTION_KB["general_support"])
            if tips:
                st.markdown("### 🛠 Steps You Can Try")
                for t in tips:
                    st.markdown(f"- {t}")

            # Fetch full ticket details
            if st.button("View Full Resolution", key=f"view_sim_{idx}"):
                with st.spinner("Fetching resolution summary..."):
                    resp = get_ticket_by_id(tid)
                    ticket_body = parse_response_body(resp)
                    ticket = normalize_ticket_data(ticket_body.get("ticket", {}))

                    block = format_resolution_block(ticket)

                # Display resolution summary
                st.markdown("---")
                st.markdown("### 🛠 Resolution Summary")
                st.markdown(f"**User Steps:**<br>{block['user_resolution_steps']}", unsafe_allow_html=True)
                st.markdown(f"**IT Steps:**<br>{block['it_resolution_steps']}", unsafe_allow_html=True)
                st.markdown(f"**Resolved At:** {block['resolved_at']}")
                st.markdown(f"**Resolution Time:** {block['resolution_time']}")


# -----------------------------------------------------
# TAB 3 — MY TICKETS (FIXED)
# -----------------------------------------------------
def tab_my_tickets():
    st.subheader("📁 My Tickets")
    
    user_email = st.session_state.get("email")
    
    if not user_email:
        st.error("User email not found in session. Please log in again.")
        return

    # Add refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Fetch tickets with error handling
    with st.spinner("Loading your tickets..."):
        try:
            resp = get_user_tickets(user_email)
            
            # Debug: Show raw response
            with st.expander("🔍 Debug Info"):
                st.write("**User Email:**", user_email)
                st.write("**Raw Response:**", resp)
            
            body = parse_response_body(resp)
            
            # Try multiple possible keys
            tickets = (
                body.get("tickets") or 
                body.get("items") or 
                body.get("data") or 
                []
            )
            
            # Debug: Show parsed body
            with st.expander("🔍 Parsed Body"):
                st.json(body)
            
        except Exception as e:
            st.error(f"Error fetching tickets: {e}")
            st.write("**Full error:**", str(e))
            return

    if not tickets:
        st.info("No tickets found for your account.")
        st.markdown("""
            **Possible reasons:**
            - You haven't created any tickets yet
            - Your email might not match the tickets in the database
            - There might be a database connection issue
            
            Try creating a new ticket in the "Raise Ticket" tab.
        """)
        return

    # Convert to DataFrame
    try:
        df = pd.DataFrame(tickets)
        
        # Normalize data
        for ticket in tickets:
            ticket = normalize_ticket_data(ticket)
        
        # Format timestamps
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].astype(str).str.slice(0, 19)
        
        if "resolved_at" in df.columns:
            df["resolved_at"] = df["resolved_at"].astype(str).str.slice(0, 19)

        # Rename columns for display
        df_display = df.rename(columns={
            "id": "Ticket ID",
            "title": "Title",
            "description": "Description",
            "category": "Category",
            "status": "Status",
            "created_at": "Created At",
        })
        
        # Select only columns that exist
        display_cols = []
        for col in ["Ticket ID", "Title", "Category", "Status", "Created At"]:
            if col in df_display.columns:
                display_cols.append(col)
        
        st.dataframe(
            df_display[display_cols],
            use_container_width=True,
            hide_index=True
        )

        # Ticket selection
        st.markdown("---")
        st.markdown("### 📋 View Ticket Details")
        
        ticket_ids = df_display["Ticket ID"].tolist()
        selected = st.selectbox("Select a Ticket", ticket_ids)

        if st.button("🔍 Open Ticket Details", type="primary"):
            with st.spinner("Loading ticket details..."):
                try:
                    resp = get_ticket_by_id(selected)
                    body = parse_response_body(resp)
                    ticket = normalize_ticket_data(body.get("ticket", {}))

                    st.markdown("---")
                    st.subheader(f"🎫 Ticket {selected}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Title:** {ticket['title']}")
                        st.markdown(f"**Category:** `{ticket['category']}`")
                        st.markdown(f"**Status:** {ticket['status']}")
                    
                    with col2:
                        st.markdown(f"**Created At:** {ticket['created_at']}")
                        st.markdown(f"**User:** {ticket['user_email']}")

                    st.markdown("---")
                    st.markdown("### 📝 Description")
                    st.markdown(ticket["description"])

                    st.markdown("---")
                    st.markdown("### 🛠 Resolution Summary")
                    block = format_resolution_block(ticket)

                    st.markdown(f"**User Steps:**<br>{block['user_resolution_steps']}", unsafe_allow_html=True)
                    st.markdown(f"**IT Steps:**<br>{block['it_resolution_steps']}", unsafe_allow_html=True)
                    st.markdown(f"**Resolved At:** {block['resolved_at']}")
                    st.markdown(f"**Resolution Time:** {block['resolution_time']}")
                    
                except Exception as e:
                    st.error(f"Error loading ticket details: {e}")
    
    except Exception as e:
        st.error(f"Error displaying tickets: {e}")
        st.write("**Tickets data:**", tickets)


# -----------------------------------------------------
# USER ROUTER
# -----------------------------------------------------
def user_router():
    nav = render_nav()

    if nav == "Raise Ticket":
        tab_raise_ticket()
    elif "Similar Tickets" in nav:
        tab_similar_tickets()
    elif nav == "My Tickets":
        tab_my_tickets()