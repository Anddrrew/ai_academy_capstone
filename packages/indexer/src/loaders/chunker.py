import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.types.Chunk import Chunk
from shared.config import config


class Chunker:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunking.size,
            chunk_overlap=config.chunking.overlap,
        )

    def split(self, text: str, source: str) -> list[Chunk]:
        pieces = self._splitter.split_text(text)
        chunks = [Chunk(text=piece, source=source, index=i) for i, piece in enumerate(pieces)]

        self.logger.info("Split '%s' into %d chunks", source, len(chunks))
        return chunks


chunker = Chunker()
