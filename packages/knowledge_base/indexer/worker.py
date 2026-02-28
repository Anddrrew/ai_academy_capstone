import logging
import threading


from indexer.loaders import load
from indexer.observer import Observer
from services.chunker import chunker
from services.embedder import embedder
from services.file_manager import file_manager
from services.knowledge_storage import KnowledgeStorage
from indexer.store import store, IndexRecord


class Worker:
    """Pulls items from store and indexes them."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.store = store
        self.current_item: str | None = None

        self.observer = Observer(store)
        self._storage = KnowledgeStorage()

        threading.Thread(target=self._run, daemon=True).start()
        self.logger.info("Worker started.")

    def _run(self) -> None:
        while True:
            record = self.store.next(timeout=1.0)
            if record is None:
                self.current_item = None
                continue

            self.current_item = record.path

            try:
                self._process_file(record)
                self.store.finish(record.id)
            except Exception as e:
                self.logger.exception("Failed to index %s: %s", record.path, e)
                self.store.fail(record.id)

            self.current_item = None

    def _process_file(self, record: IndexRecord) -> None:
        file_path = file_manager.get_file_path(record.path)

        self.logger.info("Processing %s", file_path.name)
        text = load(file_path)
        self.logger.info("Extracted %d characters from %s",
                         len(text), file_path.name)

        chunks = chunker.split(text, source=file_path.name)
        vectors = embedder.embed_chunks(chunks)
        self._storage.add_chunks(chunks, vectors)
        self.logger.info("Indexed %s (%d chunks)", file_path.name, len(chunks))


worker = Worker()
