import sys
import os
import time
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import Response
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

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ShopVoice AI Agent — Hybrid Voice Demo Server")
    print("="*70)
    print("\n[HYBRID] Ensure ngrok is running on port 8000:  ngrok http 8000")
    print("[HYBRID] Press Ctrl+C to stop the server\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
