import logging
from pathlib import Path

from langchain_community.document_loaders import TextLoader

logger = logging.getLogger(__name__)


def load(file_path: Path) -> str:
    loader = TextLoader(str(file_path), autodetect_encoding=True)
    docs = loader.load()
    logger.info("Loaded %d text document(s) from %s", len(docs), file_path.name)
    return "\n".join(doc.page_content for doc in docs)
