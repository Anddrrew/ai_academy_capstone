import logging
import threading
import time

from config import config
from services.file_manager import file_manager
from indexer.loaders import SUPPORTED_EXTENSIONS
from indexer.store import IndexStore, FileType, Priority

logger = logging.getLogger(__name__)


class Observer:
    """Polls knowledge_base/ folder, adds new files to store."""

    def __init__(self, store: IndexStore) -> None:
        self._store = store

        threading.Thread(target=self._run, daemon=True).start()
        logger.info("Observer started (poll interval: %ds)", config.knowledge_base.poll_interval)

    def _run(self) -> None:
        while True:
            self.scan()
            time.sleep(config.knowledge_base.poll_interval)

    def scan(self) -> None:
        for file_path in file_manager.iter_files():
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            if self._store.is_known(file_path.name):
                continue

            self._store.add(FileType.FILE, file_path.name, Priority.DEFAULT)
