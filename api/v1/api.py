from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter()

from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest
from agents.autoscaling import autoscaling_solver
from agents.llm import LiteLLMWrapper

class SimpleLLMRequest(BaseModel):
    prompt: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    model: Optional[str] = "gpt-4o-mini"


class AutoscalingResponse(BaseModel):
    success: bool
    num_solvers: int
    solutions: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

async def stream_solutions(problem_breakdown: Dict[str, Any]):
    try:
        num_solvers = await autoscaling_solver(problem_breakdown)
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

@router.post("/simple_llm")
async def simple_llm(request: SimpleLLMRequest):
    try:
        llm = LiteLLMWrapper(
            model=request.model,
            temperature=request.temperature
        )
        response = llm.generate(
            prompt=request.prompt,
            system_message=request.system_message,
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

@router.post("/autoscaling")
async def autoscaling(request: BreakerRequest):
    try:
        breaker = AIBreaker()
        breakdown = await breaker.process_request(request)
        
        return StreamingResponse(
            stream_solutions(breakdown),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))