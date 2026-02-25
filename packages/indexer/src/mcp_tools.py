import base64
import json

from pydantic import BaseModel
from mcp.server import Server
from mcp import types

from store import store, FileType, Priority, Status
from shared.services.file_manager import file_manager
from loaders import SUPPORTED_EXTENSIONS

mcp_server = Server("indexer")

ALLOWED_EXTENSIONS = ", ".join(SUPPORTED_EXTENSIONS)


class UploadFileArgs(BaseModel):
    filename: str
    content: str


class IndexingStatusArgs(BaseModel):
    pass



@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="upload_file",
            description=f"Upload a file to the knowledge base for indexing. Supported formats: {ALLOWED_EXTENSIONS}. Content must be base64-encoded.",
            inputSchema=UploadFileArgs.model_json_schema(),
        ),
        types.Tool(
            name="get_indexing_status",
            description="Get the current indexing queue status: what's processing, what's pending, what's done.",
            inputSchema=IndexingStatusArgs.model_json_schema(),
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, args: UploadFileArgs | IndexingStatusArgs) -> list[types.TextContent]:
    if name == "upload_file" and isinstance(args, UploadFileArgs):
        ext = "." + args.filename.rsplit(".", 1)[-1].lower() if "." in args.filename else ""

        if ext not in SUPPORTED_EXTENSIONS:
            return [types.TextContent(
                type="text",
                text=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
            )]

        if file_manager.get_file_path(args.filename).exists():
            return [types.TextContent(
                type="text",
                text=f"File '{args.filename}' already exists in the knowledge base.",
            )]

        data = base64.b64decode(args.content)
        file_manager.save_file(args.filename, data)
        store.add(FileType.FILE, args.filename, Priority.HIGH)
        return [types.TextContent(type="text", text=f"Saved and queued '{args.filename}' for indexing.")]

    elif name == "get_indexing_status" and isinstance(args, IndexingStatusArgs):
        idle = store.get_by_status(Status.IDLE)
        processing = store.get_by_status(Status.PROCESSING)
        finished = store.get_by_status(Status.FINISHED)
        failed = store.get_by_status(Status.FAILED)

        result = {
            "processing": [r.path for r in processing],
            "pending": [r.path for r in idle],
            "finished": [r.path for r in finished],
            "failed": [r.path for r in failed],
        }
        return [types.TextContent(type="text", text=json.dumps(result))]

    raise ValueError(f"Unknown tool: {name}")
