"""
ShopVoice AI Agent — Live Demo Script

Run this in front of the review panel to showcase the system.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agent.graph import run_agent
from voice.stt import listen
from voice.tts import speak
import time


def demo():
    print("\n" + "="*70)
    print("  ShopVoice AI Agent — Live Demo")
    print("="*70)
    print("\nThis AI voice agent can:")
    print("  ✓ Listen to customer calls (Whisper STT)")
    print("  ✓ Understand intent and fetch order data from SQLite")
    print("  ✓ Search policies from ChromaDB vector store")
    print("  ✓ Apply business rules (5000 Rs limit, 7-day returns, escalation)")
    print("  ✓ Think using Gemini API with LangGraph")
    print("  ✓ Speak natural responses (gTTS TTS)")
    print("\n" + "="*70)
    
    test_scenarios = [
        {
            "name": "Scenario 1: Order Status Query",
            "prompt": "Say: 'I want to check my order ORD1001'",
            "expected": "Agent will fetch order details, say status and delivery address"
        },
        {
            "name": "Scenario 2: Damaged Item Refund (Auto-Approved)",
            "prompt": "Say: 'I received a damaged item in order ORD1002, I want a refund'",
            "expected": "Agent will check 7-day window, approve Rs. 1299 refund automatically"
        },
        {
            "name": "Scenario 3: High-Value Refund (Escalation)",
            "prompt": "Say: 'I need a refund for order ORD1010'",
            "expected": "Agent will see Rs. 9998 exceeds limit, escalate to human agent"
        },
        {
            "name": "Scenario 4: Policy Query",
            "prompt": "Say: 'Can I return an item after 10 days?'",
            "expected": "Agent will search policy, explain 7-day return window"
        },
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{scenario['name']}")
        print("-" * 70)
        print(f"Panel Instruction: {scenario['prompt']}")
        print(f"Expected Behavior: {scenario['expected']}")
        print("\nListening for 5 seconds... Speak now!")
        print("-" * 70)
        
        # Listen
        user_message = listen(duration=5)
        print(f"\n[Heard] {user_message}")
        
        # Think
        print("\n[Thinking...]")
        response = run_agent(user_message)
        
        # Display
        print(f"\n[Agent Response]")
        print(f"{response}\n")
        
        # Speak
        print("[Speaking to customer]")
        speak(response)
        
        if i < len(test_scenarios):
            print("\nReady for next scenario...")
            time.sleep(2)
    
    print("\n" + "="*70)
    print("  Demo Complete! ✅")
    print("="*70)
    print("\nWhat you just saw:")
    print("  1. Real-time voice input (Whisper)")
    print("  2. Intent classification (Gemini)")
    print("  3. Data retrieval (SQLite + ChromaDB)")
    print("  4. Business rule enforcement (Decision engine)")
    print("  5. Natural language generation (Gemini)")
    print("  6. Voice output (gTTS)")
    print("\nAll happening in real-time on a single voice call!\n")


if __name__ == "__main__":
    demo()
