from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import json
router = APIRouter()

from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest
from core.round_stream import round_stream
from agents.llm import LiteLLMWrapper
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    model: Optional[str] = MODEL_NAME


class AutoscalingResponse(BaseModel):
    success: bool
    num_solvers: int
    solutions: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    role: str
    content: str


async def stream_solutions(problem_breakdown: Dict[str, Any]):
    try:
        num_solvers = await round_stream(problem_breakdown)
        sub_problems = problem_breakdown.get('data', {}).get('subProblems', [])
        
        for sub_problem in sub_problems:
            solver = Solver()
            request = SolverRequest(
                subProblem=sub_problem
            )
            solution = await solver.solve(request)
            yield f"data: {solution.json()}\n\n"
            
    except Exception as e:
        yield f"data: {{'error': '{str(e)}'}}\n\n"

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

@router.post("/breaker")
async def problem_breaker(request: BreakerRequest):
    try:
        breaker = AIBreaker()
        response = await breaker.process_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/solver")
async def problem_solver(request: SolverRequest):
    try:
        solver = Solver()
        response = await solver.solve(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/round")
async def round_stream_endpoint(request: BreakerRequest):
    """
    Stream endpoint for processing problems and generating solutions
    
    Args:
        request: BreakerRequest containing problem details
        
    Returns:
        StreamingResponse containing solutions
    """
    try:
        return StreamingResponse(
            stream_sse_events(
                problem=request.originalInput,
                follow_up_question=request.followUpQuestion,
                metadata=request.metadata
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_sse_events(
    problem: str,
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Generate SSE events from the round_stream generator
    """
    try:
        async for event in round_stream(
            problem=problem,
            follow_up_question=follow_up_question,
            metadata=metadata
        ):

            event_type = event["event"]
            data = json.dumps(event["data"])
            yield f"event: {event_type}\ndata: {data}\n\n"
            
    except Exception as e:
        error_data = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_data}\n\n"