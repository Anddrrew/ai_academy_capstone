import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx
from mcp import types
from mcp.server import Server
from pydantic import BaseModel

from indexer.loaders import SUPPORTED_EXTENSIONS
from services.embedder import embedder
from services.file_manager import file_manager
from services.knowledge_storage import KnowledgeStorage
from indexer.store import FileType, Priority, Status, store

mcp_server = Server("knowledge_base")
knowledge_storage = KnowledgeStorage()

ALLOWED_EXTENSIONS = ", ".join(SUPPORTED_EXTENSIONS)
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 5
DOWNLOAD_TIMEOUT_SECONDS = 30.0


class UploadFileFromUrlArgs(BaseModel):
    filename: str
    file_url: str


class IndexingStatusArgs(BaseModel):
    pass


class UploadFileResult(BaseModel):
    message: str
    status: str


class IndexingStatusResult(BaseModel):
    processing: list[str]
    pending: list[str]
    finished: list[str]
    failed: list[str]


class SearchKnowledgeBaseArgs(BaseModel):
    query: str


class SearchKnowledgeBaseHit(BaseModel):
    source: str
    url: str
    text: str
    score: float | None = None


class SearchKnowledgeBaseResult(BaseModel):
    query: str
    results: list[SearchKnowledgeBaseHit]


def _file_ext(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _is_blocked_ip(raw_ip: str) -> bool:
    ip = ipaddress.ip_address(raw_ip)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_public_url(file_url: str) -> str:
    parsed = urlparse(file_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("URL must include a hostname.")

    try:
        addr_info = socket.getaddrinfo(
            parsed.hostname, parsed.port or 80, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve URL hostname: {exc}") from exc

    for info in addr_info:
        sockaddr = info[4]
        ip = sockaddr[0]
        if _is_blocked_ip(ip):
            raise ValueError(
                "URL points to a blocked/private network address.")

    return file_url


def _download_url_file(file_url: str) -> bytes:
    current_url = file_url
    for _ in range(MAX_REDIRECTS):
        _validate_public_url(current_url)
        with httpx.stream(
            "GET",
            current_url,
            follow_redirects=False,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:
            if 300 <= response.status_code < 400 and response.headers.get("location"):
                current_url = urljoin(
                    current_url, response.headers["location"])
                continue

            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > MAX_DOWNLOAD_BYTES:
                    raise ValueError(
                        f"File is too large. Max allowed size is {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB."
                    )
            return bytes(data)

    raise ValueError("Too many redirects while downloading file.")


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="upload_file_from_url",
            description=(
                f"Download and upload a file to the knowledge base by public URL. "
                f"Supported formats: {ALLOWED_EXTENSIONS}."
            ),
            inputSchema=UploadFileFromUrlArgs.model_json_schema(),
            outputSchema=UploadFileResult.model_json_schema(),
        ),
        types.Tool(
            name="get_indexing_status",
            description="Get the current indexing queue status: what's processing, what's pending, what's done.",
            inputSchema=IndexingStatusArgs.model_json_schema(),
            outputSchema=IndexingStatusResult.model_json_schema(),
        ),
        types.Tool(
            name="search_knowledge_base",
            description="Search indexed chunks from the knowledge base.",
            inputSchema=SearchKnowledgeBaseArgs.model_json_schema(),
            outputSchema=SearchKnowledgeBaseResult.model_json_schema(),
        ),
    ]


@mcp_server.call_tool()
async def call_tool(
    name: str,
    raw_args: dict,
) -> types.CallToolResult:

    if name == "upload_file_from_url":
        args = UploadFileFromUrlArgs.model_validate(raw_args)
        try:
            filename = file_manager.normalize_filename(args.filename)
            _validate_public_url(args.file_url)
        except ValueError as exc:
            message = str(exc)
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        ext = _file_ext(filename)
        if ext not in SUPPORTED_EXTENSIONS:
            message = f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        if file_manager.get_file_path(filename).exists():
            message = f"File '{filename}' already exists in the knowledge base."
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        try:
            data = _download_url_file(args.file_url)
        except (ValueError, httpx.HTTPError) as exc:
            message = f"Failed to download file: {exc}"
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        try:
            file_manager.save_file(filename, data)
        except FileExistsError as exc:
            message = str(exc)
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )
        store.add(FileType.FILE, filename, Priority.HIGH)
        message = f"Downloaded, saved, and queued '{filename}' for indexing."
        payload = UploadFileResult(message=message, status="queued")
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            structuredContent=payload.model_dump(),
        )

    elif name == "get_indexing_status":
        IndexingStatusArgs.model_validate(raw_args)
        idle = store.get_by_status(Status.IDLE)
        processing = store.get_by_status(Status.PROCESSING)
        finished = store.get_by_status(Status.FINISHED)
        failed = store.get_by_status(Status.FAILED)

        result = IndexingStatusResult(
            processing=[r.path for r in processing],
            pending=[r.path for r in idle],
            finished=[r.path for r in finished],
            failed=[r.path for r in failed],
        )
        return types.CallToolResult(
            content=[types.TextContent(
                type="text", text=result.model_dump_json())],
            structuredContent=result.model_dump(),
        )

    elif name == "search_knowledge_base":
        args = SearchKnowledgeBaseArgs.model_validate(raw_args)
        vector = embedder.embed_query(args.query)
        hits = knowledge_storage.search(vector)
        result = SearchKnowledgeBaseResult(
            query=args.query,
            results=[
                SearchKnowledgeBaseHit(
                    source=r.payload["source"],
                    url=file_manager.get_public_url(r.payload["source"]),
                    text=r.payload["text"],
                    score=r.score
                )
                for r in hits
            ],
        )

        return types.CallToolResult(
            content=[types.TextContent(
                type="text", text=result.model_dump_json())],
            structuredContent=result.model_dump(),
        )

    raise ValueError(f"Unknown tool: {name}")
