from agents import Agent, ModelSettings, WebSearchTool
from agents.mcp import MCPServerSse
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

indexer_mcp = MCPServerSse(
    params={"url": config.indexer.mcp_url},
    name="Indexer",
    cache_tools_list=True,
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
    mcp_servers=[indexer_mcp],
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium", summary="auto"),
    ),
)
