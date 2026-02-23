import logging

from fastapi import FastAPI
from pydantic import BaseModel
from rich.logging import RichHandler

from worker import worker
from store import Status

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = FastAPI(title="Indexer", description="Knowledge base indexing service")


class StatusResponse(BaseModel):
    status: str
    current_item: str | None = None
    queue_size: int = 0
    indexed_sources: list[str] = []


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    idle = worker.store.get_by_status(Status.IDLE)
    finished = worker.store.get_by_status(Status.FINISHED)
    return StatusResponse(
        status="processing" if worker.current_item else "idle",
        current_item=worker.current_item,
        queue_size=len(idle),
        indexed_sources=[r.path for r in finished],
    )
