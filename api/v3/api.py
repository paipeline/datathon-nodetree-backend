from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from bson.objectid import ObjectId

from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest
from core.round_history_steam import round_stream
from agents.llm import LiteLLMWrapper
from rag.run import search_documents

load_dotenv()

router = APIRouter()
MODEL_NAME = os.getenv("MODEL_NAME")

def get_db_client():
    from db.database import get_client
    return get_client()

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    model: Optional[str] = MODEL_NAME

class Message(BaseModel):
    role: str
    content: str

class PriorityUpdateRequest(BaseModel):
    id: str
    priority: int

@router.post("/set-priority")
async def set_priority(request: PriorityUpdateRequest):
    """
    Updates the priority of a node
    
    Args:
        request: Request containing node ID and new priority
        
    Returns:
        Updated node data
    """
    try:
        client = get_db_client()
        db = client['nodetree']
        collection = db['nodes']
        
        hex_id = uuid.UUID(request.id).hex[:24]
        object_id = ObjectId(hex_id)
        
        result = await collection.update_one(
            {'_id': object_id},
            {'$set': {'priority': request.priority}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Node not found")
            
        updated_node = await collection.find_one({'_id': object_id})
        if not updated_node:
            raise HTTPException(status_code=404, detail="Node not found")
            
        updated_node['id'] = request.id
        updated_node['_id'] = updated_node['id']
        
        return {
            "success": True,
            "node": updated_node
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        llm = LiteLLMWrapper(
            model=request.model,
            temperature=request.temperature
        )

        system_message = "When returning mathematical formulas, you need to add extra $$ symbols to wrap latex formulas"
        response = llm.generate(
            prompt=request.prompt,
            system_message=system_message,
            max_tokens=request.max_tokens
        )
        
        return {"success": True, "content": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/round_context")
async def round_context_endpoint(request: BreakerRequest):
    """
    Endpoint for streaming processing with context history, used for processing questions and generating solutions
    
    Args:
        request: BreakerRequest containing question details and context information
        
    Returns:
        StreamingResponse containing solution streams
    """
    try:
        client = get_db_client()
        

        relevant_docs = search_documents(request.originalInput, k=2)
        
        return StreamingResponse(
            stream_context_events(
                problem=request.originalInput,
                client=client,
                follow_up_question=request.followUpQuestion,
                metadata=request.metadata,
                parent_id=request.metadata.get('parent_id') if request.metadata else None,
                relevant_docs=relevant_docs
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_context_events(
    problem: str,
    client,
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None,
    relevant_docs: Optional[List] = None
):
    """
    Generates SSE events with context from the round_stream generator
    """
    try:
        context = ""
        if relevant_docs:
            context = "Based on the following relevant research (top 2 most relevant documents):\n\n"
            for metadata, content in relevant_docs:
                context += f"From '{metadata.get('title', 'Untitled')}' by {metadata.get('authors', 'Unknown Authors')}:\n"
                context += f"{content}\n\n"
        
        async for event in round_stream(
            problem=problem,
            client=client,
            follow_up_question=follow_up_question,
            metadata=metadata,
            parent_id=parent_id,
            additional_context=context  # 传递额外的上下文
        ):
            event_type = event["event"]
            data = json.dumps(event["data"])
            yield f"event: {event_type}\ndata: {data}\n\n"
            
    except Exception as e:
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"

