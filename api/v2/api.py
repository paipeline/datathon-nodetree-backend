from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

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
    带有上下文历史的流式处理端点，用于处理问题并生成解决方案
    
    Args:
        request: BreakerRequest 包含问题详情和上下文信息
        
    Returns:
        StreamingResponse 包含解决方案流
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
    从 round_stream 生成器生成带有上下文的 SSE 事件
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
