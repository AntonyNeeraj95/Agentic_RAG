import json
import asyncio
import traceback  # Import traceback for detailed error logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Import the run function from your agentic workflow.
# It is crucial that the file backend/agents/agents.py exists and is accessible.
from backend.agents.agents import run as agent_run

# The APIRouter handles all endpoints for this module
router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the chatbot.
    Receives a query, runs the agent, and streams the final answer and evaluation.
    """
    await websocket.accept()
    print("WebSocket accepted.")
    try:
        while True:
            # Receive the message as a JSON string
            message_json = await websocket.receive_text()
            data = json.loads(message_json)
            user_query = data.get("query", "")
            print(f"Received message: {user_query}")

            final_answer = 'Sorry, an error occurred in the agent.'
            evaluation = 'No evaluation available.'
            status = 'error'

            try:
                # Run the agentic workflow with the user's query
                # The agent will handle routing, retrieval, generation, and evaluation.
                result_state = await agent_run(user_query)

                # Safely get the results from the agent's output
                final_answer = result_state.get('answer', 'Sorry, I could not generate an answer.')
                evaluation = result_state.get('eval_result', 'No evaluation available.')
                status = 'success'
                
            except Exception as e:
                # Log the detailed traceback to help with debugging
                print("An error occurred during agent execution:")
                traceback.print_exc()
                final_answer = "An internal error occurred. Please check the backend logs for details."
                evaluation = {"error": str(e), "traceback": traceback.format_exc()}
            
            # Create a structured JSON response with the final answer and evaluation
            response_payload = {
                "answer": final_answer,
                "evaluation": evaluation,
                "original_query": user_query,
                "status": status
            }
            print("asdafrgfwrgrwgwgwgrwgwg\n")
            # Send the JSON response back to the client
            await websocket.send_json(response_payload)
            print("Sent response back to client:", response_payload)
            # print("Sent response back to client.")

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"An unexpected error occurred in the WebSocket loop: {e}")