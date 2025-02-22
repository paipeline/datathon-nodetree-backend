# this file is used to autoscale the number of nodes that needs to solve the problem



import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional
from litellm import completion
from agents.solver import Solver, SolverRequest, SubProblem
MAX_NUM_SOLVERS = 10

def get_subtasks_len(problem_breakdown: Dict[str, Any]) -> int:
    return len(problem_breakdown.get('data', {}).get('subProblems', []))

async def autoscaling_solver(problem_breakdown: Dict[str, Any]) -> int:
    """
    Calculate the required number of LiteLLM calls based on the output of the problem breakdown
    
    Args:
        problem_breakdown (Dict[str, Any]): Output of the LLM problem breaker
        
    Returns:
        int: Required number of calls
    """
    try:
        num_solvers = get_subtasks_len(problem_breakdown)
        sub_problems = problem_breakdown.get('data', {}).get('subProblems', [])
        
        # 创建任务列表
        tasks = []
        for sub_problem in sub_problems:
            solver = Solver()
            request = SolverRequest(
                subProblem=SubProblem(
                    title=sub_problem.get('title', ''),
                    description=sub_problem.get('description', ''),
                    objective=sub_problem.get('objective', ''),
                    id=sub_problem.get('id', '')  # 确保包含id
                )
            )
            tasks.append(solver.solve(request))
        
        await asyncio.gather(*tasks)
            
        return num_solvers
    except Exception as e:
        logging.error(f"Error in autoscaling solver: {str(e)}")
        return 0

    
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
        print("问题分解结果：")
        print(response)
        print(f"\n需要的求解器数量: {get_subtasks_len(response)}")              
        
        print("\n开始解决子问题：")
        sub_problems = response.get('data', {}).get('subProblems', [])
        for sub_problem in sub_problems:
            solver = Solver()
            request = SolverRequest(
                subProblem=SubProblem(
                    title=sub_problem.get('title', ''),
                    description=sub_problem.get('description', ''),
                    objective=sub_problem.get('objective', ''),
                    id=sub_problem.get('id', '')
                )
            )
            solution = await solver.solve(request)
            print(f"\n子问题: {sub_problem.get('title')}")
            print("解决方案:")
            
            print(f"子问题ID: {sub_problem.get('id')}")
            print(f"子问题标题: {sub_problem.get('title')}")
            print(f"子问题描述: {sub_problem.get('description')}")
            print(f"子问题目标: {sub_problem.get('objective')}")
            print(f"子问题解决方案: {solution.content}")
            
            print("-" * 80)

    asyncio.run(main())
