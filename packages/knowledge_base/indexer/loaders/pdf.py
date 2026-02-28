import logging
from pathlib import Path

from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser

logger = logging.getLogger(__name__)


def load(file_path: Path) -> str:
    loader = GenericLoader(
        blob_loader=FileSystemBlobLoader(
            path=str(file_path.parent),
            glob=file_path.name,
        ),
        blob_parser=PyPDFParser(),
    )
    docs = loader.load()
    logger.info("Loaded %d pages from %s", len(docs), file_path.name)
    return "\n".join(doc.page_content for doc in docs)
