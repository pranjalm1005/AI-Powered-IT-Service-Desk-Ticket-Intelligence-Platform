"""
Utility functions for the ITSM application
"""

import json
from datetime import datetime, timedelta
import pandas as pd
import re
# -------------------------------------------------------------
# Status Utilities
# -------------------------------------------------------------

def validate_status(status):
    valid_statuses = ['open', 'in_progress', 'resolved', 'closed']

    if status is None or status not in valid_statuses:
        return 'open'

    return status


def get_status_class(status):
    status = validate_status(status)
    return f"status-{status.replace('_', '-')}"


def format_status_display(status):
    status = validate_status(status)
    return status.upper().replace('_', ' ')


# -------------------------------------------------------------
# Ticket Field Helpers
# -------------------------------------------------------------

def safe_get_ticket_field(ticket, field, default='N/A'):
    value = ticket.get(field, default)

    if value is None or (isinstance(value, str) and not value.strip()):
        return default

    return value


def normalize_ticket_data(ticket):
    """
    Ensures all critical fields exist for UI consumption.
    Compatible with updated Lambdas including:
    - resolved_at
    - last_update
    - updated_at
    - resolution steps
    - attachments
    """

    defaults = {
        'id': 'Unknown',
        'title': 'Untitled',
        'description': 'No description provided',
        'user_email': 'Unknown User',
        'category': 'unknown',
        'status': 'open',

        # New timestamps
        'created_at': 'N/A',
        'updated_at': 'N/A',
        'last_update': 'N/A',
        'resolved_at': None,
        'resolved_by': None,

        # AI fields
        'similarity_score': 0,

        # Attachments
        'attachments': [],

        # Resolution fields
        'user_resolution_steps': '',
        'it_resolution_steps': ''
    }

    # Inject defaults without overwriting existing values
    for key, default_value in defaults.items():
        ticket.setdefault(key, default_value)

    # Normalize status
    ticket["status"] = validate_status(ticket["status"])

    # Fix DB issue: resolved_at coming as boolean
    if isinstance(ticket["resolved_at"], bool):
        ticket["resolved_at"] = None

    return ticket


# -------------------------------------------------------------
# Date / Time Formatting Utilities
# -------------------------------------------------------------

def parse_iso(date_str):
    """Safely parse ISO timestamp"""
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        return datetime.fromisoformat(date_str.replace("Z", ""))
    except Exception:
        return None


def format_datetime(date_str):
    dt = parse_iso(date_str)
    if not dt:
        return "N/A"
    return dt.strftime("%d %b %Y, %I:%M %p")


def calculate_resolution_time(created, resolved):
    """Return human-readable duration"""
    start = parse_iso(created)
    end = parse_iso(resolved)

    if not start or not end:
        return "N/A"

    diff = end - start
    hours = diff.total_seconds() // 3600
    minutes = (diff.total_seconds() % 3600) // 60

    return f"{int(hours)}h {int(minutes)}m"


# -------------------------------------------------------------
# Response Normalization
# -------------------------------------------------------------

def parse_response_body(response):
    """
    Normalize Lambda "body", even if Lambda returned:
    body = '{"tickets": [...]}'
    """
    try:
        body = response.get("body", {})
        if isinstance(body, str):
            return json.loads(body)
        if isinstance(body, dict):
            return body
        return {}
    except Exception:
        return {}


def normalize_tickets(ticket_list):
    """
    Apply normalization to entire ticket list
    """
    out = []
    for t in ticket_list or []:
        out.append(normalize_ticket_data(t))
    return out


# -------------------------------------------------------------
# Similar Ticket Ranking Utilities
# -------------------------------------------------------------

def sort_similar_tickets(similar_list):
    if not similar_list:
        return []
    return sorted(
        similar_list,
        key=lambda x: float(x.get("similarity_score", 0)),
        reverse=True
    )


