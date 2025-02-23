from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from agents.llm import LiteLLMWrapper
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")

# ------------------------------
# AI Breaker
# ------------------------------
class BreakerRequest(BaseModel):
    traceId: Optional[str] = None
    originalInput: str
    # contextNodes: Optional[List[Node]] = None
    metadata: Optional[Any] = None
    followUpQuestion: Optional[str] = None  # user's follow-up question
    

class BreakerPrompt(BaseModel):
    systemInstructions: str
    userInput: str
    context: Optional[Any] = None

class BreakerResponse(BaseModel):
    success: bool
    traceId: Optional[str] = None
    followUpQuestion: Optional[str] = None  # user's follow-up question
    parentId: str = None # if the node is initial node, the parentId is None, else it is the parent node id
    data: Optional[Dict] = None
    context: Optional[Dict] = None
    def to_dict(self) -> Dict:
        """Convert the response to a dictionary"""
        return self.model_dump()
class subProblem(BaseModel):
    id: str
    title: str
    description: str
    objective: str

    def to_dict(self) -> Dict:
        """Convert the subproblem to a dictionary"""
        return self.model_dump()



class AIBreaker(LiteLLMWrapper):
    def __init__(
        self,
        model: str = MODEL_NAME,
        temperature: float = 0.7,
    ):
        super().__init__(model=model, temperature=temperature)
        self.language = "English" # default language for generation
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self, original_input: str = "", follow_up_question: Optional[str] = None) -> str:
        follow_up_str = follow_up_question if follow_up_question else "None"
        
        return f'''You are an expert in problem decomposition and system design. Your task is to first address the follow-up question (if any), then combine it with the main problem, breaking it down into logically coherent and well-defined subproblems.

Please strictly follow the following instructions:
1. If there is a follow-up question, first analyze and ensure it becomes the main focus of the problem decomposition.
2. Combine the follow-up question with the original problem, ensuring the problem decomposition prioritizes the requirements of the follow-up question.
3. Identify the primary objective that fulfills the user's complete request (including the follow-up question).
4. Break down the problem into smaller, manageable subproblems. For each subproblem, provide:
   - A clear and concise title (prioritizing the focus of the follow-up question).
   - A detailed description outlining its scope and requirements.
   - An explanation of how the subproblem achieves the objective.
   - The maximum disparity in the topics of the subproblems.
5. Your response must be entirely in {self.language} and strictly follow the JSON format below without any additional commentary.

Return your output in the exact JSON format:
{{
  "problem": "<string describing the main problem including follow-up question consideration>",
  "originalRequest": "{original_input}",
  "followUpQuestion": "{follow_up_str}",
  "mainObjective": "<string describing the primary goal prioritizing the follow-up question>",
  "subProblems": [
    {{
      "title": "<brief subproblem title or identifier prioritizing the follow-up question focus>",
      "description": "<detailed description of the subproblem>",
      "objective": "<how the subproblem helps solve the follow-up question and original request>"
    }}
  ]
}}'''

    async def break_down_problem(self, request: BreakerRequest) -> Dict:
        """
        Break down a problem into subproblems and return dictionary
        
        Args:
            request: BreakerRequest containing the problem details
        
        Returns:
            Dictionary containing the breakdown results
        """
        try:
            if request.metadata and isinstance(request.metadata, dict):
                self.language = request.metadata.get("language", "Chinese")
            
            follow_up_text = f"\nFollow-up question:\n{request.followUpQuestion}" if request.followUpQuestion else ""
            
            prompt = f"Original problem: {request.originalInput}{follow_up_text}"

            response = self.generate(
                prompt=prompt,
                system_message=self._get_system_prompt(
                    original_input=request.originalInput,
                    follow_up_question=request.followUpQuestion
                ),
                json_mode=True
            )

            if isinstance(response, str):
                import json
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON response from LLM")
            


            subproblems = []
            for subproblem_data in response.get("subProblems", []):
                subproblem_data["id"] = str(uuid4())
                subproblem = subProblem(**subproblem_data)
                #TODO check subproblem type
                subproblems.append(subproblem.to_dict())
            
            response["subProblems"] = subproblems
            
            return {
                "success": True,
                "followUpQuestion": request.followUpQuestion,
                "parentId": None,
                "data": response
            }

        except Exception as e:
            self.logger.error(f"Problem breakdown failed: {str(e)}")
            return {
                "success": False,
                "followUpQuestion": request.followUpQuestion,
                "parentId": None,
                "data": {"error": str(e)}
            }

    async def process_request(self, request: BreakerRequest) -> Dict:
        """
        Main entry point for processing breaker requests
        
        Args:
            request: BreakerRequest object containing all necessary information
            
        Returns:
            Dictionary with the results
        """
        return await self.break_down_problem(request)

# Usage example:
if __name__ == "__main__":
    import asyncio
    
    async def main():
        breaker = AIBreaker()
        request = BreakerRequest(
            originalInput="Create a web application that allows users to track their daily expenses and generate monthly reports.",
            followUpQuestion="how to perform CRUD operations in Next.js?",
        )
        response = await breaker.process_request(request)

        print(response)  # Simply print the dictionary response

    # Run the async main function
    asyncio.run(main())
    
    
    
    
