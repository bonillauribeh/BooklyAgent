import json
from datetime import date

# ---------------------------------------------------------------------------
# Mock order database
# ---------------------------------------------------------------------------

ORDERS = {
    "ORD-001": {
        "id": "ORD-001",
        "customer_name": "Alex Johnson",
        "status": "Processing",
        "items": [{"title": "Harry Potter and the Sorcerer's Stone", "quantity": 1}],
        "shipping_type": "standard",
        "order_date": "2026-06-10",
        "delivery_date": None,
        "address": "123 Main St, Austin, TX 78701",
        "final_sale": False,
    },
    "ORD-002": {
        "id": "ORD-002",
        "customer_name": "Maria Garcia",
        "status": "Shipped",
        "items": [{"title": "Harry Potter and the Chamber of Secrets", "quantity": 2}],
        "shipping_type": "express",
        "order_date": "2026-06-08",
        "delivery_date": None,
        "tracking_number": "TRK-789456123",
        "shipping_carrier": "FedEx",
        "address": "456 Oak Ave, Seattle, WA 98101",
        "final_sale": False,
    },
    "ORD-003": {
        "id": "ORD-003",
        "customer_name": "Sam Chen",
        "status": "Delivered",
        "items": [{"title": "Harry Potter and the Prisoner of Azkaban", "quantity": 1}],
        "shipping_type": "standard",
        "order_date": "2026-05-25",
        "delivery_date": "2026-06-01",  # 14 days ago — within 30-day return window
        "tracking_number": "TRK-334521987",
        "shipping_carrier": "UPS",
        "address": "789 Pine St, Chicago, IL 60601",
        "final_sale": False,
    },
    "ORD-004": {
        "id": "ORD-004",
        "customer_name": "Jordan Lee",
        "status": "Delivered",
        "items": [{"title": "Harry Potter and the Goblet of Fire", "quantity": 1}],
        "shipping_type": "standard",
        "order_date": "2026-04-01",
        "delivery_date": "2026-04-08",  # 68 days ago — outside 30-day return window
        "tracking_number": "TRK-112847563",
        "shipping_carrier": "USPS",
        "address": "321 Elm St, Boston, MA 02101",
        "final_sale": False,
    },
    "ORD-005": {
        "id": "ORD-005",
        "customer_name": "Taylor Kim",
        "status": "Delivered",
        "items": [{"title": "Harry Potter and the Order of the Phoenix", "quantity": 1}],
        "shipping_type": "express",
        "order_date": "2026-06-05",
        "delivery_date": "2026-06-07",  # 8 days ago — within window, but final sale
        "tracking_number": "TRK-998124305",
        "shipping_carrier": "FedEx",
        "address": "654 Maple Dr, Miami, FL 33101",
        "final_sale": True,
    },
}

# ---------------------------------------------------------------------------
# FAQ knowledge base
# ---------------------------------------------------------------------------

FAQ_ENTRIES = {
    "return_policy": (
        "Returns are accepted within 30 days of delivery. Items marked 'Final Sale' cannot be returned. "
        "Refunds are issued to the original payment method or as store credit — customer's choice."
    ),
    "shipping_times": (
        "Standard shipping takes 5–7 business days. Express shipping takes 2–3 business days. "
        "International shipping timelines vary — contact support for details."
    ),
    "order_modification": (
        "Orders can be modified or cancelled only while in 'Processing' status. "
        "Once an order has shipped, changes are no longer possible."
    ),
    "password_reset": (
        "To reset your password, go to Account Settings > Security > Reset Password. "
        "If you can't access your email, contact support to be escalated to the account team."
    ),
    "order_history": (
        "You can view your full order history by logging into your account and going to Account > Orders."
    ),
    "store_credit": (
        "Store credit is applied to your Bookly account automatically and can be used on any future order."
    ),
    "international_shipping": (
        "International shipping is available to select countries. For questions about a specific international "
        "order, please contact support — these cases are handled by the Bookly team directly."
    ),
}

# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_order_status(order_id: str) -> dict:
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"found": False, "message": f"No order found with ID '{order_id}'. Please double-check the order ID."}
    result = dict(order)
    result.setdefault("tracking_number", "Not available at this time")
    result.setdefault("shipping_carrier", "Not available at this time")

    # Surface the 30-day return window evaluation so the agent doesn't have to
    # infer "today" — it has no reliable current date otherwise.
    if order.get("delivery_date"):
        delivery_date = date.fromisoformat(order["delivery_date"])
        days_since_delivery = (date.today() - delivery_date).days
        result["days_since_delivery"] = days_since_delivery
        result["within_return_window"] = days_since_delivery <= 30
    else:
        result["days_since_delivery"] = None
        result["within_return_window"] = None

    return {"found": True, "order": result}


def initiate_return(order_id: str, reason: str, refund_type: str) -> dict:
    order = ORDERS.get(order_id.upper())

    if not order:
        return {"success": False, "reason": "order_not_found", "message": f"No order found with ID '{order_id}'."}

    if order["status"] != "Delivered":
        return {
            "success": False,
            "reason": "not_delivered",
            "message": f"Order {order_id} has status '{order['status']}' and cannot be returned yet — only delivered orders are eligible.",
        }

    if order["final_sale"]:
        return {
            "success": False,
            "reason": "final_sale",
            "message": f"Order {order_id} contains a Final Sale item and is not eligible for return or refund.",
        }

    delivery_date = date.fromisoformat(order["delivery_date"])
    days_since_delivery = (date.today() - delivery_date).days
    if days_since_delivery > 30:
        return {
            "success": False,
            "reason": "outside_return_window",
            "days_since_delivery": days_since_delivery,
            "message": (
                f"Order {order_id} was delivered {days_since_delivery} days ago, "
                "which is outside the 30-day return window."
            ),
        }

    refund_label = "original payment method" if refund_type == "original_payment" else "store credit"
    return {
        "success": True,
        "order_id": order_id,
        "return_id": f"RET-{order_id}-{date.today().strftime('%Y%m%d')}",
        "refund_type": refund_type,
        "message": (
            f"Return successfully initiated for order {order_id}. "
            f"A {refund_label} refund will be processed within 5–7 business days."
        ),
    }


