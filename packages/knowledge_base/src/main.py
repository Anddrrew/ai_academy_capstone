import logging
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from rich.logging import RichHandler
from starlette.responses import FileResponse, PlainTextResponse, Response
from mcp.server.sse import SseServerTransport

from indexer.worker import worker
from indexer.store import Status
from mcp_tools import mcp_server
from services.file_manager import file_manager

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = FastAPI(title="Knowledge Base", description="Knowledge base indexing service")


# --- REST API ---

class StatusResponse(BaseModel):
    status: str
    current_item: str | None = None
    queue_size: int = 0
    indexed_sources: list[str] = []


class ReindexResponse(BaseModel):
    message: str


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


@app.get("/files", response_class=PlainTextResponse)
def files_catalog() -> PlainTextResponse:
    files = sorted(file_manager.list_files(), key=lambda path: path.name.lower())
    if not files:
        return PlainTextResponse("No files uploaded yet.\n")
    links = [f"/files/{quote(path.name)}" for path in files]
    return PlainTextResponse("\n".join(links) + "\n")


@app.post("/reindex", response_model=ReindexResponse)
def reindex() -> ReindexResponse:
    worker.force_reindex()
    return ReindexResponse(
        message="Reindex forced and restarted.",
    )


@app.get("/files/{filename:path}")
def serve_file(filename: str) -> FileResponse:
    root = file_manager.knowledge_base_dir.resolve()
    requested_path = (root / filename).resolve()

    if root not in requested_path.parents and requested_path != root:
        raise HTTPException(status_code=404, detail="File not found")

    if not requested_path.exists() or not requested_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=requested_path, filename=requested_path.name)


# --- MCP over SSE ---

sse_transport = SseServerTransport("/mcp/messages/")


@app.api_route("/mcp/sse", methods=["GET"])
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())
    return Response()


app.mount("/mcp/messages/", app=sse_transport.handle_post_message)
