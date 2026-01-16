import boto3
import json

# -----------------------------------------
# Boto3 Lambda Client
# -----------------------------------------
lambda_client = boto3.client(
    "lambda",
    region_name="us-east-1"
)

# -----------------------------------------
# Generic Lambda Invocation Wrapper
# -----------------------------------------
def invoke_lambda(function_name, payload_dict):
    """
    Unified wrapper for invoking a Lambda safely.
    Handles:
    - AWS invocation errors
    - JSON string inside body
    - Missing fields
    """
    try:
        print(f"INVOKING: {function_name}")
        print(f"PAYLOAD: {payload_dict}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload_dict)
        )
    except Exception as e:
        print(f"LAMBDA INVOCATION ERROR: {e}")
        return {"error": f"Lambda Invocation Failed: {str(e)}"}

    raw = response["Payload"].read().decode("utf-8")
    print(f"RAW RESPONSE: {raw}")

    # Parse first-level Lambda JSON
    try:
        parsed = json.loads(raw)
    except Exception as e:
        print(f"JSON PARSE ERROR: {e}")
        return {"error": "Invalid top-level JSON", "raw": raw}

    # Parse body if nested JSON string
    if isinstance(parsed, dict) and "body" in parsed:
        body = parsed["body"]

        if isinstance(body, str):
            try:
                parsed["body"] = json.loads(body)
            except Exception:
                parsed["body"] = {"error": "Invalid body JSON", "raw": body}

    print(f"FINAL PARSED: {parsed}")
    return parsed


# =====================================================
# 📌 PRIMARY LAMBDA WRAPPERS
# =====================================================

def classify_ticket(text: str):
    """
    Classify ticket and find similar tickets
    FIXED: Now properly passes ticket_text parameter
    """
    return invoke_lambda("classify_ticket_lambda", {
        "ticket_text": text
    })


def create_ticket(title, description, category, user_email):
    """Create a new ticket"""
    return invoke_lambda("create_ticket_lambda", {
        "title": title,
        "description": description,
        "category": category,
        "user_email": user_email
    })


def get_latest_ticket(filters=None):
    """Get the most recent ticket"""
    return invoke_lambda("get_latest_ticket", filters or {})


def get_ticket_attachments(ticket_id: str):
    """Get attachments for a specific ticket"""
    return invoke_lambda("get_ticket_attachments", {
        "ticket_id": ticket_id
    })


def get_user_tickets(user_email):
    """Get all tickets for a specific user"""
    return invoke_lambda("get_user_tickets", {
        "user_email": user_email
    })


def get_ticket_by_id(ticket_id: str):
    """Get detailed information for a specific ticket"""
    return invoke_lambda("get_ticket_by_id", {
        "ticket_id": ticket_id
    })


def get_resolved_tickets():
    """Get all resolved tickets"""
    return invoke_lambda("get_resolved_tickets", {})


def search_similar_tickets(issue_text: str):
    """
    FIXED: Now uses text-based similarity search
    This should call search_similar_tickets Lambda (not classify_ticket)
    """
    return invoke_lambda("search_similar_tickets", {
        "query": issue_text
    })


def update_ticket_status(ticket_id, status, admin_email):
    """
    Update ticket status
    Lambda auto-updates:
    - last_update timestamp
    - resolved_at when status becomes resolved
    """
    return invoke_lambda("update_ticket_status", {
        "ticket_id": ticket_id,
        "status": status,
        "admin_email": admin_email
    })


def get_all_tickets():
    """Loads all tickets for admin dashboard"""
    return invoke_lambda("get_all_tickets", {})


# =====================================================
# OPTIONAL ADVANCED LAMBDAS (AI features)
# =====================================================

def generate_resolution_suggestion(ticket_id):
    """Generate AI-powered resolution suggestion"""
    return invoke_lambda("get_resolution_suggestion", {
        "ticket_id": ticket_id
    })


def generate_it_summary(ticket_id: str):
    """Generate IT summary for ticket"""
    return invoke_lambda("generate_it_summary", {
        "ticket_id": ticket_id
    })


# =====================================================
# TESTING HELPER
# =====================================================

def test_classification():
    """
    Test function to verify classification works
    """
    test_cases = [
        "I forgot my password and can't log in",
        "VPN is not connecting properly",
        "My invoice amount looks wrong",
        "I need a refund for last month",
        "The application keeps crashing",
        "I need access to the HR portal",
        "General help needed"
    ]
    
    print("\n" + "="*60)
    print("TESTING CLASSIFICATION")
    print("="*60)
    
    for test in test_cases:
        print(f"\nTesting: {test}")
        result = classify_ticket(test)
        
        if "body" in result:
            body = result["body"]
            if isinstance(body, dict):
                category = body.get("category", "ERROR")
                print(f"✓ Category: {category}")
            else:
                print(f"✗ Invalid body: {body}")
        else:
            print(f"✗ No body in response: {result}")


if __name__ == "__main__":
    # Run test when file is executed directly
    test_classification()