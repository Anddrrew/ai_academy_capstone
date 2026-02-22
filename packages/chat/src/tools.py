import json
import logging

from agents import function_tool

from shared.services.embedder import embedder
from shared.services.file_manager import file_manager
from shared.services.knowledge_storage import KnowledgeStorage

logger = logging.getLogger(__name__)

_storage = KnowledgeStorage()


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
