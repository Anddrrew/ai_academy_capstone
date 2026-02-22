from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_CONFIG_FILE = Path(__file__).parent.parent.parent / ".env"


class QdrantConfig(BaseModel):
    search_k: int = 10
    host: str
    port: int
    collection: str


class EmbeddingConfig(BaseModel):
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    vector_size: int = 1024
    public_url: str


class IndexerConfig(BaseModel):
    start_on_startup: bool = True


class ChunkingConfig(BaseModel):
    size: int = 500
    overlap: int = 50


class WhisperConfig(BaseModel):
    model: str = "base"
    batch_size: int = 8


class OpenAIConfig(BaseModel):
    chat_model: str = "gpt-5.2"
    api_key: str


class ServerConfig(BaseModel):
    display_name: str = "RAG Assistant"
    log_level: str = "INFO"
    public_url: str


class Config(BaseSettings):
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    indexer: IndexerConfig = IndexerConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    whisper: WhisperConfig = WhisperConfig()
    openai: OpenAIConfig
    server: ServerConfig

    model_config = SettingsConfigDict(env_file=ENV_CONFIG_FILE, env_file_encoding="utf-8", env_nested_delimiter="__")


config = Config()
