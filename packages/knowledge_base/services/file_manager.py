import logging
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

from config import config


class FileManager:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._knowledge_base_dir = Path(
            __file__).parent.parent.parent.parent / "knowledge_base"
        self.logger.info(
            "Initialized FileManager with knowledge base directory: %s", self._knowledge_base_dir)

    @property
    def knowledge_base_dir(self) -> Path:
        """Get the knowledge base directory path."""
        return self._knowledge_base_dir

    def list_files(self) -> list[Path]:
        return list(self.iter_files())

    def normalize_filename(self, filename: str) -> str:
        normalized = Path(filename).name
        if not normalized or normalized in {".", ".."} or normalized != filename:
            raise ValueError(
                "Invalid filename. Provide a plain file name without path segments."
            )
        return normalized

    def iter_files(self) -> Iterator[Path]:
        if not self._knowledge_base_dir.exists():
            self.logger.warning(
                "Knowledge base directory does not exist: %s",
                self._knowledge_base_dir,
            )
            return

        for path in self._knowledge_base_dir.iterdir():
            if path.is_file():
                yield path

    def save_file(self, filename: str, data: bytes) -> Path:
        """Save bytes to knowledge_base/{filename}."""
        filename = self.normalize_filename(filename)
        self._knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        path = self._knowledge_base_dir / filename
        if path.exists():
            raise FileExistsError(f"File '{filename}' already exists in the knowledge base.")
        path.write_bytes(data)
        self.logger.info("Saved file: %s (%d bytes)", filename, len(data))
        return path

    def get_file_path(self, filename: str) -> Path:
        return self._knowledge_base_dir / self.normalize_filename(filename)

    def get_public_url(self, filename: str) -> str:
        filename = self.normalize_filename(filename)
        encoded_filename = quote(filename)
        return f"{config.knowledge_base.public_url.rstrip('/')}/files/{encoded_filename}"

    def get_file_extension(self, file_path: Path) -> str:
        """Get the lowercase file extension."""
        return file_path.suffix.lower()


file_manager = FileManager()
