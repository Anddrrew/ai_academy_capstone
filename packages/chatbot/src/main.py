import logging
from contextlib import asynccontextmanager

from agents import set_default_openai_key

from api.openai_router import router as openai_router
from api.router import router
from researcher.agent import indexer_mcp
from shared.services.file_manager import file_manager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.logging import RichHandler

from shared.config import config


logging.basicConfig(
    level=config.server.log_level,
    handlers=[RichHandler(rich_tracebacks=True)],
)

set_default_openai_key(config.openai.api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with indexer_mcp:
        yield


app = FastAPI(title="RAG Chat", description="RAG-based chatbot", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(openai_router)
app.mount("/files", StaticFiles(directory=file_manager.knowledge_base_dir), name="files")
