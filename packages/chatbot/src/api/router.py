import logging

from fastapi import APIRouter
from pydantic import BaseModel

# from agent import agent

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# @router.post("/chat")
# def chat(request: ChatRequest) -> ChatResponse:
#     question = request.question
#     logger.debug("Question: %s", question)

#     result = agent.agent_run([{"role": "user", "content": question}])
#     answer = result["answer"]
#     logger.debug("Answer length: %d chars", len(answer))
#     return ChatResponse(answer=answer)


@router.get("/status")
def status():
    return {"status": "ok"}
