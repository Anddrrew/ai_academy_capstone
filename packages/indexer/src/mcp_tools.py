import json

from mcp.server import Server
from mcp import types

from store import store, FileType, Priority, Status

mcp_server = Server("indexer")


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="index_github_repo",
            description="Add a GitHub repository URL to the indexing queue. The indexer will clone, analyze, and store it in the knowledge base.",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "GitHub repository URL (e.g. https://github.com/user/repo)",
                    }
                },
            },
        ),
        types.Tool(
            name="get_indexing_status",
            description="Get the current indexing queue status: what's processing, what's pending, what's done.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "index_github_repo":
        url = arguments["url"]
        added = store.add(FileType.GITHUB, url, Priority.HIGH)
        if added:
            return [types.TextContent(type="text", text=f"Queued {url} for indexing (high priority).")]
        else:
            return [types.TextContent(type="text", text=f"{url} is already in the indexing queue.")]

    elif name == "get_indexing_status":
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
