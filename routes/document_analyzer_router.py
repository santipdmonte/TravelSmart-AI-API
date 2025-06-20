"""
main_document_routes.py
Routes for the document analyzer graph
"""

from fastapi import APIRouter
from graphs.document_analyzer_graph import graph
from langgraph.types import Command

document_analyzer_router = APIRouter(prefix="/document", tags=["Document Analyzer"])

@document_analyzer_router.post("/initialize_graph")
def initialize_graph(thread_id: str):

    initial_state = {
            "state": "initial",
            "document_path": "test_path.pdf",
            "type_action": "",
            "action_suggestion": "",
            "user_feedback": ""
        }   
    
    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(initial_state, config=config)

    return {"message": "Graph initialized"}

@document_analyzer_router.post("/HIL_response")
def user_HIL_response(thread_id: str, user_HIL_response: str):

    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(Command(resume={"messages": user_HIL_response}), config=config)

    return {"message": "User response received"}