def cancel_or_modify_order(order_id: str, action: str, modification_details: str = "") -> dict:
    order = ORDERS.get(order_id.upper())

    if not order:
        return {"success": False, "reason": "order_not_found", "message": f"No order found with ID '{order_id}'."}

    if order["status"] in ("Shipped", "Delivered"):
        return {
            "success": False,
            "reason": "already_shipped",
            "status": order["status"],
            "message": (
                f"Order {order_id} has already {order['status'].lower()} and can no longer be "
                f"{'cancelled' if action == 'cancel' else 'modified'}. "
                "If you'd like, you may be eligible to start a return instead."
            ),
        }

    if action == "cancel":
        return {
            "success": True,
            "action": "cancel",
            "order_id": order_id,
            "message": f"Order {order_id} has been successfully cancelled. You will receive a full refund within 5–7 business days.",
        }
    else:
        return {
            "success": True,
            "action": "modify",
            "order_id": order_id,
            "modification_applied": modification_details,
            "message": f"Order {order_id} has been updated: {modification_details}",
        }


def escalate_to_human(reason: str) -> dict:
    ticket_id = f"TKT-{abs(hash(reason)) % 900000 + 100000}"
    print(f"  [ESCALATION LOG] Ticket {ticket_id}: {reason}")
    return {
        "success": True,
        "ticket_id": ticket_id,
        "message": f"Escalation ticket {ticket_id} created. A human agent will follow up shortly.",
    }


def search_faq(query: str) -> dict:
    query_lower = query.lower()
    keywords = {
        "return_policy": ["return", "refund", "send back", "exchange"],
        "shipping_times": ["shipping", "delivery time", "how long", "arrive", "standard", "express"],
        "order_modification": ["cancel", "modify", "change", "edit", "update order"],
        "password_reset": ["password", "reset", "login", "sign in", "locked out", "security"],
        "order_history": ["order history", "past orders", "previous orders", "view orders"],
        "store_credit": ["store credit", "credit", "balance"],
        "international_shipping": ["international", "overseas", "outside", "country"],
    }

    matches = {}
    for key, terms in keywords.items():
        if any(term in query_lower for term in terms):
            matches[key] = FAQ_ENTRIES[key]

    if not matches:
        return {
            "found": False,
            "message": "No FAQ entries matched that query. This may need to be escalated to the Bookly team.",
        }
    return {"found": True, "results": matches}


# ---------------------------------------------------------------------------
# Tool dispatcher — called by agent.py
# ---------------------------------------------------------------------------

def execute_tool(name: str, inputs: dict) -> dict:
    if name == "get_order_status":
        return get_order_status(**inputs)
    elif name == "initiate_return":
        return initiate_return(**inputs)
    elif name == "cancel_or_modify_order":
        return cancel_or_modify_order(**inputs)
    elif name == "search_faq":
        return search_faq(**inputs)
    elif name == "escalate_to_human":
        return escalate_to_human(**inputs)
    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Tool schemas — passed to the Anthropic API
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "get_order_status",
        "description": "Look up the status and details of a customer order by order ID. Use this whenever a customer asks about their order, where it is, when it will arrive, or what it contains.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID provided by the customer (e.g. ORD-001).",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "initiate_return",
        "description": (
            "Initiate a return or refund for a delivered order. "
            "This tool enforces eligibility rules: 30-day window, no final-sale items. "
            "Only call this after confirming the order ID, return reason, and refund preference with the customer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to return."},
                "reason": {"type": "string", "description": "The customer's reason for the return."},
                "refund_type": {
                    "type": "string",
                    "enum": ["original_payment", "store_credit"],
                    "description": "How the customer wants to receive their refund.",
                },
            },
            "required": ["order_id", "reason", "refund_type"],
        },
    },
    {
        "name": "cancel_or_modify_order",
        "description": (
            "Cancel or modify an order. Only succeeds if the order is still in 'Processing' status. "
            "Only call this after getting explicit confirmation from the customer about what they want changed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to cancel or modify."},
                "action": {
                    "type": "string",
                    "enum": ["cancel", "modify"],
                    "description": "Whether to cancel the order or modify it.",
                },
                "modification_details": {
                    "type": "string",
                    "description": "For 'modify' actions: describe exactly what should be changed (e.g. 'Change shipping address to 99 New St, Denver, CO').",
                },
            },
            "required": ["order_id", "action"],
        },
    },
    {
        "name": "search_faq",
        "description": "Search Bookly's FAQ for policy information. Use this for questions about shipping times, return policy, password resets, store credit, order history, or anything not covered by order-specific tools.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The topic or question to look up (e.g. 'return policy', 'express shipping time', 'reset password').",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalate a customer issue to a human agent. Call this whenever escalation is required: "
            "damaged or incorrect items, complaints, out-of-scope requests, customer frustration, "
            "or an explicit request for a human. Pass a brief summary of the issue as the reason."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "A brief summary of the issue being escalated (e.g. 'Customer received a damaged copy of Atomic Habits, order ORD-003').",
                }
            },
            "required": ["reason"],
        },
    },
]
