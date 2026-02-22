import logging
import time

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from shared.config import config

COLLECTION_NAME = "evaluation_log"
VECTOR_SIZE = config.embedding.vector_size


class EvaluationStorage:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client = QdrantClient(host=config.qdrant.host, port=config.qdrant.port)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(collection_name=COLLECTION_NAME):
            return
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        self.logger.info("Created collection '%s'", COLLECTION_NAME)

    def save(
        self,
        user_input: str,
        agent_output: str,
        tool_calls: list[str],
        score: str,
        feedback: str,
        vector: list[float],
    ) -> None:
        point_id = int(time.time() * 1000)  # ms timestamp as unique id
        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "user_input": user_input,
                        "agent_output": agent_output,
                        "tool_calls": tool_calls,
                        "score": score,
                        "feedback": feedback,
                        "created_at": int(time.time()),
                    },
                )
            ],
        )
        self.logger.info("Logged evaluation: score=%s, id=%d", score, point_id)


evaluation_storage = EvaluationStorage()
