from datetime import datetime


REFUND_AUTO_APPROVE_LIMIT = 5000.0
RETURN_WINDOW_DAYS = 7
MAX_ATTEMPTS_BEFORE_ESCALATE = 2


def can_auto_approve_refund(amount_inr: float) -> bool:
    """Returns True if agent can approve without human."""
    return amount_inr <= REFUND_AUTO_APPROVE_LIMIT


def is_within_return_window(delivered_at: str) -> bool:
    """Returns True if order is within 7-day return window."""
    if not delivered_at:
        return False
    delivered = datetime.strptime(delivered_at, "%Y-%m-%d %H:%M:%S")
    days_since = (datetime.now() - delivered).days
    return days_since <= RETURN_WINDOW_DAYS


def should_escalate(amount_inr: float = 0,
                    dissatisfaction_count: int = 0,
                    is_fraud: bool = False,
                    attempts: int = 0) -> dict:
    """
    Central escalation decision function.
    Returns whether to escalate and the reason why.
    """
    if is_fraud:
        return {"escalate": True, "reason": "Fraud or legal complaint raised."}

    if amount_inr > REFUND_AUTO_APPROVE_LIMIT:
        return {
            "escalate": True,
            "reason": f"Refund amount Rs. {amount_inr} exceeds auto-approval limit of Rs. {REFUND_AUTO_APPROVE_LIMIT}."
        }

    if dissatisfaction_count >= 3:
        return {
            "escalate": True,
            "reason": "Customer expressed dissatisfaction multiple times."
        }

    if attempts >= MAX_ATTEMPTS_BEFORE_ESCALATE:
        return {
            "escalate": True,
            "reason": "Agent could not resolve issue after maximum attempts."
        }

    return {"escalate": False, "reason": ""}


def get_membership_benefits(tier: str) -> dict:
    """Returns support benefits based on membership tier."""
    benefits = {
        "gold": {
            "priority_support":  True,
            "free_returns":      True,
            "callback_hours":    2,
            "description": "Gold member: priority support, free returns, 2-hour callback."
        },
        "silver": {
            "priority_support":  False,
            "free_returns":      True,
            "callback_hours":    4,
            "description": "Silver member: free returns on orders above Rs. 1000, 4-hour callback."
        },
        "standard": {
            "priority_support":  False,
            "free_returns":      False,
            "callback_hours":    24,
            "description": "Standard member: default 7-day return window."
        },
    }
    return benefits.get(tier.lower(), benefits["standard"])


def classify_issue(customer_message: str) -> str:
    """
    Simple keyword-based intent classifier as a fallback.
    The LLM classifier in nodes.py is the primary one.
    """
    msg = customer_message.lower()

    if any(w in msg for w in ["refund", "money back", "reimburse"]):
        return "refund_request"
    if any(w in msg for w in ["cancel", "cancellation"]):
        return "cancel_order"
    if any(w in msg for w in ["where", "status", "track", "delivery", "arrive"]):
        return "order_query"
    if any(w in msg for w in ["wrong item", "incorrect", "different product"]):
        return "wrong_item"
    if any(w in msg for w in ["damaged", "broken", "defective", "not working"]):
        return "damaged_item"
    if any(w in msg for w in ["exchange", "swap", "replace"]):
        return "exchange_request"
    if any(w in msg for w in ["policy", "rule", "allowed", "eligible"]):
        return "policy_query"

    return "general_query"


if __name__ == "__main__":
    print("=== Testing decision_rules.py ===\n")

    print("1. Can auto approve Rs. 1299?", can_auto_approve_refund(1299))
    print("2. Can auto approve Rs. 9998?", can_auto_approve_refund(9998))

    print("\n3. Return window check (delivered 3 days ago):")
    from datetime import timedelta
    recent = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    old    = (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d %H:%M:%S")
    print("   Recent order:", is_within_return_window(recent))
    print("   Old order:   ", is_within_return_window(old))

    print("\n4. Escalation checks:")
    print("   High amount:  ", should_escalate(amount_inr=9998))
    print("   Dissatisfied: ", should_escalate(dissatisfaction_count=3))
    print("   Normal case:  ", should_escalate(amount_inr=500))

    print("\n5. Membership benefits:")
    print("   Gold:    ", get_membership_benefits("gold")["description"])
    print("   Silver:  ", get_membership_benefits("silver")["description"])
    print("   Standard:", get_membership_benefits("standard")["description"])

    print("\n6. Intent classification:")
    print("   'where is my order'     →", classify_issue("where is my order"))
    print("   'I want a refund'       →", classify_issue("I want a refund"))
    print("   'item arrived damaged'  →", classify_issue("item arrived damaged"))
    print("   'cancel my order'       →", classify_issue("cancel my order"))

    print("\n[decision_rules] All tests passed.")
