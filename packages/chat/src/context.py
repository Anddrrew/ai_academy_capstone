from agent import agent
from shared.services.file_manager import file_manager
from shared.services.knowledge_storage import KnowledgeStorage
from shared.services.embedder import embedder
import logging


logger = logging.getLogger(__name__)



class Context:
    def __init__(self):
        self.storage = KnowledgeStorage()

    def get_chunks(self, question: str) -> list[str]:
        search_query = agent.extract_search_query(question)
        if not search_query:
            return []

        vector = embedder.embed_query(search_query)
        results = self.storage.search(vector)
        logger.debug("Found %d chunks: %s", len(results), [r.payload["source"] for r in results])
        return [
            f"[Source: [{r.payload['source']}]({file_manager.get_public_url(r.payload['source'])})]\n{r.payload['text']}"
            for r in results
        ]


context = Context()