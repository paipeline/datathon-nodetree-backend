# this file is used to autoscale the number of nodes that needs to solve the problem



import os
import time
import logging
from typing import Dict, Any, Optional
from litellm import completion

MAX_NUM_SOLVERS = 10

def get_subtasks_len(problem_breakdown: Dict[str, Any]) -> int:
    return len(problem_breakdown.get('data', {}).get('subProblems', []))

def autoscaling_llm(problem_breakdown: Dict[str, Any]) -> int: # Dict from breaker
    """
    Calculate the required number of LiteLLM calls based on the output of the problem breakdown
    
    Args:
        problem_breakdown (Dict[str, Any]): Output of the LLM problem breaker
        
    Returns:
        int: Required number of calls
    """
    try:
        num_solvers = get_subtasks_len(problem_breakdown)
    except Exception as e:
        logging.error(f"Error calculating the required number of calls: {str(e)}")

    
if __name__ == "__main__":
    import asyncio
    from agents.breaker import AIBreaker, BreakerRequest
    
    async def main():
        breaker = AIBreaker()
        request = BreakerRequest(
            userId="test_user",
            originalInput="Create a web application that allows users to track their daily expenses and generate monthly reports.",
            followUpQuestion="how to perform CRUD operations in Next.js?"
        )
        response = await breaker.process_request(request)
        print(response)
        print(f"number of solvers: {get_subtasks_len(response)}")              
        

    asyncio.run(main())
