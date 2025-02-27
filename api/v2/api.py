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
    parent_id: Optional[str] = None

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
        
        # 处理 UUID 格式的 ID
        try:
            if len(request.id) == 36:  # UUID 格式
                hex_id = uuid.UUID(request.id).hex[:24]
                object_id = ObjectId(hex_id)
            else:  # 已经是 24 位的 hex 格式
                object_id = ObjectId(request.id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")
        
        # 更新优先级
        result = await collection.update_one(
            {'_id': object_id},
            {'$set': {'priority': request.priority}}
        )
        
        if result.modified_count == 0:
            # 检查文档是否存在
            doc = await collection.find_one({'_id': object_id})
            if not doc:
                raise HTTPException(status_code=404, detail="Node not found")
            # 如果文档存在但没有修改，可能是设置了相同的优先级
        
        # 获取更新后的节点
        updated_node = await collection.find_one({'_id': object_id})
        if not updated_node:
            raise HTTPException(status_code=404, detail="Node not found after update")
        
        # 确保返回正确的 ID 格式
        updated_node['id'] = str(updated_node['_id'])
        del updated_node['_id']
        
        return {
            "success": True,
            "node": updated_node
        }
        
    except HTTPException:
        
        raise
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
        return StreamingResponse(
            stream_context_events(
                problem=request.originalInput,
                client=client,
                follow_up_question=request.followUpQuestion,
                metadata=request.metadata,
                parent_id=request.metadata.get('parent_id') if request.metadata else None
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
    parent_id: Optional[str] = None
):
    """
    Generates SSE events with context from the round_stream generator
    """
    try:
        async for event in round_stream(
            problem=problem,
            client=client,
            follow_up_question=follow_up_question,
            metadata=metadata,
            parent_id=parent_id
        ):
            event_type = event["event"]
            data = json.dumps(event["data"])
            yield f"event: {event_type}\ndata: {data}\n\n"
            
    except Exception as e:
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"


