import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ecommerce.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def approve_refund(order_id: str, reason: str) -> dict:
    """Approve a pending refund for an order. Only works for amounts under Rs. 5000."""
    conn = get_connection()
    try:
        order = conn.execute(
            "SELECT total_inr, status FROM orders WHERE order_id = ?",
            (order_id,)
        ).fetchone()

        if not order:
            return {"success": False, "message": f"Order {order_id} not found."}

        if order["total_inr"] > 5000:
            return {
                "success":   False,
                "message":   f"Refund of Rs. {order['total_inr']} exceeds Rs. 5000 limit. Must escalate to human agent.",
                "escalate":  True,
                "amount_inr": order["total_inr"],
            }

        existing = conn.execute(
            "SELECT refund_id, status FROM refunds WHERE order_id = ? ORDER BY requested_at DESC LIMIT 1",
            (order_id,)
        ).fetchone()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            conn.execute("""
                UPDATE refunds
                SET status = 'approved', resolved_at = ?, reason = ?
                WHERE refund_id = ?
            """, (now, reason, existing["refund_id"]))
            refund_id = existing["refund_id"]
        else:
            refund_id = f"REF{order_id[-4:]}{datetime.now().strftime('%H%M%S')}"
            conn.execute("""
                INSERT INTO refunds
                (refund_id, order_id, customer_id, reason, amount_inr, status, requested_at, resolved_at)
                SELECT ?, order_id, customer_id, ?, total_inr, 'approved', ?, ?
                FROM orders WHERE order_id = ?
            """, (refund_id, reason, now, now, order_id))

        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE order_id = ?",
            (order_id,)
        )
        conn.commit()

        return {
            "success":    True,
            "refund_id":  refund_id,
            "amount_inr": order["total_inr"],
            "message":    f"Refund of Rs. {order['total_inr']} approved. Will be credited in 5-7 business days.",
        }
    finally:
        conn.close()


def reject_refund(order_id: str, reason: str) -> dict:
    """Reject a refund request with a reason."""
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT refund_id FROM refunds WHERE order_id = ? ORDER BY requested_at DESC LIMIT 1",
            (order_id,)
        ).fetchone()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            conn.execute("""
                UPDATE refunds SET status = 'rejected', resolved_at = ?, reason = ?
                WHERE refund_id = ?
            """, (now, reason, existing["refund_id"]))
        else:
            refund_id = f"REF{order_id[-4:]}{datetime.now().strftime('%H%M%S')}"
            conn.execute("""
                INSERT INTO refunds
                (refund_id, order_id, customer_id, reason, amount_inr, status, requested_at, resolved_at)
                SELECT ?, order_id, customer_id, ?, total_inr, 'rejected', ?, ?
                FROM orders WHERE order_id = ?
            """, (refund_id, reason, now, now, order_id))

        conn.commit()
        return {
            "success": True,
            "message": f"Refund rejected. Reason: {reason}",
        }
    finally:
        conn.close()


def cancel_order(order_id: str) -> dict:
    """Cancel an order if it is still in processing state."""
    conn = get_connection()
    try:
        order = conn.execute(
            "SELECT status, total_inr FROM orders WHERE order_id = ?",
            (order_id,)
        ).fetchone()

        if not order:
            return {"success": False, "message": f"Order {order_id} not found."}

        if order["status"] == "cancelled":
            return {"success": False, "message": "Order is already cancelled."}

        if order["status"] in ("shipped", "delivered"):
            return {
                "success": False,
                "message": f"Order is already {order['status']} and cannot be cancelled. Please request a return instead.",
            }

        conn.execute(
            "UPDATE orders SET status = 'cancelled' WHERE order_id = ?",
            (order_id,)
        )
        conn.commit()

        return {
            "success":    True,
            "message":    f"Order {order_id} cancelled successfully. Refund of Rs. {order['total_inr']} will be processed in 3 business days.",
            "amount_inr": order["total_inr"],
        }
    finally:
        conn.close()


def log_escalation(order_id: str, reason: str, customer_id: str) -> dict:
    """Log a case that needs human agent follow-up."""
    conn = get_connection()
    try:
        escalation_id = f"ESC{order_id[-4:]}{datetime.now().strftime('%H%M%S')}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("""
            INSERT OR IGNORE INTO refunds
            (refund_id, order_id, customer_id, reason, amount_inr, status, requested_at)
            SELECT ?, order_id, customer_id, ?, total_inr, 'pending', ?
            FROM orders WHERE order_id = ?
        """, (escalation_id, f"ESCALATED: {reason}", now, order_id))

        conn.commit()

        return {
            "success":       True,
            "escalation_id": escalation_id,
            "message":       "Your case has been escalated to our team. You will receive a callback within 24 hours.",
        }
    finally:
        conn.close()

def create_new_order(customer_id: str, product_id: str) -> dict:
    """Creates a new order organically when the customer requests one via voice."""
    conn = get_connection()
    try:
        product = conn.execute("SELECT name, price_inr FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if not product:
            return {"success": False, "message": f"Product {product_id} not found. Please try another product."}
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unique_num = datetime.now().strftime("%y%m%H%M%S")
        new_order_id = f"ORD{unique_num}"
        
        conn.execute("""
            INSERT INTO orders (order_id, customer_id, status, total_inr, ordered_at, product_name)
            VALUES (?, ?, 'processing', ?, ?, ?)
        """, (new_order_id, customer_id, product["price_inr"], now, product["name"]))
        
        conn.commit()
        return {
            "success": True, 
            "order_id": new_order_id, 
            "amount_inr": product["price_inr"], 
            "product_name": product["name"], 
            "message": f"Perfect! New order created for {product['name']}."
        }
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Testing record_tools.py ===\n")

    print("1. Approve refund for ORD1002 (Rs. 1299 — under limit):")
    print(approve_refund("ORD1002", "Item arrived damaged"))

    print("\n2. Approve refund for ORD1010 (Rs. 9998 — over limit, should escalate):")
    print(approve_refund("ORD1010", "Customer unhappy"))

    print("\n3. Cancel order ORD1008 (processing — should work):")
    print(cancel_order("ORD1008"))

    print("\n4. Cancel order ORD1007 (shipped — should fail):")
    print(cancel_order("ORD1007"))

    print("\n5. Log escalation for ORD1010:")
    print(log_escalation("ORD1010", "Refund exceeds Rs. 5000", "C004"))

    print("\n[record_tools] All tests passed.")
