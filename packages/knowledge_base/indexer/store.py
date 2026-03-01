import logging
import sqlite3
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent.parent / "knowledge_base_store.db"


class FileType(str, Enum):
    FILE = "file"


class Status(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    FINISHED = "finished"
    FAILED = "failed"


class Priority(int, Enum):
    HIGH = 1   # user-triggered (uploads)
    DEFAULT = 2  # observer (files from knowledge_base/)


@dataclass
class IndexRecord:
    id: int
    file_type: FileType
    path: str
    priority: Priority
    status: Status
    created_at: str
    updated_at: str


class IndexStore:
    """SQLite-backed queue + registry. One table, dual purpose."""

    def __init__(self) -> None:
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._has_work = threading.Event()
        self._init_db()

        # signal if there's pending work
        if self._count_idle() > 0:
            self._has_work.set()

        logger.info("IndexStore ready (%d records, %d pending).", self._count_all(), self._count_idle())

    def _init_db(self) -> None:
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS index_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_type TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                priority INTEGER NOT NULL DEFAULT 2,
                status TEXT NOT NULL DEFAULT 'idle',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # reset any stuck PROCESSING items from previous run
        self._db.execute("UPDATE index_items SET status = 'idle' WHERE status = 'processing'")
        self._db.commit()

    def add(self, file_type: FileType, path: str, priority: Priority = Priority.DEFAULT) -> bool:
        """Add a new item. Returns False if path already exists."""
        with self._lock:
            try:
                self._db.execute(
                    "INSERT INTO index_items (file_type, path, priority) VALUES (?, ?, ?)",
                    (file_type.value, path, priority.value),
                )
                self._db.commit()
                self._has_work.set()
                logger.info("Added %s [%s] priority=%d", path, file_type.value, priority.value)
                return True
            except sqlite3.IntegrityError:
                return False

    def next(self, timeout: float = 1.0) -> IndexRecord | None:
        """Get next idle item (lowest priority number first, then oldest). Blocks until available."""
        self._has_work.wait(timeout=timeout)

        with self._lock:
            row = self._db.execute(
                "SELECT * FROM index_items WHERE status = 'idle' ORDER BY priority ASC, created_at ASC LIMIT 1"
            ).fetchone()

            if row is None:
                self._has_work.clear()
                return None

            self._db.execute(
                "UPDATE index_items SET status = 'processing', updated_at = datetime('now') WHERE id = ?",
                (row["id"],),
            )
            self._db.commit()
            return self._to_record(row)

    def finish(self, record_id: int) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE index_items SET status = 'finished', updated_at = datetime('now') WHERE id = ?",
                (record_id,),
            )
            self._db.commit()

    def fail(self, record_id: int) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE index_items SET status = 'failed', updated_at = datetime('now') WHERE id = ?",
                (record_id,),
            )
            self._db.commit()

    def is_known(self, path: str) -> bool:
        """Check if a path exists in the store (any status)."""
        row = self._db.execute("SELECT 1 FROM index_items WHERE path = ?", (path,)).fetchone()
        return row is not None

    def get_all(self) -> list[IndexRecord]:
        rows = self._db.execute("SELECT * FROM index_items ORDER BY created_at DESC").fetchall()
        return [self._to_record(r) for r in rows]

    def get_by_status(self, status: Status) -> list[IndexRecord]:
        rows = self._db.execute(
            "SELECT * FROM index_items WHERE status = ? ORDER BY priority ASC, created_at ASC",
            (status.value,),
        ).fetchall()
        return [self._to_record(r) for r in rows]

    def _count_idle(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM index_items WHERE status = 'idle'").fetchone()[0]

    def _count_all(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM index_items").fetchone()[0]

    def _to_record(self, row: sqlite3.Row) -> IndexRecord:
        return IndexRecord(
            id=row["id"],
            file_type=FileType(row["file_type"]),
            path=row["path"],
            priority=Priority(row["priority"]),
            status=Status(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


store = IndexStore()
