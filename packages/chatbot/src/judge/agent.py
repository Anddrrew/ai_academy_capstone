from agents import Agent

from judge.prompt import SYSTEM
from judge.models import EvaluationFeedback

judge_agent = Agent(
    name="Response Judge",
    instructions=SYSTEM,
    model="gpt-4o-mini",
    output_type=EvaluationFeedback,
)
