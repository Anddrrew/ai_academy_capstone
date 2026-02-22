from agents import Agent, ModelSettings, WebSearchTool, set_default_openai_key
from openai.types.shared import Reasoning

from shared.config import config
from tools import (
    search_knowledge_base,
    list_documents,
    search_memories,
    save_memory,
    list_memories,
    delete_memory,
)
import prompts

set_default_openai_key(config.openai.api_key)

rag_agent = Agent(
    name="RAG Assistant",
    instructions=prompts.system(),
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
