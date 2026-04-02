import os
import sys
from google import genai
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tools.order_tools  import get_order_details, check_return_eligibility, get_refund_status
from tools.policy_tools import search_policy
from tools.record_tools import approve_refund, reject_refund, cancel_order, log_escalation, create_new_order
from agent.decision_rules import (
    can_auto_approve_refund,
    is_within_return_window,
    should_escalate,
    get_membership_benefits,
    classify_issue,
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def gemini_reply(prompt: str) -> str:
    """Send a prompt to Gemini and return the text reply."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


def classify_intent(state: dict) -> dict:
    """
    Node 1 — Classify what the customer wants.
    Uses Gemini for accurate classification.
    """
    message = state["user_message"]

    prompt = f"""
You are an intent classifier for a customer support voice agent at an e-commerce company.

Classify the customer message into exactly one of these intents:
- order_query       (asking about order status, location, delivery)
- refund_request    (wants money back)
- cancel_order      (wants to cancel an order)
- place_order       (wants to buy a new product, or order something)
- damaged_item      (received broken or defective product)
- wrong_item        (received wrong product)
- exchange_request  (wants to swap for different size or colour)
- policy_query      (asking about return policy, rules, eligibility)
- general_query     (anything else)

Customer message: "{message}"

Reply with only the intent label, nothing else.
"""
    intent = gemini_reply(prompt).strip().lower()

    # Fallback to keyword classifier if Gemini returns unexpected value
    valid_intents = [
        "order_query", "refund_request", "cancel_order", "place_order",
        "damaged_item", "wrong_item", "exchange_request",
        "policy_query", "general_query"
    ]
    if intent not in valid_intents:
        intent = classify_issue(message)

    print(f"[Node] Intent classified: {intent}")
    state["intent"] = intent
    return state


def extract_order_id(state: dict) -> dict:
    """
    Node 2 — Extract order ID or Product ID from the customer message depending on intent.
    """
    message = state["user_message"]
    intent = state.get("intent", "")

    if intent == "place_order":
        prompt = f"""
Extract the Product ID from this customer message.
Product IDs follow the pattern: P followed by 3 digits (example: P001, P015).

Customer message: "{message}"

If you find a product ID, reply with just the product ID (e.g. P001).
If no product ID is found, reply with: NONE
"""
        product_id = gemini_reply(prompt).strip().upper()
        if product_id == "NONE" or not product_id.startswith("P"):
            product_id = None
            
        print(f"[Node] Product ID extracted: {product_id}")
        state["product_id"] = product_id
        state["order_id"] = None
    else:
        prompt = f"""
Extract the order ID from this customer message.
Order IDs follow the pattern: ORD followed by numbers (example: ORD1001, ORD1007).

Customer message: "{message}"

If you find an order ID, reply with just the order ID (e.g. ORD1001).
If no order ID is found, reply with: NONE
"""
        order_id = gemini_reply(prompt).strip().upper()
        if order_id == "NONE" or not order_id.startswith("ORD"):
            order_id = None

        print(f"[Node] Order ID extracted: {order_id}")
        state["order_id"] = order_id
        state["product_id"] = None
        
    return state


def fetch_order_data(state: dict) -> dict:
    """
    Node 3 — Fetch order details and eligibility from SQLite.
    """
    order_id = state.get("order_id")

    if not order_id:
        state["order_data"]       = None
        state["return_eligibility"] = None
        state["refund_status"]    = None
        return state

    state["order_data"]        = get_order_details(order_id)
    state["return_eligibility"] = check_return_eligibility(order_id)
    state["refund_status"]     = get_refund_status(order_id)

    print(f"[Node] Order data fetched for {order_id}")
    return state


def fetch_policy(state: dict) -> dict:
    """
    Node 4 — Retrieve relevant policy from ChromaDB based on intent.
    """
    intent  = state.get("intent", "")
    message = state.get("user_message", "")

    query_map = {
        "refund_request":   "refund approval and processing",
        "damaged_item":     "damaged defective item return refund",
        "wrong_item":       "wrong item delivered return",
        "cancel_order":     "order cancellation policy",
        "exchange_request": "exchange policy variants",
        "policy_query":     message,
        "order_query":      "order delivery tracking",
        "general_query":    message,
    }

    query = query_map.get(intent, message)
    state["policy_data"] = search_policy(query, n_results=2)

    print(f"[Node] Policy fetched for intent: {intent}")
    return state


def make_decision(state: dict) -> dict:
    """
    Node 5 — Apply business rules and decide what action to take.
    Sets state['action'] to one of:
      approve_refund / reject_refund / cancel_order /
      escalate / provide_info / general_response
    """
    intent            = state.get("intent", "")
    order_data        = state.get("order_data") or {}
    return_eligibility = state.get("return_eligibility") or {}
    attempts          = state.get("attempts", 0)

    amount   = order_data.get("total_inr", 0)
    tier     = order_data.get("membership_tier", "standard")
    state["membership_benefits"] = get_membership_benefits(tier)

    # Check escalation first
    esc = should_escalate(
        amount_inr=amount,
        dissatisfaction_count=state.get("dissatisfaction_count", 0),
        attempts=attempts
    )
    if esc["escalate"]:
        state["action"]           = "escalate"
        state["escalation_reason"] = esc["reason"]
        return state

    # Decide based on intent
    if intent in ("refund_request", "damaged_item", "wrong_item"):
        if not return_eligibility.get("eligible") and intent == "refund_request":
            state["action"] = "reject_refund"
        elif can_auto_approve_refund(amount):
            state["action"] = "approve_refund"
        else:
            state["action"] = "escalate"
            state["escalation_reason"] = f"Refund of Rs. {amount} requires manager approval."

    elif intent == "cancel_order":
        state["action"] = "cancel_order"

    elif intent == "place_order":
        state["action"] = "create_order"

    elif intent in ("policy_query", "exchange_request", "order_query"):
        state["action"] = "provide_info"

    else:
        state["action"] = "general_response"

    print(f"[Node] Decision made: {state['action']}")
    return state


def execute_action(state: dict) -> dict:
    """
    Node 6 — Execute the decided action against the database.
    """
    action   = state.get("action")
    order_id = state.get("order_id")
    intent   = state.get("intent", "")

    if action == "approve_refund" and order_id:
        result = approve_refund(order_id, f"Approved via voice agent: {intent}")
        state["action_result"] = result

    elif action == "reject_refund" and order_id:
        result = reject_refund(order_id, "Outside 7-day return window.")
        state["action_result"] = result

    elif action == "cancel_order" and order_id:
        result = cancel_order(order_id)
        state["action_result"] = result

    elif action == "create_order":
        prod_id = state.get("product_id")
        if prod_id:
            # We assume user C001 (Ravi Kumar) is dynamically logged in to Voice systems for the demo
            result = create_new_order("C001", prod_id)
            state["action_result"] = result
        else:
            state["action_result"] = {"success": False, "message": "Failed to place order. No valid Product ID found."}

    elif action == "escalate" and order_id:
        customer_id = (state.get("order_data") or {}).get("customer_id", "unknown")
        result = log_escalation(
            order_id,
            state.get("escalation_reason", "Escalated by voice agent"),
            customer_id
        )
        state["action_result"] = result

    else:
        state["action_result"] = {"success": True, "message": "Information provided."}

    print(f"[Node] Action executed: {action}")
    return state


def generate_response(state: dict) -> dict:
    """
    Node 7 — Generate a natural, human-like spoken response using Gemini.
    """
    order_data      = state.get("order_data") or {}
    policy_data     = state.get("policy_data") or {}
    action_result   = state.get("action_result") or {}
    intent          = state.get("intent", "")
    action          = state.get("action", "")
    membership      = state.get("membership_benefits") or {}

    policies_text = ""
    if policy_data.get("policies"):
        policies_text = "\n".join(
            f"- {p['topic']}: {p['text']}" for p in policy_data["policies"]
        )

    prompt = f"""
You are a helpful, professional customer support voice agent for ShopVoice, an Indian e-commerce company.
You are speaking directly to a customer on a phone call. Keep your response natural, warm, and concise.
Do not use bullet points or markdown. Speak in plain sentences as you would on a phone call.
Address the customer by name if available.

Customer name: {order_data.get('customer_name', 'the customer')}
Membership tier: {order_data.get('membership_tier', 'standard')}
Membership benefits: {membership.get('description', '')}

Customer intent: {intent}
Action taken: {action}
Action result: {action_result.get('message', '')}

Order details:
- Order ID: {order_data.get('order_id', 'N/A')}
- Status: {order_data.get('status', 'N/A')}
- Total: Rs. {order_data.get('total_inr', 'N/A')}
- Delivered: {order_data.get('delivered_at', 'N/A')}
- Items: {order_data.get('items', [])}

Relevant policies:
{policies_text}

Generate a helpful, spoken response to the customer. Be empathetic and clear.
If a refund was approved, confirm the amount and timeline.
If escalated, reassure them and give a clear timeline.
If rejected, explain why politely and offer alternatives if any.
If a new order was placed successfully, enthusiastically confirm their new order ID and total amount!
Keep the response under 60 words.
"""

    response_text = gemini_reply(prompt)
    state["final_response"] = response_text

    print(f"[Node] Response generated.")
    return state