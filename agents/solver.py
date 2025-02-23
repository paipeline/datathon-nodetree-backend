from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from agents.llm import LiteLLMWrapper
from dotenv import load_dotenv
import os

load_dotenv()


MODEL_NAME = os.getenv("MODEL_NAME")

class SubProblem(BaseModel):
    """Data structure for a sub-problem"""
    title: str
    description: str
    objective: str
    id: str

class SolverRequest(BaseModel):
    """Data structure for solver request"""
    traceId: Optional[str] = None
    subProblem: SubProblem
    modelConfig: Optional[Dict[str, Any]] = None
    metadata: Optional[Any] = None
    
    # RAG & History
    context: Optional[Dict] = None

class SolverResponse(BaseModel):
    """Data structure for solver response"""
    success: bool
    title: str
    content: str
    traceId: Optional[str] = None
    subProblemId: str
    
class Solver(LiteLLMWrapper):
    def __init__(
        self, 
        model: str = MODEL_NAME, 
        temperature: float = 0.7,
        language: str = "English"
    ):
        """
        Initialize the solver
        
        Args:
            model: Name of the LLM model to use
            temperature: Generation temperature
            language: Language for generation (default: English)
        """
        super().__init__(model=model, temperature=temperature)
        self.language = language

    def _get_system_prompt(self) -> str:
        """Get system prompt"""
        return f"""You are a professional technical problem-solving expert. You need to:
1. Carefully analyze the given sub-problem
2. Provide detailed solutions, including specific code examples and markdown math formulas
3. Organize your answer using Markdown format
4. All answers must be in {self.language}
"""

    def _get_user_prompt(self, subProblem: SubProblem, id: str = "", context: Optional[Dict] = None) -> str:
        """
        Generate user prompt with relevant context
        
        Args:
            subProblem: Sub-problem object
            id: Optional identifier string
            context: Optional context dictionary containing solution history
        """
        base_prompt = f"""Please solve the following sub-problem:

Title: {subProblem.title}
Description: {subProblem.description}
Objective: {subProblem.objective}"""

        if context:

            if context.get("originalProblem"):
                base_prompt += f"\n\nOriginal Problem: {context['originalProblem']}"
            if context.get("followUpQuestion"):
                base_prompt += f"\n\nFollow-up Question: {context['followUpQuestion']}"
            
            # Extract only the most recent parent node solution from the history
            if context.get("solutionHistory"):
                history = context["solutionHistory"]
                if history:
                    latest_solution = history[-1]  # Get the latest solution
                    base_prompt += "\n\nPrevious Solution Context:"
                    base_prompt += f"\nTitle: {latest_solution.get('title', '')}"
                    base_prompt += f"\nProblem: {latest_solution.get('problem', '')}"
                    # Only include the key part of the solution
                    solution_content = latest_solution.get('solution', '')
                    if len(solution_content) > 1000:  # If the content is too long, only take the first 1000 characters
                        solution_content = solution_content[:1000] + "..."
                    base_prompt += f"\nSolution Summary: {solution_content}"

        base_prompt += "\n\nPlease provide a solution that builds upon the previous context while addressing the current problem. Focus on practical implementation details and ensure your answer is in the specified language."
        
        return base_prompt

    async def solve_subproblem(self, request: SolverRequest) -> SolverResponse:
        """
        Solve a single sub-problem and return detailed solution
        
        Args:
            request: Request object containing sub-problem details
            
        Returns:
            Solver response containing the solution
        """
        try:
            if request.metadata and isinstance(request.metadata, dict):
                self.language = request.metadata.get("language", "English")
            
            system_prompt = self._get_system_prompt()
            user_prompt = self._get_user_prompt(
                request.subProblem, 
                request.traceId or "",
                request.context
            )
            
            solution = self.generate(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=2000,
                stop=None
            )
            
            return SolverResponse(
                success=True,
                title=request.subProblem.title,
                content=solution,
                traceId=request.traceId,
                subProblemId=request.subProblem.id
            )
            
        except Exception as e:
            error_msg = f"Failed to solve sub-problem: {str(e)}"
            self.logger.error(error_msg)
            return SolverResponse(
                success=False,
                title=request.subProblem.title,
                content=error_msg,
                traceId=request.traceId,
                subProblemId=request.subProblem.id
            )

    async def solve(self, request: SolverRequest) -> SolverResponse:
        """
        Main entry point to solve the problem
        
        Args:
            request: Solver request
            
        Returns:
            Solver response
        """
        return await self.solve_subproblem(request)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        solver = Solver()
        test_subproblem = SubProblem(
            title="Setting Up Next.js for CRUD Operations",
            description="This sub-problem involves configuring a Next.js application to handle CRUD operations, including setting up necessary packages and creating an API route for managing expense data.",
            objective="By establishing a foundation for CRUD operations in Next.js, this sub-problem enables the application to create, read, update, and delete expense records, fulfilling the original request for expense tracking.",
            id="12345"
        )
        
        request = SolverRequest(
            subProblem=test_subproblem,
            metadata={"language": "English"},
            traceId="test-trace-001"
        )
        
        response = await solver.solve(request)
        
        if response.success:
            print("Solution:")
            print(response.content)
        else:
            print("Error:", response.content)
    
    asyncio.run(main())