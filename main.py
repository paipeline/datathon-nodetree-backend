from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from agents.llm import LiteLLMWrapper

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None

@router.post("/generate")
async def generate_response(request: GenerateRequest):
    try:
        llm = LiteLLMWrapper.get_instance()
        response = await llm.generate(
            prompt=request.prompt,
            system_message=request.system_message,
            max_tokens=request.max_tokens,
            stop=request.stop
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        llm = LiteLLMWrapper.get_instance()
        messages = [msg.dict() for msg in request.messages]
        response = await llm.generate_with_history(
            messages=messages,
            max_tokens=request.max_tokens,
            stop=request.stop
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))