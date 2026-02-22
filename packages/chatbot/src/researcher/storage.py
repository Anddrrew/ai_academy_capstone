import hashlib
import time
from typing import TypedDict

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    Direction,
    OrderBy,
    PointIdsList,
    PointStruct,
    ScoredPoint,
)

from shared.services.base_storage import BaseStorage


class MemoryRecord(TypedDict):
    id: int
    text: str
    created_at: int | None


class MemoryStorage(BaseStorage):
    collection_name = "user_memory"

    @staticmethod
    def _make_id(user_id: str, text: str) -> int:
        digest = hashlib.sha256(f"{user_id}:{text}".encode()).digest()
        return int.from_bytes(digest[:8], "big")

    @staticmethod
    def _user_filter(user_id: str) -> Filter:
        return Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])

    def save(self, user_id: str, text: str, vector: list[float]) -> int:
        point_id = self._make_id(user_id, text)
        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"user_id": user_id, "text": text, "created_at": int(time.time())},
                )
            ],
        )
        return point_id

    def search(self, user_id: str, vector: list[float], k: int = 5) -> list[ScoredPoint]:
        result = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=self._user_filter(user_id),
            limit=k,
        )
        return result.points

    def list_all(self, user_id: str) -> list[MemoryRecord]:
        result = self._client.scroll(
            collection_name=self.collection_name,
            scroll_filter=self._user_filter(user_id),
            order_by=OrderBy(key="created_at", direction=Direction.DESC),
            limit=100,
        )
        points = result[0]
        return [
            MemoryRecord(
                id=int(p.id),
                text=str((p.payload or {}).get("text", "")),
                created_at=(p.payload or {}).get("created_at"),
            )
            for p in points
        ]

    def delete(self, point_id: int) -> None:
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=[point_id]),
        )


memory_storage = MemoryStorage()
