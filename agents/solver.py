from typing import Optional, List, Any
from pydantic import BaseModel
from schemas import Node, Edge
from agents.llm import LiteLLMWrapper

# ------------------------------
# Solver Agent
# ------------------------------
class SolverAgentPrompt(BaseModel):
    traceId: Optional[str] = None
    sessionId: Optional[str] = None
    question: str
    contextNodes: Optional[List[Node]] = None
    knowledgeBaseRefs: Optional[List[str]] = None
    modelConfig: Optional[Any] = None

class SolverAgentResponse(BaseModel):
    success: bool
    answer: str
    reasoning: Optional[str] = None
    references: Optional[List[str]] = None
    newNodes: Optional[List[Node]] = None
    newEdges: Optional[List[Edge]] = None
    traceId: Optional[str] = None
    
    
class Solver(LiteLLMWrapper):
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.7, language: str = "English"):
        super().__init__(model=model, temperature=temperature)
        self.language = language
        
    def _get_system_prompt(self, question: str, contextNodes: Optional[List[Node]] = None, knowledgeBaseRefs: Optional[List[str]] = None) -> str:
        return """You are an expert problem solver and subject matter specialist. Your role is to:
1. Analyze the given problem or subproblem carefully
2. Provide comprehensive, detailed solutions
3. Ensure solutions align with the overall context
4. Present solutions in a clear, step-by-step format
5. Include relevant code examples when necessary"""
    
    def _get_user_prompt(self, question: str, contextNodes: Optional[List[Node]] = None, knowledgeBaseRefs: Optional[List[str]] = None) -> str:
        context = ""
        if contextNodes:
            context = "\nContext Information:\n" + "\n".join([
                f"- {node.title}: {node.content}" for node in contextNodes
            ])
            
        refs = ""
        if knowledgeBaseRefs:
            refs = "\nRelevant References:\n" + "\n".join([
                f"- {ref}" for ref in knowledgeBaseRefs
            ])
            
        return f"""Problem to solve: {question}
{context}
{refs}

Please provide a detailed solution following these guidelines:
1. Carefully analyze the problem
2. Ensure the solution is consistent with the overall context
3. Provide step-by-step instructions
4. Include relevant code examples if needed
5. Response must be in {self.language}

Your solution should be thorough and practical."""

    async def solve(self, prompt: SolverAgentPrompt) -> SolverAgentResponse:
        system_prompt = self._get_system_prompt(
            prompt.question, 
            prompt.contextNodes,
            prompt.knowledgeBaseRefs
        )
        
        user_prompt = self._get_user_prompt(
            prompt.question,
            prompt.contextNodes,
            prompt.knowledgeBaseRefs
        )
        
        response = await self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_config=prompt.modelConfig
        )
        
        return SolverAgentResponse(
            success=True,
            answer=response,
            traceId=prompt.traceId,
            references=prompt.knowledgeBaseRefs
        )
        
        
if __name__ == "__main__":
    import asyncio
    
    async def main():
        solver = Solver()
        prompt = SolverAgentPrompt(question="What is the capital of France?")
        response = await solver.solve(prompt)
        print(response)
    
    asyncio.run(main())
