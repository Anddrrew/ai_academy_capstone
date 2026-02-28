from dataclasses import dataclass
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter


from config import config


@dataclass
class Chunk:
    text: str
    source: str
    index: int


class Chunker:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunking.size,
            chunk_overlap=config.chunking.overlap,
        )

    def split(self, text: str, source: str) -> list[Chunk]:
        pieces = self._splitter.split_text(text)
        chunks = [Chunk(text=piece, source=source, index=i)
                  for i, piece in enumerate(pieces)]

        self.logger.info("Split '%s' into %d chunks", source, len(chunks))
        return chunks


chunker = Chunker()
