import json
import logging
import time
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import Runner
from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryPartDoneEvent,
)

from shared.config import config
from agent import rag_agent

logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = False


@router.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": config.server.display_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "rag",
            }
        ],
    }


def _make_sse_chunk(completion_id: str, model: str, delta: dict, finish_reason: str | None = None) -> str:
    chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(chunk)}\n\n"


async def _stream_chat(messages: list[dict], model: str):
    """Stream agent output as Chat Completions SSE with <think> tags for reasoning."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    yield _make_sse_chunk(completion_id, model, {"role": "assistant"})

    result = Runner.run_streamed(rag_agent, input=messages)

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            data = event.data
            if isinstance(data, ResponseReasoningSummaryPartAddedEvent):
                yield _make_sse_chunk(completion_id, model, {"content": "<think>\n"})
            elif isinstance(data, ResponseReasoningSummaryTextDeltaEvent):
                yield _make_sse_chunk(completion_id, model, {"content": data.delta})
            elif isinstance(data, ResponseReasoningSummaryPartDoneEvent):
                yield _make_sse_chunk(completion_id, model, {"content": "\n</think>\n\n"})
            elif isinstance(data, ResponseTextDeltaEvent):
                yield _make_sse_chunk(completion_id, model, {"content": data.delta})
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                raw = getattr(event.item, "raw_item", None)
                tool_name = getattr(raw, "name", "tool") if raw else "tool"
                yield _make_sse_chunk(completion_id, model, {
                    "content": f"🔧 *Calling {tool_name}...*\n\n"
                })

    yield _make_sse_chunk(completion_id, model, {}, finish_reason="stop")
    yield "data: [DONE]\n\n"


@router.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    messages = [m.model_dump() for m in request.messages]

    if request.stream:
        return StreamingResponse(
            _stream_chat(messages, request.model),
            media_type="text/event-stream",
        )

    # Non-streaming: run agent loop
    result = await Runner.run(rag_agent, input=messages)
    answer = result.final_output

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
    }
