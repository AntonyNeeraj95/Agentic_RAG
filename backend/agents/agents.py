from typing import List, Dict
from langgraph.graph import StateGraph, END, START
from langchain_ollama import ChatOllama
from langchain.schema import Document
from backend.db.qdrant_db import vector_store
from typing_extensions import TypedDict
import os
from serpapi import GoogleSearch

from langchain.schema import Document
from IPython.display import Image
 
from pprint import pprint

os.environ["SERPAPI_API_KEY"] = "67a7d178a26af541599594f1fa9e352bebf8311c87b597507ef950c300e16ab7"
class State(TypedDict):
    query: str
    docs: List[Document] = None
    answer: str = None
    eval_result: Dict = None
    route: str = None  # "DB" or "WEB"

# --- Router Agent ---
def router_node(state: State) -> State:
    vector_db = vector_store
    retriever = vector_db.as_retriever(search_kwargs={"k": 1, "score_threshold": 0.5})
    results = retriever.get_relevant_documents(state['query'])
    print("Retrieved results:", results)
    
    if results:
        state["route"] = "DB"
    else:
        state["route"] = "WEB"
    
    return state

# --- Retrieval Agent ---
def retrieval_node(state: State) -> State:
    vector_db = vector_store
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    state["docs"] = retriever.get_relevant_documents(state['query'])
    return state


def web_search_node(state: State) -> State:
    query = state["query"]
    api_key = os.environ.get("SERPAPI_API_KEY") or "your_api_key_here"
    params = {  
        "q": query,  
        "api_key": api_key,  
        "num": 5,  
        "engine": "google",  
    }  

    try:  
        search = GoogleSearch(params)  
        results = search.get_dict()  

        # Extract organic results  
        organic = results.get("organic_results", [])  
        passages = [r["snippet"] for r in organic if "snippet" in r]  

        joined = "\n".join(passages[:3]) or "No relevant web results found."  
    except Exception as e:  
        joined = f"Web search failed: {str(e)}"  

    state["docs"] = [Document(page_content=joined)]  
    return state  

# --- Generation Agent ---
def generation_node(state: State) -> State:
    llm = ChatOllama(model="llama3.2:3b", temperature=0.1)
    docs_text = "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(state['docs'])])
    prompt = f"""
    You are a helpful assistant.
    Answer the query using ONLY the information provided.

    Query: {state['query']}
    Information:
    {docs_text}
    """
    state['answer'] = llm.invoke(prompt).content.strip()
    return state

# --- Evaluation Agent ---
def evaluation_node(state: State) -> State:
    llm = ChatOllama(model="llama3.2:3b", temperature=0)
    docs_text = "\n\n".join([f"[{i+1}] {d.page_content}" for i, d in enumerate(state['docs'])])
    prompt = f"""
    Evaluate the following RAG output.

    Query: {state['query']}
    Retrieved info:
    {docs_text}
    Answer: {state['answer']}

    Provide two scores between 0 and 1:
    - faithfulness
    - relevance

    Output Requirements:
    - Return only valid JSON — no extra text, no markdown, no code fences.
    - The JSON must have exactly the following keys:

        "faithfulness": "...",
        "relevance": "...",
        "comment": "<brief explanation>"

    - Do not infer or assume missing information beyond what is provided.
    - The response must be directly parseable by JSON parsers.
    """
    import json
    # try:
    resp = llm.invoke(prompt).content
    # print("Response from LLM:", resp)   
   
    # json_resp = json.loads(resp)
    # print("Evaluation Result:", json_resp)
    # except:
    state['eval_result'] = resp
    return state

# --- Graph Wiring ---
graph = StateGraph(State)

graph.add_node("router", router_node)
graph.add_node("retrieval", retrieval_node)
graph.add_node("web_search", web_search_node)
graph.add_node("generation", generation_node)
graph.add_node("evaluation", evaluation_node)

graph.add_edge(START,"router")
graph.add_conditional_edges("router", lambda s: ( "web_search", "retrieval")[s['route'] == "DB"], ["retrieval", "web_search"])
graph.add_edge("retrieval", "generation")
graph.add_edge("web_search", "generation")
graph.add_edge("generation", "evaluation")
graph.add_edge("evaluation", END)

app = graph.compile()

# Visualize the graph
img = Image(app.get_graph(xray=True).draw_mermaid_png())
with open("graph_diagram1.png", "wb") as f:
    f.write(img.data)


async def run(query: str) -> State:
    """Run the agent with the given query."""
    print("**"*50)
    result = await app.ainvoke({"query": query})

    return result
# Example run
if __name__ == "__main__":
    query = "what is plan agent?"
    import asyncio

    result = asyncio.run(run(query))
    pprint(result)
    print(result.keys())
