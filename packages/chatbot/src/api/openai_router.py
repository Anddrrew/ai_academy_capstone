import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends
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
from shared.services.embedder import embedder
from judge.storage import evaluation_storage
from researcher import researcher_agent
from judge import judge_agent
from context import UserContext

logger = logging.getLogger(__name__)
router = APIRouter()


async def _evaluate_response(
    messages: list[dict], answer: str, tool_calls: list[dict[str, str]],
) -> None:
    """Fire-and-forget: run judge agent and log non-passing evaluations."""
    try:
        user_question = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        tools_section = ""
        for tc in tool_calls:
            tools_section += f"### {tc['name']}\n**Input:** {tc.get('input', 'N/A')}\n**Output:** {tc.get('output', 'N/A')}\n\n"

        judge_input = [
            {"role": "user", "content": (
                f"## User question\n{user_question}\n\n"
                f"## Assistant answer\n{answer}\n\n"
                f"## Tool calls and results\n{tools_section or 'No tools used.'}"
            )},
        ]
        result = await Runner.run(judge_agent, input=judge_input)
        evaluation = result.final_output

        logger.info("Judge score: %s", evaluation.score)
        if evaluation.score != "pass":
            vector = embedder.embed_query(user_question)
            evaluation_storage.save(
                user_input=user_question,
                agent_output=answer,
                tool_calls=[tc["name"] for tc in tool_calls],
                score=evaluation.score,
                feedback=evaluation.feedback,
                vector=vector,
            )
    except Exception as e:
        logger.warning("Judge evaluation failed: %s", e)


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


async def _stream_chat(messages: list[dict], model: str, user_ctx: UserContext):
    """Stream agent output as Chat Completions SSE with <think> tags for reasoning."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    yield _make_sse_chunk(completion_id, model, {"role": "assistant"})

    result = Runner.run_streamed(researcher_agent, input=messages, context=user_ctx)

    collected_answer: list[str] = []
    collected_tools: list[dict[str, str]] = []

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
                collected_answer.append(data.delta)
                yield _make_sse_chunk(completion_id, model, {"content": data.delta})
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                raw = getattr(event.item, "raw_item", None)
                tool_name = getattr(raw, "name", "tool") if raw else "tool"
                tool_input = getattr(raw, "arguments", "") if raw else ""
                collected_tools.append({"name": tool_name, "input": tool_input})
                yield _make_sse_chunk(completion_id, model, {
                    "content": f"🔧 *Calling {tool_name}...*\n\n"
                })
            elif event.item.type == "tool_call_output_item":
                output = getattr(event.item, "output", "")
                if collected_tools:
                    collected_tools[-1]["output"] = output

    yield _make_sse_chunk(completion_id, model, {}, finish_reason="stop")
    yield "data: [DONE]\n\n"

    # Fire judge in background (non-blocking)
    asyncio.create_task(
        _evaluate_response(messages, "".join(collected_answer), collected_tools)
    )


@router.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest, user_ctx: UserContext = Depends(UserContext)):
    messages = [m.model_dump() for m in request.messages]

    if request.stream:
        return StreamingResponse(
            _stream_chat(messages, request.model, user_ctx),
            media_type="text/event-stream",
        )

    # Non-streaming: run agent loop
    result = await Runner.run(researcher_agent, input=messages, context=user_ctx)
    answer = result.final_output

    # Extract tool calls from run result
    tool_calls: list[dict[str, str]] = []
    for item in result.new_items:
        if item.type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", "tool") if raw else "tool"
            arguments = getattr(raw, "arguments", "") if raw else ""
            tool_calls.append({"name": name, "input": arguments})
        elif item.type == "tool_call_output_item":
            output = getattr(item, "output", "")
            if tool_calls:
                tool_calls[-1]["output"] = output

    # Fire judge in background
    asyncio.create_task(_evaluate_response(messages, answer, tool_calls))

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
