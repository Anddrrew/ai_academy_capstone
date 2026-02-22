from agents import Agent, ModelSettings, WebSearchTool
from openai.types.shared import Reasoning

from shared.config import config
from researcher.prompt import SYSTEM
from researcher.tools import (
    search_knowledge_base,
    list_documents,
    search_memories,
    save_memory,
    list_memories,
    delete_memory,
)

researcher_agent = Agent(
    name="Researcher",
    instructions=SYSTEM,
    model=config.openai.chat_model,
    tools=[
        search_knowledge_base,
        list_documents,
        search_memories,
        save_memory,
        list_memories,
        delete_memory,
        WebSearchTool(),
    ],
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium", summary="auto"),
    ),
)
