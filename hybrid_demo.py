import sys
import os
import os
import time
import sqlite3
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import Response, HTMLResponse
import uvicorn

sys.path.append(os.path.dirname(__file__))

from voice.stt import listen
from agent.graph import run_agent
from voice.tts import speak

app = FastAPI(title="ShopVoice Hybrid Demo")

def execute_demo():
    print("\n[=========================================]")
    print("[HYBRID TRIGGER] Call received from Exotel! ")
    print("[=========================================]")
    
    # Wait for the phone greeting to play before turning on laptop mic
    print("\n[HYBRID] Phone is ringing/speaking... waiting 3.5 seconds...")
    time.sleep(3.5)
    
    # Start the standard demo loop locally
    print("\n[HYBRID] 🎙️ Laptop microphone is now LISTENING for 10 seconds...")
    print("[HYBRID] Speak up loud and clear into the room!")
    
    try:
        user_speech = listen(duration=10)
        print(f"\n[HYBRID] Heard: {user_speech}")
        
        if not user_speech or len(user_speech.strip()) < 3:
            print("[HYBRID] Didn't catch that. Please try calling again.")
            return
            
        print("\n[HYBRID] 🧠 Agent is thinking...")
        agent_response = run_agent(user_speech)
        print(f"\n[HYBRID] Agent says: {agent_response}")
        
        print("\n[HYBRID] 🔊 Speaking response loud from laptop speakers...")
        speak(agent_response)
        
        print("\n[HYBRID] ✅ Demo turn complete. You can hang up the phone.")
        
    except Exception as e:
        print(f"\n[HYBRID] Error during demo execution: {e}")

@app.post("/trigger")
@app.get("/trigger")
async def trigger_demo(request: Request, background_tasks: BackgroundTasks):
    """
    Exotel hits this URL via Passthru applet the moment the call starts.
    We return 200 OK immediately so Exotel moves to the Greeting applet.
    Meanwhile, we start the demo in the background!
    """
    background_tasks.add_task(execute_demo)
    return Response(content="OK", status_code=200, media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the beautiful frontend dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error</h1><p>frontend/index.html not found. Please create it.</p>"


@app.get("/store", response_class=HTMLResponse)
async def serve_store():
    """Serves the customer storefront."""
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "store.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error</h1><p>frontend/store.html not found.</p>"

@app.get("/api/products")
async def api_get_products():
    """Provides product data and Exotel number for the mock storefront."""
    db_path = os.path.join(os.path.dirname(__file__), "data", "ecommerce.db")
    try:
        phone = os.getenv("EXOTEL_PHONE_NUMBER", "Call Support")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM products").fetchall()
        products = [dict(row) for row in rows]
        conn.close()
        return {"phone": phone, "products": products}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/orders")
async def api_get_orders():
    """Provides real-time database orders for the frontend."""
    db_path = os.path.join(os.path.dirname(__file__), "data", "ecommerce.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT o.order_id, c.name as customer_name, o.product_name, o.status, 
                   o.total_inr, o.ordered_at, o.delivered_at, o.delivery_addr
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            ORDER BY o.ordered_at DESC
        """
        rows = conn.execute(query).fetchall()
        orders = [dict(row) for row in rows]
        
        # Merge refund statuses inside
        refund_query = "SELECT order_id, status as refund_status, reason FROM refunds"
        refund_rows = conn.execute(refund_query).fetchall()
        refund_dict = {row["order_id"]: {"status": row["refund_status"], "reason": row["reason"]} for row in refund_rows}
        
        for order in orders:
            if order["order_id"] in refund_dict:
                order["refund_info"] = refund_dict[order["order_id"]]
            else:
                order["refund_info"] = None
                
        conn.close()
        return {"orders": orders}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ShopVoice AI Agent — Hybrid Voice Demo Server")
    print("="*70)
    print("\n[HYBRID] Ensure ngrok is running on port 8000:  ngrok http 8000")
    print("[HYBRID] Press Ctrl+C to stop the server\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
