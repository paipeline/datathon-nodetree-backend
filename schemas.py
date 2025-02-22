# # type for node to frontend

# # type for edge to frontend

# # type for response to frontend

# # type for resquest from frontend


# # request for AI breaker from frontend

# # prompt for AI breaker 

# # response from AI breaker to frontend



# # prompt for solver agent from frontend

# # response from solver agent

# # litellm type with RAG integration from frontend




# from pydantic import BaseModel
# from typing import List, Optional, Any, Dict

# # ------------------------------
# # Node & Edge
# # ------------------------------
# class Node(BaseModel):
#     id: str
#     type: str
#     content: str
#     metadata: Optional[Any] = None
#     parentNodeId: Optional[str] = None
#     childrenNodeIds: Optional[List[str]] = None

# class Edge(BaseModel):
#     id: str
#     sourceId: str
#     targetId: str
#     label: Optional[str] = None
#     metadata: Optional[Any] = None

# # ------------------------------
# # 通用的前后端交互
# # ------------------------------
# class FrontendResponse(BaseModel):
#     success: bool
#     message: Optional[str] = None
#     data: Optional[Any] = None
#     traceId: Optional[str] = None

# class FrontendRequest(BaseModel):
#     userId: str
#     sessionId: Optional[str] = None
#     action: str
#     payload: Any
#     traceId: Optional[str] = None

# # ------------------------------
# # AI Breaker
# # ------------------------------
# class BreakerRequest(BaseModel):
#     traceId: Optional[str] = None
#     userId: str
#     sessionId: Optional[str] = None
#     originalInput: str
#     contextNodes: Optional[List[Node]] = None
#     metadata: Optional[Any] = None
#     followUpQuestion: Optional[str] = None

# class BreakerPrompt(BaseModel):
#     systemInstructions: str
#     userInput: str
#     context: Optional[Any] = None

# class BreakerResponse(BaseModel):
#     success: bool
#     # traceId: Optional[str] = None
#     followUpQuestion: Optional[str] = None  # user's follow-up question
#     parentId: str = None # if the node is initial node, the parentId is None, else it is the parent node id
#     data: Optional[Dict] = None

#     def to_dict(self) -> Dict:
#         """Convert the response to a dictionary"""
#         return self.model_dump()


# # ------------------------------
# # Solver Agent
# # ------------------------------
# class SolverAgentPrompt(BaseModel):
#     traceId: Optional[str] = None
#     userId: str
#     sessionId: Optional[str] = None
#     question: str
#     contextNodes: Optional[List[Node]] = None
#     knowledgeBaseRefs: Optional[List[str]] = None
#     modelConfig: Optional[Any] = None

# class SolverAgentResponse(BaseModel):
#     success: bool
#     answer: str
#     reasoning: Optional[str] = None
#     references: Optional[List[str]] = None
#     newNodes: Optional[List[Node]] = Nonee
#     newEdges: Optional[List[Edge]] = None
#     traceId: Optional[str] = None

# # ------------------------------
# # RAG
# # ------------------------------
# class RAGRequest(BaseModel):
#     traceId: Optional[str] = None
#     userId: str
#     sessionId: Optional[str] = None
#     query: str
#     topK: Optional[int] = None
#     retrieveOnly: Optional[bool] = None

# class RAGResponse(BaseModel):
#     success: bool
#     message: Optional[str] = None
#     retrievedDocs: Optional[List[Any]] = None
#     generatedAnswer: Optional[str] = None
#     traceId: Optional[str] = None
