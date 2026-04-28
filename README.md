# ShopVoice AI Agent

ShopVoice is a powerful AI-driven voice commerce agent designed to handle customer interactions over the phone. It integrates with **Exotel** to process incoming calls, uses **Google Generative AI (Gemini)** via **LangChain & LangGraph** for intelligent decision making, and includes a full **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** pipeline.

The system also provides a full-stack mock eCommerce environment, featuring a customer storefront and a real-time order dashboard backed by an SQLite database.

## Features

*   **Telephony Integration (Exotel)**: Connects to Exotel APIs to handle incoming customer phone calls.
*   **Full Voice Pipeline**: 🎙️ Listen (STT) → 🧠 Think (LLM) → 🔊 Speak (TTS).
*   **Intelligent Agent**: Built using LangChain and LangGraph for robust conversational flow and tool execution.
*   **RAG Architecture**: Uses **ChromaDB** to index and retrieve relevant product and store information.
*   **E-Commerce Backend**: Manages customers, products, orders, and refunds using **SQLite3**.
*   **Web Dashboards**:
    *   **Storefront**: A mock UI for customers to view products (`/store`).
    *   **Admin Dashboard**: A beautiful real-time view of all incoming orders and refund statuses (`/`).
*   **Hybrid Demo Mode**: Allows testing the Exotel integration locally using laptop speakers and microphones, heavily utilized for presentations.

## Tech Stack

*   **Backend**: Python, FastAPI, Uvicorn
*   **AI/LLM**: Google Generative AI (Gemini), LangChain, LangGraph
*   **Vector Database**: ChromaDB
*   **Voice/Audio**: gTTS (Google Text-to-Speech), Python SpeechRecognition
*   **Database**: SQLite3
*   **Frontend**: HTML, CSS, Vanilla JavaScript

## Project Structure

```
├── agent/            # LangGraph agent definitions and logic
├── api/              # FastAPI application and endpoints (main.py)
├── data/             # SQLite databases and ChromaDB storage
├── frontend/         # HTML/CSS files for the Dashboard and Store
├── tools/            # Custom tools available to the LangChain Agent
├── voice/            # STT (Speech-to-Text) and TTS (Text-to-Speech) modules
├── .env              # Environment variables
├── requirements.txt  # Python dependencies
├── hybrid_demo.py    # Hybrid voice demo server with Exotel triggers
└── demo.py           # Standard demonstration script
```

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Charan7960/minor-project.git
   cd minor-project
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add the necessary credentials:
   ```env
   # LLM
   GOOGLE_API_KEY=your_gemini_api_key

   # Exotel Credentials
   EXOTEL_ACCOUNT_SID=your_exotel_sid
   EXOTEL_API_KEY=your_exotel_api_key
   EXOTEL_API_TOKEN=your_exotel_api_token
   EXOTEL_PHONE_NUMBER=your_exotel_phone_number
   ```

## Running the Project

### 1. Standard API Server
To run the primary FastAPI server for Chat and Exotel Voice passthrough endpoints:
```bash
python api/main.py
```
*   **Docs**: `http://localhost:8000/docs`

### 2. Hybrid Demo Mode
To run the demo server with the beautiful UI dashboards and the hybrid Exotel/Local-Voice trigger:
```bash
python hybrid_demo.py
```
*   **Admin Dashboard**: `http://localhost:8000/`
*   **Storefront**: `http://localhost:8000/store`

*Note: If connecting to Exotel, you must run `ngrok http 8000` and configure the generated Ngrok URL in your Exotel Applet.*

## License

This project is created for educational and presentation purposes.
