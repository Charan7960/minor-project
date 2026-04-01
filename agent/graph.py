import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agent.nodes import (
    classify_intent,
    extract_order_id,
    fetch_order_data,
    fetch_policy,
    make_decision,
    execute_action,
    generate_response,
)


# ── State definition ─────────────────────────────────────────────
# This is the single object that flows through every node.
# Each node reads from it and writes back to it.

class AgentState(TypedDict):
    user_message:          str
    intent:                Optional[str]
    order_id:              Optional[str]
    order_data:            Optional[dict]
    return_eligibility:    Optional[dict]
    refund_status:         Optional[dict]
    policy_data:           Optional[dict]
    membership_benefits:   Optional[dict]
    action:                Optional[str]
    action_result:         Optional[dict]
    escalation_reason:     Optional[str]
    final_response:        Optional[str]
    dissatisfaction_count: int
    attempts:              int


def build_graph():
    """Build and compile the LangGraph agent."""

    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("classify_intent",  classify_intent)
    graph.add_node("extract_order_id", extract_order_id)
    graph.add_node("fetch_order_data", fetch_order_data)
    graph.add_node("fetch_policy",     fetch_policy)
    graph.add_node("make_decision",    make_decision)
    graph.add_node("execute_action",   execute_action)
    graph.add_node("generate_response",generate_response)

    # Define the flow
    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent",  "extract_order_id")
    graph.add_edge("extract_order_id", "fetch_order_data")
    graph.add_edge("fetch_order_data", "fetch_policy")
    graph.add_edge("fetch_policy",     "make_decision")
    graph.add_edge("make_decision",    "execute_action")
    graph.add_edge("execute_action",   "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


def run_agent(user_message: str,
              dissatisfaction_count: int = 0,
              attempts: int = 0) -> str:
    """
    Run the full agent pipeline for a single customer message.
    Returns the spoken response string.
    """
    agent = build_graph()

    initial_state: AgentState = {
        "user_message":          user_message,
        "intent":                None,
        "order_id":              None,
        "order_data":            None,
        "return_eligibility":    None,
        "refund_status":         None,
        "policy_data":           None,
        "membership_benefits":   None,
        "action":                None,
        "action_result":         None,
        "escalation_reason":     None,
        "final_response":        None,
        "dissatisfaction_count": dissatisfaction_count,
        "attempts":              attempts,
    }

    result = agent.invoke(initial_state)
    return result["final_response"]


if __name__ == "__main__":
    import time

    print("=== Testing graph.py — Full Agent Pipeline ===\n")

    test_cases = [
        "I want to cancel my order ORD1008.",
        "I need a refund for ORD1010.",
    ]

    for msg in test_cases:
        print(f"\nCustomer: {msg}")
        print("-" * 50)
        response = run_agent(msg)
        print(f"Agent: {response}")
        print("=" * 50)
        time.sleep(30)
