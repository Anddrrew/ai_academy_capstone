from typing import Literal

from pydantic import BaseModel


class EvaluationFeedback(BaseModel):
    score: Literal["pass", "needs_improvement", "fail"]
    feedback: str
