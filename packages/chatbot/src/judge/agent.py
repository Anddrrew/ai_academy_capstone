from agents import Agent

from shared.config import config
from judge.prompt import SYSTEM
from judge.models import EvaluationFeedback

judge_agent = Agent(
    name="Response Judge",
    instructions=SYSTEM,
    model=config.openai.judge_model,
    output_type=EvaluationFeedback,
)
