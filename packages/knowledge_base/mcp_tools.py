import base64

from mcp import types
from mcp.server import Server
from pydantic import BaseModel

from indexer.loaders import SUPPORTED_EXTENSIONS
from services.embedder import embedder
from services.file_manager import file_manager
from services.knowledge_storage import DEFAULT_SEARCH_LIMIT, KnowledgeStorage
from indexer.store import FileType, Priority, Status, store

mcp_server = Server("knowledge_base")
knowledge_storage = KnowledgeStorage()

ALLOWED_EXTENSIONS = ", ".join(SUPPORTED_EXTENSIONS)


class UploadFileArgs(BaseModel):
    filename: str
    content: str


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
    k: int = DEFAULT_SEARCH_LIMIT


class SearchKnowledgeBaseHit(BaseModel):
    source: str
    url: str
    text: str
    score: float | None = None


class SearchKnowledgeBaseResult(BaseModel):
    query: str
    results: list[SearchKnowledgeBaseHit]


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="upload_file",
            description=f"Upload a file to the knowledge base for indexing. Supported formats: {ALLOWED_EXTENSIONS}. Content must be base64-encoded.",
            inputSchema=UploadFileArgs.model_json_schema(),
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

    if name == "upload_file":
        args = UploadFileArgs.model_validate(raw_args)
        ext = "." + args.filename.rsplit(".", 1)[-1].lower() if "." in args.filename else ""

        if ext not in SUPPORTED_EXTENSIONS:
            message = f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        if file_manager.get_file_path(args.filename).exists():
            message = f"File '{args.filename}' already exists in the knowledge base."
            payload = UploadFileResult(message=message, status="error")
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=message)],
                structuredContent=payload.model_dump(),
                isError=True,
            )

        data = base64.b64decode(args.content)
        file_manager.save_file(args.filename, data)
        store.add(FileType.FILE, args.filename, Priority.HIGH)
        message = f"Saved and queued '{args.filename}' for indexing."
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
            content=[types.TextContent(type="text", text=result.model_dump_json())],
            structuredContent=result.model_dump(),
        )

    elif name == "search_knowledge_base":
        args = SearchKnowledgeBaseArgs.model_validate(raw_args)
        vector = embedder.embed_query(args.query)
        hits = knowledge_storage.search(vector, k=args.k)
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
            content=[types.TextContent(type="text", text=result.model_dump_json())],
            structuredContent=result.model_dump(),
        )

    raise ValueError(f"Unknown tool: {name}")
