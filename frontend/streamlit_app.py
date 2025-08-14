import streamlit as st
import json
import websocket
import threading
import requests
import queue

# Set page title and favicon
st.set_page_config(page_title="Agentic RAG Chat", page_icon="🤖", layout="wide")

st.title("💬 Agentic RAG Chat")
st.write("This chat connects to your FastAPI `/api/v1/ws/chat` WebSocket endpoint.")

# Store chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Store WebSocket connection in session state
if "ws" not in st.session_state:
    st.session_state.ws = None
    
# Store a thread-safe queue for inter-thread communication
if "message_queue" not in st.session_state:
    st.session_state.message_queue = queue.Queue()

# Callback function for WebSocket messages
def on_message(ws, message):
    """
    Handles incoming JSON messages from the FastAPI backend.
    Instead of rerunning the app directly, it puts the message in a queue.
    """
    st.session_state.message_queue.put(message)

# Callback function for WebSocket errors
def on_error(ws, error):
    st.error(f"WebSocket Error: {error}")

# Callback function for WebSocket close event
def on_close(ws, close_status_code, close_msg):
    st.warning("WebSocket connection closed.")
    st.session_state.ws = None

# Function to connect and listen to WS messages
def connect_ws():
    """
    Establishes and manages the WebSocket connection in a separate thread.
    """
    if st.session_state.ws is None:
        try:
            ws_url = "ws://localhost:8000/api/v1/ws/chat"
            st.session_state.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            # Run the WebSocket connection in a background thread
            ws_thread = threading.Thread(target=st.session_state.ws.run_forever, daemon=True)
            ws_thread.start()
            st.success("WebSocket connection established!")
        except Exception as e:
            st.error(f"Could not connect to WebSocket server: {e}")
            st.session_state.ws = None

# Function to check the message queue and update the UI
def poll_messages():
    """
    Checks the queue for new messages and safely updates Streamlit's state.
    """
    if not st.session_state.message_queue.empty():
        message = st.session_state.message_queue.get()
        try:
            data = json.loads(message)
            st.session_state.messages.append({
                "role": "agent",
                "answer": data.get("answer", "No answer provided."),
                "evaluation": data.get("evaluation", "No evaluation provided.")
            })
        except json.JSONDecodeError:
            st.session_state.messages.append({
                "role": "agent",
                "answer": "Received a malformed message from the server.",
                "evaluation": message
            })
        st.experimental_rerun()

# Establish WebSocket connection on app load
connect_ws()

# Poll the message queue every time the script reruns
poll_messages()

# --- New File Upload Section ---
# Use a sidebar for the file uploader to keep the main chat view clean
st.sidebar.header("📁 Document Upload")
uploaded_file = st.sidebar.file_uploader(
    "Choose a PDF file to upload",
    type=["pdf"],
    help="Upload a PDF to process and make it available for the chatbot's knowledge base."
)
upload_button = st.sidebar.button("Process Document")

if upload_button and uploaded_file:
    # Use a spinner to show that the app is working
    with st.spinner("Processing document..."):
        try:
            # Prepare the file for the POST request
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            
            # Send the file to the FastAPI endpoint
            api_url = "http://localhost:8000/api/v1/upload/pdf"
            response = requests.post(api_url, files=files)
            
            # Check the response from the server
            if response.status_code == 200:
                st.sidebar.success("Document processed successfully!")
                st.sidebar.json(response.json())
            else:
                st.sidebar.error(f"Failed to process document. Server responded with status code: {response.status_code}")
                st.sidebar.write(response.json())
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"An error occurred while connecting to the backend API: {e}")

# --- Chat Interface Section ---
st.divider()

# Input box and send button
user_query = st.text_input("Your query:", key="query_input")
send_button = st.button("Send")

if send_button and user_query:
    if st.session_state.ws and st.session_state.ws.sock and st.session_state.ws.sock.connected:
        payload = json.dumps({"query": user_query})
        st.session_state.ws.send(payload)
        st.session_state.messages.append({"role": "user", "content": user_query})
        # Clear the input box after sending
        st.experimental_set_query_params(query_input="")
    else:
        st.error("WebSocket is not connected. Please refresh the page.")

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**🧑 You:** {msg['content']}")
    else:
        st.markdown(f"**🤖 Agent:**")
        st.markdown(msg['answer'])
        with st.expander("Show Agent Evaluation"):
            st.code(msg['evaluation'], language="json")
