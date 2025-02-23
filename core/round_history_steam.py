from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
from agents.breaker import AIBreaker, BreakerRequest
from agents.solver import Solver, SolverRequest, SubProblem
from datetime import datetime
from db.database import get_client  # Changed to directly import from database module
import logging
from db.find_history import get_solution_history, save_solution
import uuid
import json

from bson import ObjectId 

logger = logging.getLogger(__name__)

def serialize_solution(solution: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the solution to ensure all fields are available
    """
    # Directly return the original solution without serialization
    return solution


async def round_stream(
    problem: str,
    client,  # MongoDB client instance
    follow_up_question: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream processing function for generating solutions
    """
    try:
        # Retrieve history records
        solution_history = []
        if parent_id:
            solution_history = await get_solution_history(parent_id, client)
            # No longer need to serialize history records
            # solution_history = [serialize_solution(sol) for sol in solution_history]
        
        breaker = AIBreaker()
        breaker_request = BreakerRequest(
            originalInput=problem,
            followUpQuestion=follow_up_question,
            metadata={"language": metadata.get('language', 'English')},
            context={"solutionHistory": solution_history}
        )

        breakdown = await breaker.process_request(breaker_request)
        
        # Get the list of sub-problems
        sub_problems = breakdown.get('data', {}).get('subProblems', [])
        if not sub_problems:
            # If there are no sub-problems, create a default sub-problem
            sub_problems = [{
                'title': 'Solution',
                'description': problem,
                'objective': follow_up_question or 'Provide a complete solution',
                'id': str(uuid.uuid4())
            }]

        # Process each sub-problem
        for sub_problem in sub_problems:
            solver = Solver(
                language=metadata.get('language', 'English')
            )
            
            # Create solver request
            solver_request = SolverRequest(
                subProblem=SubProblem(
                    title=sub_problem.get('title', ''),
                    description=sub_problem.get('description', ''),
                    objective=sub_problem.get('objective', ''),
                    id=sub_problem.get('id', ''),
                    language=metadata.get('language', 'English')
                ),
                metadata=metadata,
                context={
                    "originalProblem": problem,
                    "solutionHistory": solution_history,
                    "followUpQuestion": follow_up_question
                }
            )
            
            # Get the solution
            solution = await solver.solve(solver_request)
            
            # Create the current solution
            current_solution = {
                'title': sub_problem.get('title'),
                'description': sub_problem.get('description'),
                'objective': sub_problem.get('objective'),
                'solution': solution.content,
                'problem': problem,
                'follow_up_question': follow_up_question,
                'created_at': datetime.utcnow().isoformat(),
                'parent_id': parent_id,
                'metadata': metadata,
                '_id': str(uuid.uuid4()),
                'priority': 0
            }
            
            # Save the solution
            saved_id = await save_solution(current_solution, client)
            if saved_id:
                # Ensure ObjectId is converted to string
                current_solution['id'] = str(saved_id) if isinstance(saved_id, ObjectId) else str(saved_id)
                current_solution['_id'] = str(current_solution['_id'])
                
                # Directly use the original dictionary without any conversion
                data = {
                    "event": "solver_output",
                    "data": dict(current_solution)
                }
                yield data
            
    except Exception as e:
        logger.error(f"Error in round stream: {str(e)}")
        error_data = {
            "error": str(e),
            "problem": problem,
            "follow_up_question": follow_up_question
        }
        yield {
            "event": "error",
            "data": error_data
        }

if __name__ == "__main__":
    async def main():
        client = None
        try:
            # Set log level
            logging.basicConfig(level=logging.INFO)
            
            # Initialize database connection
            await connect_to_mongo()
            client = get_client()
            
            # Validate database connection
            db = client['nodetree']
            collections = await db.list_collection_names()
            print(f"Available collections: {collections}")
            
            # First call - Create the initial node
            print("\n=== Creating the initial node: Basic To-Do App ===")
            first_id = None
            async for event in round_stream(
                problem="Create a simple to-do app",
                client=client,
                metadata={"language": "English"}
            ):
                print(f"\nEvent type: {event['event']}")
                print("Data:", event['data'])
                print("-" * 80)
                first_id = event['data']['id']

            # Second call - Add user authentication
            print("\n=== Adding user authentication ===")
            second_id = None
            async for event in round_stream(
                problem="How to add user authentication?",
                client=client,
                follow_up_question="What technology stack is needed?",
                metadata={"language": "English"},
                parent_id=first_id
            ):
                print(f"\nEvent type: {event['event']}")
                print("Data:", event['data'])
                print("-" * 80)
                second_id = event['data']['id']

            # Third call - Add task categorization
            print("\n=== Adding task categorization ===")
            third_id = None
            async for event in round_stream(
                problem="How to implement task categorization?",
                client=client,
                follow_up_question="How to design the database model?",
                metadata={"language": "English"},
                parent_id=second_id
            ):
                print(f"\nEvent type: {event['event']}")
                print("Data:", event['data'])
                print("-" * 80)
                third_id = event['data']['id']

            # Fourth call - Add task priority
            print("\n=== Adding task priority ===")
            async for event in round_stream(
                problem="How to add task priority?",
                client=client,
                follow_up_question="How to display different priorities on the interface?",
                metadata={"language": "English"},
                parent_id=third_id
            ):
                print(f"\nEvent type: {event['event']}")
                print("Data:", event['data'])
                print("-" * 80)


            print("\n=== Displaying the complete solution history chain ===")
            history = await get_solution_history(third_id, client)
            print("\nComplete history data structure:")
            for idx, item in enumerate(history, 1):
                print(f"\nSolution #{idx}:")
                print("Data structure:")
                print({
                    "id": item.get('id'),
                    "title": item.get('title'),
                    "description": item.get('description'),
                    "objective": item.get('objective'),
                    "solution": item.get('solution'),
                    "problem": item.get('problem'),
                    "follow_up_question": item.get('follow_up_question'),
                    "created_at": item.get('created_at'),
                    "parent_id": item.get('parent_id'),
                    "metadata": item.get('metadata')
                })
                print("-" * 80)
            print("History:")
            print(history)
            # Display the hierarchical relationship of the history records
            print("\nSolution hierarchy structure:")
            def print_tree(items, parent_id=None, level=0):
                for item in items:
                    if item.get('parent_id') == parent_id:
                        print("  " * level + f"├── {item.get('title')} (ID: {item.get('id')})")
                        print_tree(items, item.get('id'), level + 1)
            
            print_tree(history)

        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            if client:
                await close_mongo_connection()

    asyncio.run(main())
