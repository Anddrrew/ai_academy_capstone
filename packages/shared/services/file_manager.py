import logging
from pathlib import Path
from typing import Iterator
from urllib.parse import quote

from shared.config import config


class FileManager:
    _instance: "FileManager | None" = None
    logger: logging.Logger
    _knowledge_base_dir: Path

    def __new__(cls) -> "FileManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger(cls.__name__)
            cls._instance._knowledge_base_dir = Path(__file__).parent.parent.parent.parent / "knowledge_base"
        return cls._instance

    @property
    def knowledge_base_dir(self) -> Path:
        """Get the knowledge base directory path."""
        return self._knowledge_base_dir
    
    def list_files(self) -> list[Path]:
        """List all files in the knowledge base directory."""
        if not self._knowledge_base_dir.exists():
            self.logger.warning(
                "Knowledge base directory does not exist: %s",
                self._knowledge_base_dir,
            )
            return []
        return list(self.iter_files())

    def iter_files(self) -> Iterator[Path]:
        if not self._knowledge_base_dir.exists():
            self.logger.warning(
                "Knowledge base directory does not exist: %s",
                self._knowledge_base_dir,
            )
            return iter([])  

        for path in self._knowledge_base_dir.iterdir():
            if path.is_file():
                yield path

    def save_file(self, filename: str, data: bytes) -> Path:
        """Save bytes to knowledge_base/{filename}."""
        self._knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        path = self._knowledge_base_dir / filename
        path.write_bytes(data)
        self.logger.info("Saved file: %s (%d bytes)", filename, len(data))
        return path

    def get_file_path(self, filename: str) -> Path:
        return self._knowledge_base_dir / filename

    def get_public_url(self, filename: str) -> str:
        encoded_filename = quote(filename)
        return f"{config.server.public_url}/files/{encoded_filename}"

    def get_file_extension(self, file_path: Path) -> str:
        """Get the lowercase file extension."""
        return file_path.suffix.lower()


file_manager = FileManager()
