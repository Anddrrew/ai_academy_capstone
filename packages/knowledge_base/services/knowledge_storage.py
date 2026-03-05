import hashlib
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, ScoredPoint, FilterSelector, Filter
from qdrant_client.models import Distance, VectorParams

from config import config
from services.chunker import Chunk

DEFAULT_SEARCH_LIMIT = config.qdrant.search_k


class KnowledgeStorage:
    collection_name = config.qdrant.collection

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client = QdrantClient(host=config.qdrant.host, port=config.qdrant.port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(self.collection_name):
            return
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=config.embedding.vector_size,
                distance=Distance.COSINE,
            ),
        )
        self.logger.info("Created collection '%s'", self.collection_name)

    def _make_point_id(self, source: str, index: int) -> int:
        digest = hashlib.sha256(f"{source}:{index}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def add_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        points = [
            PointStruct(
                id=self._make_point_id(c.source, c.index),
                vector=vectors[i],
                payload={"text": c.text, "source": c.source, "index": c.index},
            )
            for i, c in enumerate(chunks)
        ]
        self.upsert(points)

    def upsert(self, points: list[PointStruct]) -> None:
        if not points:
            return
        self._client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector: list[float], k: int = DEFAULT_SEARCH_LIMIT) -> list[ScoredPoint]:
        result = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=k,
        )
        return result.points

    def reset_storage(self) -> None:
        self._client.delete(collection_name=self.collection_name, points_selector=FilterSelector(filter=Filter()))
        self.logger.info("Knowledge storage reset: all points deleted from collection '%s'", self.collection_name)
