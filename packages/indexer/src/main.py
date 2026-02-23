import logging

from fastapi import FastAPI, Request
from pydantic import BaseModel
from rich.logging import RichHandler
from starlette.responses import Response
from mcp.server.sse import SseServerTransport

from worker import worker
from store import Status
from mcp_tools import mcp_server

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = FastAPI(title="Indexer", description="Knowledge base indexing service")


# --- REST API ---

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


# --- MCP over SSE ---

sse_transport = SseServerTransport("/mcp/messages/")


@app.api_route("/mcp/sse", methods=["GET"])
async def handle_sse(request: Request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())
    return Response()


app.mount("/mcp/messages/", app=sse_transport.handle_post_message)
