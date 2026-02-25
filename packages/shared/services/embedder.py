import logging

import httpx

from shared.types.chunk import Chunk
from shared.config import config

SERVICE_ENDPOINT = config.embedding.public_url


class Embedder:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def embed_chunks(self, chunks: list[Chunk]) -> list[list[float]]:
        if not chunks:
            return []
        texts = [c.text for c in chunks]
        response = httpx.post(
            SERVICE_ENDPOINT,
            json={"inputs": texts},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_chunks([Chunk(text=text, source="", index=0)])[0]


embedder = Embedder()
