# this file is used to autoscale the number of nodes that needs to solve the problem


import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from litellm import completion
from agents.solver import Solver, SolverRequest, SubProblem
from agents.breaker import AIBreaker, BreakerRequest
from agents.llm import LiteLLMWrapper

MAX_NUM_SOLVERS = 10

def get_subtasks_len(problem_breakdown: Dict[str, Any]) -> int:
    return len(problem_breakdown.get('data', {}).get('subProblems', []))

async def autoscaling_solver_group(problem_breakdown: Dict[str, Any]) -> int:
    """
    Calculate the required number of LiteLLM calls based on the output of the problem breakdown

    Args:
        problem_breakdown (Dict[str, Any]): Output of the LLM problem breaker
        
    Returns:
        int: Required number of calls
    """
    try:
        num_solvers = min(get_subtasks_len(problem_breakdown), MAX_NUM_SOLVERS)
        sub_problems = problem_breakdown.get('data', {}).get('subProblems', [])
        tasks = []
        metadata = problem_breakdown.get('metadata', {})
        if 'language' not in metadata:
            metadata['language'] = 'English'
            
        for sub_problem in sub_problems:
            solver = Solver(language=metadata.get('language', 'English'))
            request = SolverRequest(
                subProblem=SubProblem(
                    title=sub_problem.get('title', ''),
                    description=sub_problem.get('description', ''),
                    objective=sub_problem.get('objective', ''),
                    id=sub_problem.get('id', ''),
                    language=metadata.get('language', 'English')
                ),
                metadata=metadata
            )
            tasks.append(solver.solve(request))
        
        await asyncio.gather(*tasks)
            
        return num_solvers
    except Exception as e:
        logging.error(f"Error in autoscaling solver: {str(e)}")
        return 0

    
async def round_stream(
    problem: str,
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Wrapper function to process problems and generate solutions

    Args:
        problem (str): Original problem description
        follow_up_question (Optional[str]): Optional follow-up question
        user_id (str): User ID
        language (str): Response language

    Returns:
        Dict[str, Any]: Dictionary containing all subproblems and solutions
    """

    breaker = AIBreaker()
    breaker_request = BreakerRequest(
        originalInput=problem,
        followUpQuestion=follow_up_question,
        metadata={"language": metadata.get('language', 'English')}
    )
    

    breakdown = await breaker.process_request(breaker_request)
    

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
        
        solutions.append({
            'id': sub_problem.get('id'),
            'title': sub_problem.get('title'),
            'description': sub_problem.get('description'),
            'objective': sub_problem.get('objective'),
            'solution': solution.content
        })
    
    return {
        'breakdown': breakdown,
        'solutions': solutions
    }

if __name__ == "__main__":
    async def main():
        result = await round_stream(
            problem="Create a web application that allows users to track their daily expenses and generate monthly reports.",
            follow_up_question="how to perform CRUD operations in Next.js?",
            metadata={"language": "English"}
        )
        
        print("Problem Breakdown Results:")
        print(result['breakdown'])
        print(f"\nTotal sub-problems: {len(result['solutions'])}")
        
        print("\nSolutions:")
        for solution in result['solutions']:
            print(f"\nSub-problem: {solution['title']}")
            print(f"ID: {solution['id']}")
            print(f"Description: {solution['description']}")
            print(f"Objective: {solution['objective']}")
            print(f"Solution: {solution['solution']}")
            print("-" * 80)

    asyncio.run(main())
