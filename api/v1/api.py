from fastapi import APIRouter

router = APIRouter()
from litellm import completion



@router.post("/llm")