# -------------------------------------------------------------
# Attachment Formatting (NEW)
# -------------------------------------------------------------

def format_attachments(attachments):
    out = []
    for a in attachments or []:
        out.append({
            "id": a.get("id"),
            "file_name": a.get("file_name"),
            "s3_key": a.get("s3_key"),
            "uploaded_at": format_datetime(a.get("uploaded_at"))
        })
    return out


# -------------------------------------------------------------
# Search Query Validation
# -------------------------------------------------------------

def validate_search_query(query):
    if not query or not isinstance(query, str):
        return None
    query = query.strip()
    if len(query) == 0:
        return None
    return query[:200]  # Safety limit


# -------------------------------------------------------------
# Resolution Formatting Helpers (UPDATED)
# -------------------------------------------------------------

def format_resolution_block(ticket):
    """
    Return structured resolution details for UI including:
    - user steps
    - IT steps
    - timestamps
    - resolution duration
    - cleaned attachments
    """
    ticket = normalize_ticket_data(ticket)

    return {
        "ticket_id": ticket["id"],
        "title": ticket["title"],
        "user_resolution_steps": ticket.get("user_resolution_steps") or "No user steps",
        "it_resolution_steps": ticket.get("it_resolution_steps") or "No IT steps",
        "resolved_at": format_datetime(ticket.get("resolved_at")),
        "resolution_time": calculate_resolution_time(
            ticket.get("created_at"),
            ticket.get("resolved_at")
        ),
        "attachments": format_attachments(ticket.get("attachments", []))
    }


def clean_and_format_ai_output(text):
    """
    Cleans and formats AI output into bullet points.
    Works for:
    - strings
    - lists
    - multiline text
    """

    # ---------------- LIST HANDLING --------------------
    if isinstance(text, list):
        items = []
        for t in text:
            cleaned = str(t).strip()

            # Remove IDs like: [6f2afd46/...]
            cleaned = cleaned.split("]")[-1].strip()

            if cleaned:
                items.append(f"<li>{cleaned}</li>")

        return f"<ul>{''.join(items)}</ul>"

    # ---------------- STRING HANDLING --------------------
    if isinstance(text, str):

        # Remove ID prefix patterns
        if "]" in text:
            text = text.split("]")[-1].strip()

        # Split long text into bullet-like lines if separated by ". " or newlines
        parts = [p.strip() for p in text.replace("\n", ". ").split(". ") if p.strip()]

        if len(parts) > 1:
            return "<ul>" + "".join([f"<li>{p}</li>" for p in parts]) + "</ul>"

        return f"<p>{text}</p>"

    return f"<p>{text}</p>"


def smart_format_ai_output(raw_text):
    """
    Fixes messy AI responses by merging numbered steps, removing broken lines,
    and formatting into clean bullets.
    """

    if not raw_text:
        return "<p>No suggestion available.</p>"

    # Convert list into one text block
    if isinstance(raw_text, list):
        raw_text = " ".join([str(x) for x in raw_text])

    # Normalize spacing
    text = raw_text.replace("\n", " ").replace("•", "").strip()

    # Remove "Bot:" or similar junk
    text = re.sub(r"^bot[:\- ]*", "", text, flags=re.IGNORECASE)

    # Split into step blocks using digits: 
    parts = re.split(r"\s*(?<!\d)(\d+)\s*[\.\-\)]?\s*", text)

    # The regex returns: ['', '1', 'Step1 text...', '2', 'Step2 text...', ...]
    steps = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.isdigit():
            # Start of new step
            if current:
                steps.append(current.strip())
            current = ""
        else:
            current += " " + part

    if current:
        steps.append(current.strip())

    # Fallback if nothing meaningful extracted
    if not steps:
        return f"<p>{text}</p>"

    # Build clean HTML bullet list
    bullet_html = "<ul>"
    for step in steps:
        bullet_html += f"<li>{step}</li>"
    bullet_html += "</ul>"

    return bullet_html
