import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field
from rich.logging import RichHandler
from shared_config import config

logging.basicConfig(
    level="INFO",
    handlers=[RichHandler(rich_tracebacks=True)],
)

MODEL_NAME = config.embedding.model_name

logger = logging.getLogger("embedder")
model: HuggingFaceEmbeddings | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading model %s...", MODEL_NAME)
    model = HuggingFaceEmbeddings(model_name=MODEL_NAME, show_progress=True)
    logger.info("Model loaded.")
    yield


app = FastAPI(title="Embedder", description="Text embedding service", lifespan=lifespan)


class EmbedRequest(BaseModel):
    inputs: list[str] = Field(examples=[["Hello world", "How are you?"]])


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


class StatusResponse(BaseModel):
    status: str = Field(examples=["ok"])


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(status="ok")


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest) -> EmbedResponse:
    return EmbedResponse(embeddings=model.embed_documents(request.inputs))
