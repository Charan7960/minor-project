import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "ecommerce.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id     TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            phone           TEXT,
            membership_tier TEXT DEFAULT 'standard',
            created_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS products (
            product_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            category     TEXT,
            price_inr    REAL NOT NULL,
            stock_qty    INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id      TEXT PRIMARY KEY,
            customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
            status        TEXT DEFAULT 'delivered',
            total_inr     REAL NOT NULL,
            ordered_at    TEXT NOT NULL,
            delivered_at  TEXT,
            delivery_addr TEXT
        );
        CREATE TABLE IF NOT EXISTS order_items (
            item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   TEXT NOT NULL REFERENCES orders(order_id),
            product_id TEXT NOT NULL REFERENCES products(product_id),
            qty        INTEGER NOT NULL,
            unit_price REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id    TEXT PRIMARY KEY,
            order_id     TEXT NOT NULL REFERENCES orders(order_id),
            customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
            reason       TEXT,
            amount_inr   REAL,
            status       TEXT DEFAULT 'pending',
            requested_at TEXT DEFAULT (datetime('now')),
            resolved_at  TEXT
        );
    """)
    conn.commit()
    print("[DB] Tables created.")

def seed_customers(conn):
    customers = [
        ("C001", "Ravi Kumar",    "ravi.kumar@email.com",    "9876543210", "gold"),
        ("C002", "Sneha Reddy",   "sneha.reddy@email.com",   "9123456780", "silver"),
        ("C003", "Arjun Nair",    "arjun.nair@email.com",    "9988776655", "standard"),
        ("C004", "Divya Sharma",  "divya.sharma@email.com",  "9871234560", "gold"),
        ("C005", "Kiran Patel",   "kiran.patel@email.com",   "9765432100", "standard"),
        ("C006", "Meera Iyer",    "meera.iyer@email.com",    "9654321098", "silver"),
        ("C007", "Suresh Babu",   "suresh.babu@email.com",   "9543210987", "standard"),
        ("C008", "Ananya Pillai", "ananya.pillai@email.com", "9432109876", "gold"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?,datetime('now'))",
        customers
    )
    conn.commit()
    print(f"[DB] Seeded {len(customers)} customers.")

def seed_products(conn):
    products = [
        ("P001", "Noise Cancelling Headphones", "Electronics", 4999.0,  50),
        ("P002", "Wireless Mouse",              "Electronics", 1299.0, 120),
        ("P003", "Mechanical Keyboard",         "Electronics", 3499.0,  75),
        ("P004", "USB-C Hub 7-in-1",            "Electronics", 2199.0,  90),
        ("P005", "Cotton Formal Shirt",         "Clothing",     899.0, 200),
        ("P006", "Running Shoes",               "Footwear",    2999.0,  60),
        ("P007", "Stainless Steel Water Bottle","Lifestyle",    599.0, 150),
        ("P008", "Yoga Mat",                    "Fitness",     1499.0,  80),
        ("P009", "Face Moisturiser SPF 50",     "Beauty",       749.0, 100),
        ("P010", "Laptop Stand Adjustable",     "Electronics", 1899.0,  65),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)",
        products
    )
    conn.commit()
    print(f"[DB] Seeded {len(products)} products.")

def seed_orders(conn):
    now = datetime.now()
    orders_raw = [
        ("ORD1001", "C001", "delivered", 6298.0,  3,  1, "14 MG Road, Bengaluru 560001"),
        ("ORD1002", "C002", "delivered", 1299.0,  5,  3, "22 Anna Salai, Chennai 600002"),
        ("ORD1003", "C003", "delivered", 5598.0,  2,  1, "8 Banjara Hills, Hyderabad 500034"),
        ("ORD1004", "C004", "delivered", 4999.0,  6,  4, "3 Marine Drive, Mumbai 400001"),
        ("ORD1005", "C005", "delivered", 3499.0, 15, 12, "9 Connaught Place, Delhi 110001"),
        ("ORD1006", "C006", "delivered",  899.0, 20, 17, "55 Park Street, Kolkata 700016"),
        ("ORD1007", "C007", "shipped",   2798.0,  2, None, "77 FC Road, Pune 411004"),
        ("ORD1008", "C008", "processing", 599.0,  1, None, "12 Jubilee Hills, Hyderabad 500033"),
        ("ORD1009", "C001", "cancelled", 1899.0,  8, None, "14 MG Road, Bengaluru 560001"),
        ("ORD1010", "C004", "delivered", 9998.0,  4,  2, "3 Marine Drive, Mumbai 400001"),
    ]
    for (oid, cid, status, total, days_ago, del_days_ago, addr) in orders_raw:
        ordered_at   = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        delivered_at = (now - timedelta(days=del_days_ago)).strftime("%Y-%m-%d %H:%M:%S") if del_days_ago else None
        conn.execute(
            "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?,?)",
            (oid, cid, status, total, ordered_at, delivered_at, addr)
        )
    conn.commit()
    print(f"[DB] Seeded {len(orders_raw)} orders.")

def seed_order_items(conn):
    items = [
        ("ORD1001", "P001", 1, 4999.0),
        ("ORD1001", "P002", 1, 1299.0),
        ("ORD1002", "P002", 1, 1299.0),
        ("ORD1003", "P001", 1, 4999.0),
        ("ORD1003", "P007", 1,  599.0),
        ("ORD1004", "P001", 1, 4999.0),
        ("ORD1005", "P003", 1, 3499.0),
        ("ORD1006", "P005", 1,  899.0),
        ("ORD1007", "P002", 1, 1299.0),
        ("ORD1007", "P007", 1,  599.0),
        ("ORD1007", "P008", 1,  900.0),
        ("ORD1008", "P007", 1,  599.0),
        ("ORD1009", "P010", 1, 1899.0),
        ("ORD1010", "P001", 2, 4999.0),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO order_items (order_id, product_id, qty, unit_price) VALUES (?,?,?,?)",
        items
    )
    conn.commit()
    print(f"[DB] Seeded {len(items)} order items.")

def seed_refunds(conn):
    now = datetime.now()
    refunds = [
        ("REF001", "ORD1002", "C002", "Item arrived damaged", 1299.0, "pending",
         (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), None),
        ("REF002", "ORD1003", "C003", "Wrong item delivered", 599.0, "approved",
         (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
         (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")),
        ("REF003", "ORD1005", "C005", "Changed mind", 3499.0, "rejected",
         (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
         (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO refunds VALUES (?,?,?,?,?,?,?,?)",
        refunds
    )
    conn.commit()
    print(f"[DB] Seeded {len(refunds)} refunds.")

def verify(conn):
    print("\n[DB] Verification:")
    for table in ["customers", "products", "orders", "order_items", "refunds"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15}: {count} rows")

if __name__ == "__main__":
    print(f"[DB] Creating database at: {DB_PATH}\n")
    conn = get_connection()
    create_tables(conn)
    seed_customers(conn)
    seed_products(conn)
    seed_orders(conn)
    seed_order_items(conn)
    seed_refunds(conn)
    verify(conn)
    conn.close()
    print("\n[DB] Phase 1a complete.")

