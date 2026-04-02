import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "ecommerce.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS refunds;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        
        CREATE TABLE customers (
            customer_id     TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            phone           TEXT,
            membership_tier TEXT DEFAULT 'standard',
            created_at      TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE products (
            product_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            category     TEXT,
            price_inr    REAL NOT NULL,
            stock_qty    INTEGER DEFAULT 0
        );
        CREATE TABLE orders (
            order_id      TEXT PRIMARY KEY,
            customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
            status        TEXT DEFAULT 'delivered',
            total_inr     REAL NOT NULL,
            ordered_at    TEXT NOT NULL,
            delivered_at  TEXT,
            delivery_addr TEXT,
            product_name  TEXT DEFAULT 'Various Items'
        );
        CREATE TABLE order_items (
            item_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   TEXT NOT NULL REFERENCES orders(order_id),
            product_id TEXT NOT NULL REFERENCES products(product_id),
            qty        INTEGER NOT NULL,
            unit_price REAL NOT NULL
        );
        CREATE TABLE refunds (
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
    print("[DB] Tables dropped and recreated.")

# Original 10 strictly preserved for the demo
def seed_products(conn):
    base_products = [
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
    extended_products = [
        ("Smart Watch Series 5", "Electronics", 3999.0, 40),
        ("4K Web Camera", "Electronics", 2499.0, 30),
        ("Wireless Earbuds", "Electronics", 1599.0, 200),
        ("Ergonomic Office Chair", "Furniture", 8500.0, 15),
        ("Premium Leather Wallet", "Accessories", 499.0, 300),
        ("Aviator Sunglasses", "Accessories", 1200.0, 80),
        ("Whey Protein (1kg)", "Fitness", 2200.0, 50),
        ("Hex Dumbbell Set (10kg)", "Fitness", 1800.0, 30),
        ("Scented Candles Set", "Lifestyle", 399.0, 100),
        ("Ceramic Coffee Mug", "Lifestyle", 299.0, 150),
        ("Classic Denim Jacket", "Clothing", 1499.0, 60),
        ("Graphic Pattern T-Shirt", "Clothing", 499.0, 250),
        ("Vitamin C Face Serum", "Beauty", 699.0, 120),
        ("Long-last Matte Lipstick", "Beauty", 350.0, 200),
        ("Gaming Monitor 144Hz", "Electronics", 14500.0, 10),
        ("Portable Bluetooth Speaker", "Electronics", 1899.0, 75),
        ("Durable Travel Backpack", "Accessories", 1199.0, 90),
        ("Athletic Running Shorts", "Clothing", 450.0, 120),
        ("Seamless Yoga Pants", "Fitness", 799.0, 85),
        ("Smart Water Purifier", "Lifestyle", 899.0, 45)
    ]
    products = list(base_products)
    for i, (name, cat, price, stock) in enumerate(extended_products):
        products.append((f"P{str(11+i).zfill(3)}", name, cat, price, stock))
        
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)
    conn.commit()
    print(f"[DB] Seeded {len(products)} products.")

def seed_data_procedurally(conn):
    now = datetime.now()
    
    # Original 8 customers to preserve existing demo script
    base_customers = [
        ("C001", "Ravi Kumar",    "gold"),
        ("C002", "Sneha Reddy",   "silver"),
        ("C003", "Arjun Nair",    "standard"),
        ("C004", "Divya Sharma",  "gold"),
        ("C005", "Kiran Patel",   "standard"),
        ("C006", "Meera Iyer",    "silver"),
        ("C007", "Suresh Babu",   "standard"),
        ("C008", "Ananya Pillai", "gold"),
    ]
    
    # 42 extra procedural names
    first_names = ["Amit", "Neha", "Rahul", "Priya", "Vikram", "Pooja", "Raj", "Kavita", "Sandeep", "Aarti", "Manish", "Sunita", "Deepak", "Ritu", "Vivek", "Jyoti", "Ashok", "Kiran", "Vijay", "Anil", "Geeta"]
    last_names = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Reddy", "Iyer", "Nair", "Das", "Joshi", "Bansal", "Chopra", "Chauhan", "Mehta", "Bhat"]
    tiers = ["standard", "standard", "standard", "silver", "silver", "gold"]
    statuses = ["delivered", "delivered", "delivered", "shipped", "processing", "cancelled"]
    addrs = ["MG Road, Bengaluru", "Anna Salai, Chennai", "Banjara Hills, Hyderabad", "Marine Drive, Mumbai", "Connaught Place, Delhi", "Park Street, Kolkata", "FC Road, Pune", "Jubilee Hills, Hyderabad"]
    
    customers = []
    # Add base 8
    for i, (cid, name, tier) in enumerate(base_customers):
        customers.append((cid, name, f"{name.split(' ')[0].lower()}@email.com", f"9876543{str(i).zfill(3)}", tier))
    
    # Generate 992 more to hit 1000 customers
    random.seed(42) # Deterministic
    for i in range(9, 1001):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.replace(' ', '.').lower()}{i}@email.com"
        customers.append((f"C{str(i).zfill(3)}", name, email, f"91{random.randint(10000000, 99999999)}", random.choice(tiers)))
        
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,datetime('now'))", customers)
    
    product_names = [
        "Noise Cancelling Headphones", "Wireless Mouse", "Mechanical Keyboard",
        "Cotton Formal Shirt", "Running Shoes", "Yoga Mat", "Gaming Monitor 144Hz",
        "Portable Bluetooth Speaker", "Vitamin C Face Serum", "Ergonomic Office Chair"
    ]

    # Base 10 orders (PRESERVED for demo accuracy)
    orders = [
        ("ORD1001", "C001", "delivered", 6298.0, 3, 1, "14 MG Road, Bengaluru 560001", "Noise Cancelling Headphones"),
        ("ORD1002", "C002", "delivered", 1299.0, 5, 3, "22 Anna Salai, Chennai 600002", "Wireless Mouse"),
        ("ORD1003", "C003", "delivered", 5598.0, 2, 1, "8 Banjara Hills, Hyderabad 500034", "Mechanical Keyboard"),
        ("ORD1004", "C004", "delivered", 4999.0, 6, 4, "3 Marine Drive, Mumbai 400001", "Noise Cancelling Headphones"),
        ("ORD1005", "C005", "delivered", 3499.0, 15, 12, "9 Connaught Place, Delhi 110001", "Mechanical Keyboard"),
        ("ORD1006", "C006", "delivered",  899.0, 20, 17, "55 Park Street, Kolkata 700016", "Cotton Formal Shirt"),
        ("ORD1007", "C007", "shipped",   2798.0, 2, None, "77 FC Road, Pune 411004", "Running Shoes"),
        ("ORD1008", "C008", "processing", 599.0, 1, None, "12 Jubilee Hills, Hyderabad 500033", "Stainless Steel Water Bottle"),
        ("ORD1009", "C001", "cancelled", 1899.0, 8, None, "14 MG Road, Bengaluru 560001", "Laptop Stand Adjustable"),
        ("ORD1010", "C004", "delivered", 9998.0, 4, 2, "3 Marine Drive, Mumbai 400001", "Ergonomic Office Chair"),
    ]
    
    # Generate 990 more orders for the new customers
    for i in range(11, 1001):
        cid = f"C{str(i).zfill(3)}"
        status = random.choice(statuses)
        days_ago = random.randint(1, 30)
        del_days_ago = days_ago - random.randint(1, 4) if status == "delivered" else None
        addr = f"{random.randint(10, 99)} {random.choice(addrs)}"
        # Mock total, normally derived from items
        total = float(random.choice([899.0, 1299.0, 2199.0, 2999.0, 3499.0, 4999.0, 19998.0]))
        pname = random.choice(product_names)
        orders.append((f"ORD{1000+i}", cid, status, total, days_ago, del_days_ago, addr, pname))

    for (oid, cid, status, total, days_ago, del_days_ago, addr, pname) in orders:
        ordered_at = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        delivered_at = (now - timedelta(days=del_days_ago)).strftime("%Y-%m-%d %H:%M:%S") if del_days_ago else None
        conn.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", (oid, cid, status, total, ordered_at, delivered_at, addr, pname))
        
    conn.commit()
    print(f"[DB] Seeded 1000 customers and 1000 orders.")

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
    conn.executemany("INSERT INTO refunds VALUES (?,?,?,?,?,?,?,?)", refunds)
    conn.commit()

def verify(conn):
    print("\n[DB] Verification:")
    for table in ["customers", "products", "orders", "refunds"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15}: {count} rows")

if __name__ == "__main__":
    print(f"[DB] Resetting database at: {DB_PATH}\n")
    conn = get_connection()
    create_tables(conn)
    seed_products(conn)
    seed_data_procedurally(conn)
    seed_refunds(conn)
    verify(conn)
    conn.close()
    print("\n[DB] Phase 1a complete. Dashboard dataset expanded to 1000.")
