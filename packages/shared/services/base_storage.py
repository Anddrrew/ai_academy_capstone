import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from shared.config import config


class BaseStorage:
    collection_name: str

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client = QdrantClient(host=config.qdrant.host, port=config.qdrant.port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self.collection_name):
            return
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=config.embedding.vector_size, distance=Distance.COSINE),
        )
        self.logger.info("Created collection '%s'", self.collection_name)
