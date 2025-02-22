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

    