import json
import logging

from agents import RunContextWrapper, function_tool

from shared.services.embedder import embedder
from shared.services.file_manager import file_manager
from shared.services.knowledge_storage import KnowledgeStorage
from shared.services.memory_storage import memory_storage
from context import UserContext

logger = logging.getLogger(__name__)

_storage = KnowledgeStorage()


# --- Knowledge base ---

@function_tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant information. Use this when the user asks about topics that may be covered in the uploaded documents.

    Args:
        query: Search query to find relevant information
    """
    logger.info("Tool call: search_knowledge_base(%s)", query)
    vector = embedder.embed_query(query)
    results = _storage.search(vector)
    logger.debug("Search found %d chunks", len(results))
    chunks = []
    for r in results:
        source = r.payload["source"]
        url = file_manager.get_public_url(source)
        chunks.append({"source": source, "url": url, "text": r.payload["text"]})
    return json.dumps({"results": chunks})


@function_tool
def list_documents() -> str:
    """List all available documents in the knowledge base."""
    logger.info("Tool call: list_documents()")
    files = file_manager.list_files()
    return json.dumps({"documents": [f.name for f in files]})


# --- Memory ---

@function_tool
def search_memories(ctx: RunContextWrapper[UserContext], query: str) -> str:
    """Search user memories for relevant preferences, facts, or context from previous conversations.

    Args:
        query: What to search for in user memories
    """
    user_id = ctx.context.user_id
    logger.info("Tool call: search_memories(%s) [user=%s]", query, user_id)
    vector = embedder.embed_query(query)
    results = memory_storage.search(user_id, vector)
    memories = [{"id": r.id, "text": r.payload["text"]} for r in results]
    return json.dumps({"memories": memories})


@function_tool
def save_memory(ctx: RunContextWrapper[UserContext], content: str) -> str:
    """Save a new memory about the user — a preference, fact, or important context worth remembering across conversations.

    Args:
        content: The memory to save (e.g. "User prefers concise answers", "User's name is Andrew")
    """
    user_id = ctx.context.user_id
    logger.info("Tool call: save_memory(%s) [user=%s]", content, user_id)
    vector = embedder.embed_query(content)
    point_id = memory_storage.save(user_id, content, vector)
    return json.dumps({"status": "saved", "id": point_id})


@function_tool
def list_memories(ctx: RunContextWrapper[UserContext]) -> str:
    """List all stored user memories."""
    user_id = ctx.context.user_id
    logger.info("Tool call: list_memories() [user=%s]", user_id)
    memories = memory_storage.list_all(user_id)
    return json.dumps({"memories": memories})


@function_tool
def delete_memory(memory_id: int) -> str:
    """Delete an outdated or incorrect user memory.

    Args:
        memory_id: The ID of the memory to delete
    """
    logger.info("Tool call: delete_memory(%d)", memory_id)
    memory_storage.delete(memory_id)
    return json.dumps({"status": "deleted", "id": memory_id})
