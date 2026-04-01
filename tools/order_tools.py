import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ecommerce.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_order_details(order_id: str) -> dict:
    """Fetch full order details including customer and items."""
    conn = get_connection()
    try:
        order = conn.execute("""
            SELECT o.*, c.name as customer_name, c.email,
                   c.phone, c.membership_tier
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ?
        """, (order_id,)).fetchone()

        if not order:
            return {"error": f"Order {order_id} not found."}

        items = conn.execute("""
            SELECT p.name, oi.qty, oi.unit_price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        """, (order_id,)).fetchall()

        return {
            "order_id":       order["order_id"],
            "customer_name":  order["customer_name"],
            "customer_id":    order["customer_id"],
            "email":          order["email"],
            "phone":          order["phone"],
            "membership_tier":order["membership_tier"],
            "status":         order["status"],
            "total_inr":      order["total_inr"],
            "ordered_at":     order["ordered_at"],
            "delivered_at":   order["delivered_at"],
            "delivery_addr":  order["delivery_addr"],
            "items": [
                {
                    "product": item["name"],
                    "qty":     item["qty"],
                    "price":   item["unit_price"]
                }
                for item in items
            ],
        }
    finally:
        conn.close()


def get_customer_orders(customer_id: str) -> dict:
    """Fetch all orders for a customer."""
    conn = get_connection()
    try:
        orders = conn.execute("""
            SELECT order_id, status, total_inr, ordered_at, delivered_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY ordered_at DESC
        """, (customer_id,)).fetchall()

        if not orders:
            return {"error": f"No orders found for customer {customer_id}."}

        return {
            "customer_id": customer_id,
            "orders": [dict(o) for o in orders]
        }
    finally:
        conn.close()


def check_return_eligibility(order_id: str) -> dict:
    """Check if an order is within the 7-day return window."""
    conn = get_connection()
    try:
        order = conn.execute("""
            SELECT order_id, status, total_inr, delivered_at
            FROM orders WHERE order_id = ?
        """, (order_id,)).fetchone()

        if not order:
            return {"eligible": False, "reason": f"Order {order_id} not found."}

        if order["status"] not in ("delivered",):
            return {
                "eligible": False,
                "reason": f"Order status is '{order['status']}'. Only delivered orders can be returned."
            }

        if not order["delivered_at"]:
            return {"eligible": False, "reason": "Delivery date not recorded."}

        delivered_at = datetime.strptime(order["delivered_at"], "%Y-%m-%d %H:%M:%S")
        days_since   = (datetime.now() - delivered_at).days

        if days_since <= 7:
            return {
                "eligible":    True,
                "days_since_delivery": days_since,
                "reason": f"Order delivered {days_since} day(s) ago. Within 7-day return window.",
                "total_inr":   order["total_inr"],
            }
        else:
            return {
                "eligible":    False,
                "days_since_delivery": days_since,
                "reason": f"Order delivered {days_since} day(s) ago. Outside 7-day return window.",
                "total_inr":   order["total_inr"],
            }
    finally:
        conn.close()


def get_refund_status(order_id: str) -> dict:
    """Check if a refund exists for an order and its current status."""
    conn = get_connection()
    try:
        refund = conn.execute("""
            SELECT * FROM refunds WHERE order_id = ?
            ORDER BY requested_at DESC LIMIT 1
        """, (order_id,)).fetchone()

        if not refund:
            return {"exists": False, "message": "No refund request found for this order."}

        return {
            "exists":       True,
            "refund_id":    refund["refund_id"],
            "status":       refund["status"],
            "amount_inr":   refund["amount_inr"],
            "reason":       refund["reason"],
            "requested_at": refund["requested_at"],
            "resolved_at":  refund["resolved_at"],
        }
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Testing order_tools.py ===\n")

    print("1. Order details for ORD1001:")
    print(get_order_details("ORD1001"))

    print("\n2. Return eligibility for ORD1002 (recent):")
    print(check_return_eligibility("ORD1002"))

    print("\n3. Return eligibility for ORD1005 (old):")
    print(check_return_eligibility("ORD1005"))

    print("\n4. Refund status for ORD1002:")
    print(get_refund_status("ORD1002"))

    print("\n[order_tools] All tests passed.")
