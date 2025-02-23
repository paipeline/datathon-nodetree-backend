from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest, SubProblem

async def round_stream(
    problem: str,
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Wrapper function to process problems and generate solutions with SSE streaming
    
    Args:
        problem (str): Original problem description
        follow_up_question (Optional[str]): Optional follow-up question
        metadata (Optional[Dict[str, Any]]): Additional metadata
    
    Yields:
        Dict[str, Any]: Stream of events containing breakdown and solution updates
    """
    breaker = AIBreaker()
    breaker_request = BreakerRequest(
        originalInput=problem,
        followUpQuestion=follow_up_question,
        metadata={"language": metadata.get('language', 'English')}
    )

    # 首先流式输出问题分解结果
    breakdown = await breaker.process_request(breaker_request)
    yield {
        "event": "breakdown",
        "data": breakdown
    }

    solutions = []
    sub_problems = breakdown.get('data', {}).get('subProblems', [])
    
    for sub_problem in sub_problems:
        solver = Solver(language=breakdown.get('metadata', {}).get('language', metadata.get('language', 'English')))
        solver_request = SolverRequest(
            subProblem=SubProblem(
                title=sub_problem.get('title', ''),
                description=sub_problem.get('description', ''),
                objective=sub_problem.get('objective', ''),
                id=sub_problem.get('id', ''),
                language=breakdown.get('metadata', {}).get('language', metadata.get('language', 'English'))
            ),
            metadata=breakdown.get('metadata', {'language': metadata.get('language', 'English')})
        )
        solution = await solver.solve(solver_request)
        
        current_solution = {
            'id': sub_problem.get('id'),
            'title': sub_problem.get('title'),
            'description': sub_problem.get('description'),
            'objective': sub_problem.get('objective'),
            'solution': solution.content
        }
        solutions.append(current_solution)
        
        yield {
            "event": "solution",
            "data": current_solution
        }
    

    yield {
        "event": "complete",
        "data": {
            'breakdown': breakdown,
            'solutions': solutions
        }
    }

if __name__ == "__main__":
    async def main():
        async for event in round_stream(
            problem="Create a web application that allows users to track their daily expenses and generate monthly reports.",
            follow_up_question="how to perform CRUD operations in Next.js?",
            metadata={"language": "English"}
        ):
            print(f"\nEvent Type: {event['event']}")
            print("Data:", event['data'])
            print("-" * 80)

    asyncio.run(main())
