import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent.graph import run_agent
from voice.stt import listen, transcribe
from voice.tts import speak
from fastapi.responses import Response
import tempfile
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ShopVoice Agent")

# Exotel credentials
EXOTEL_ACCOUNT_SID = os.getenv("EXOTEL_ACCOUNT_SID")
EXOTEL_API_KEY = os.getenv("EXOTEL_API_KEY")
EXOTEL_API_TOKEN = os.getenv("EXOTEL_API_TOKEN")


class TextRequest(BaseModel):
    message: str


# Global dictionary to store agent responses per CallSid
# In production, use a real database like Redis
call_responses = {}

@app.post("/exotel/incoming")
async def exotel_incoming_call(request_obj: Request):
    """
    (Deprecated for this flow, but kept just in case)
    """
    return Response(status_code=200)


@app.post("/exotel/process")
async def exotel_process_speech(request_obj: Request):
    """
    Step 3 in App Bazaar: Passthru Applet.
    Exotel sends the RecordingUrl here. We process it and save the response.
    """
    print("\n[EXOTEL] Processing recorded speech...")
    form_data = await request_obj.form()
    
    call_sid = form_data.get("CallSid")
    recording_url = form_data.get("RecordingUrl")
    caller_number = form_data.get("From")
    
    print(f"[EXOTEL] Caller: {caller_number}, CallSid: {call_sid}")
    
    if not recording_url:
        print("[EXOTEL] No recording URL received.")
        call_responses[call_sid] = "Sorry, I couldn't hear you clearly."
        return Response(status_code=200)
        
    print(f"[EXOTEL] Downloading audio from {recording_url}")
    try:
        auth = (EXOTEL_API_KEY, EXOTEL_API_TOKEN) if EXOTEL_API_KEY and EXOTEL_API_TOKEN else None
        audio_resp = requests.get(recording_url, auth=auth)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_resp.content)
            tmp_path = tmp.name
            
        print("[EXOTEL] Transcribing audio...")
        user_message = transcribe(tmp_path)
    except Exception as e:
        print(f"[EXOTEL] Error processing audio: {e}")
        user_message = "Hello, what is my order status?" 
        
    print(f"[EXOTEL] Understood: {user_message}")
    agent_response = run_agent(user_message)
    print(f"[EXOTEL] Agent says: {agent_response}")
    
    # Store the response so the next Greeting applet can fetch it
    call_responses[call_sid] = agent_response
    
    return Response("OK", status_code=200)


@app.get("/exotel/get-response")
async def exotel_get_response(request_obj: Request):
    """
    Step 4 in App Bazaar: Greeting Applet (Dynamic Text).
    Exotel hits this to get the text to read out loud.
    """
    call_sid = request_obj.query_params.get("CallSid")
    
    # Wait up to 5 seconds if the processing is slightly delayed
    import time
    for _ in range(10):
        if call_sid in call_responses:
            answer = call_responses.pop(call_sid)
            print(f"[EXOTEL] Sending text to phone: {answer}")
            return Response(content=answer, media_type="text/plain")
        time.sleep(0.5)
        
    return Response(content="I am sorry, my connection timed out while processing your request.", media_type="text/plain")
def chat(request: TextRequest):
    """
    Receive text input, run the agent, return text response.
    """
    message = request.message
    print(f"\n[API] Received: {message}")
    
    response = run_agent(message)
    print(f"[API] Responding: {response}")
    
    return {"response": response}


@app.post("/voice")
def voice_chat():
    """
    Full voice pipeline: listen → agent → speak
    """
    print("\n[API] Starting voice conversation...")
    print("[API] Listening for 5 seconds...")
    
    # Step 1 — Listen
    user_message = listen(duration=5)
    print(f"[API] You said: {user_message}")
    
    # Step 2 — Think
    response = run_agent(user_message)
    print(f"[API] Agent says: {response}")
    
    # Step 3 — Speak
    speak(response)
    
    return {
        "user_message": user_message,
        "agent_response": response
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "ShopVoice AI Agent",
        "version": "1.0",
        "endpoints": {
            "POST /chat": "Send text, get text response",
            "POST /voice": "Full voice conversation (listen → think → speak)",
            "GET /health": "Health check",
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("\n[API] Starting ShopVoice Agent Server on http://localhost:8000")
    print("[API] Open http://localhost:8000 in browser to see API docs")
    print("[API] Press Ctrl+C to stop\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)