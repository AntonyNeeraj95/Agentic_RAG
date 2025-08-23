import streamlit as st
import json
import websocket
import threading
import requests
import time
import queue
from typing import Optional
import os

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "ws://localhost:8000")
API_BASE_URL = f"{BACKEND_URL}/api"  # Adjust based on your API structure


# Set page title and favicon
st.set_page_config(page_title="Agentic RAG Chat", page_icon="🤖", layout="wide")

class WebSocketManager:
    def __init__(self):
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.thread: Optional[threading.Thread] = None
        self.message_queue = queue.Queue()
        self.connection_status = {"connected": False, "error": None}
        
    def on_message(self, ws, message):
        """Handle incoming messages - put them in queue for main thread"""
        try:
            data = json.loads(message)
            self.message_queue.put({
                "type": "message",
                "data": {
                    "role": "agent",
                    "answer": data.get("answer", "No answer provided."),
                    "evaluation": data.get("evaluation", "No evaluation provided.")
                }
            })
        except json.JSONDecodeError as e:
            self.message_queue.put({
                "type": "error",
                "data": f"Failed to parse message: {e}"
            })
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.connection_status["error"] = f"WebSocket Error: {error}"
        self.connection_status["connected"] = False
        self.connected = False
        self.message_queue.put({
            "type": "error",
            "data": f"WebSocket Error: {error}"
        })
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.connected = False
        self.connection_status["connected"] = False
        self.message_queue.put({
            "type": "status",
            "data": "Connection closed"
        })
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        self.connected = True
        self.connection_status["connected"] = True
        self.connection_status["error"] = None
        self.message_queue.put({
            "type": "status",
            "data": "Connected successfully"
        })
    
    def connect(self, url: str):
        """Connect to WebSocket"""
        if self.connected:
            return True
            
        try:
            # Close existing connection if any
            self.disconnect()
            
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            self.thread = threading.Thread(
                target=self.ws.run_forever,
                daemon=True
            )
            self.thread.start()
            
            # Wait a moment for connection to establish
            time.sleep(1)
            return True
            
        except Exception as e:
            self.connection_status["error"] = f"Connection failed: {e}"
            return False
    
    def send_message(self, message: dict):
        """Send message through WebSocket"""
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(message))
                return True
            except Exception as e:
                self.message_queue.put({
                    "type": "error",
                    "data": f"Failed to send message: {e}"
                })
                return False
        return False
    
    def disconnect(self):
        """Disconnect WebSocket"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        self.connected = False
        self.connection_status["connected"] = False
    
    def get_messages(self):
        """Get all queued messages"""
        messages = []
        while not self.message_queue.empty():
            try:
                messages.append(self.message_queue.get_nowait())
            except queue.Empty:
                break
        return messages

# Initialize session state
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "ws_manager" not in st.session_state:
        st.session_state.ws_manager = WebSocketManager()
    if "last_status" not in st.session_state:
        st.session_state.last_status = None

init_session_state()

st.title("💬 Agentic RAG Chat")
st.write("This chat connects to your FastAPI /api/v1/ws/chat WebSocket endpoint.")

# WebSocket URL and connection controls
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    ws_url = st.text_input("WebSocket URL:", value=f"{WEBSOCKET_URL}/api/v1/ws/chat")
with col2:
    if st.button("Connect"):
        with st.spinner("Connecting..."):
            if st.session_state.ws_manager.connect(ws_url):
                st.session_state.last_status = "Attempting to connect..."
            else:
                st.session_state.last_status = "Connection failed"
        st.rerun()
with col3:
    if st.button("Disconnect"):
        st.session_state.ws_manager.disconnect()
        st.session_state.last_status = "Disconnected"
        st.rerun()

# Process queued messages
ws_messages = st.session_state.ws_manager.get_messages()
for ws_msg in ws_messages:
    if ws_msg["type"] == "message":
        st.session_state.messages.append(ws_msg["data"])
    elif ws_msg["type"] == "status":
        st.session_state.last_status = ws_msg["data"]
    elif ws_msg["type"] == "error":
        st.session_state.last_status = f"Error: {ws_msg['data']}"

# Show connection status
status = st.session_state.ws_manager.connection_status
if status["connected"]:
    st.success("🟢 Connected to WebSocket")
elif status["error"]:
    st.error(f"🔴 {status['error']}")
else:
    st.info("🔵 Not connected to WebSocket")

# Show last status message
if st.session_state.last_status:
    st.info(st.session_state.last_status)

# --- File Upload Section ---
with st.sidebar:
    st.header("📁 Document Upload")
    uploaded_file = st.file_uploader(
        "Choose a PDF file to upload",
        type=["pdf"],
        help="Upload a PDF to process and make it available for the chatbot's knowledge base."
    )

    if st.button("Process Document", disabled=not uploaded_file):
        with st.spinner("Processing document..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                api_url = f"{API_BASE_URL}/v1/upload/pdf"
                response = requests.post(api_url, files=files)
                
                if response.status_code == 200:
                    st.success("Document processed successfully!")
                    st.json(response.json())
                else:
                    st.error(f"Failed to process document. Status code: {response.status_code}")
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

# --- Chat Interface ---
st.divider()

# Chat input form
with st.form("chat_form", clear_on_submit=True):
    user_query = st.text_area("Your query:", placeholder="Type your message here...", height=100)
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.form_submit_button("Send", use_container_width=True)

# Handle form submission
if send_button and user_query:
    if st.session_state.ws_manager.connection_status["connected"]:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Send message through WebSocket
        if st.session_state.ws_manager.send_message({"query": user_query}):
            st.success("Message sent!")
        else:
            st.error("Failed to send message")
    else:
        st.error("Please connect to WebSocket first")
    
    # Rerun to update the display
    st.rerun()

# Display chat history
if st.session_state.messages:
    st.subheader("Chat History")
    
    # Create a container for the chat messages
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["answer"])
                    with st.expander("Show Agent Evaluation", expanded=False):
                        st.code(msg["evaluation"], language="json")
else:
    st.info("No messages yet. Start a conversation!")

# Auto-refresh section (optional)
if st.session_state.ws_manager.connection_status["connected"]:
    # Add a small delay and check for new messages
    time.sleep(0.1)
    
    # Check if there are new messages to process
    if not st.session_state.ws_manager.message_queue.empty():
        st.rerun()
        
# Add refresh button for manual refresh
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Refresh", help="Manually refresh to check for new messages"):
        st.rerun()

# Clear chat button
with st.sidebar:
    st.divider()
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

# Debug information (optional - can be removed in production)
with st.sidebar:
    st.divider()
    with st.expander("Debug Info"):
        st.write("Connection Status:", st.session_state.ws_manager.connection_status)
        st.write("Queue Size:", st.session_state.ws_manager.message_queue.qsize())
        st.write("Total Messages:", len(st.session_state.messages))