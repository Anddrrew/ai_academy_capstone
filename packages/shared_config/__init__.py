from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_CONFIG_FILE = Path(__file__).resolve().parents[2] / ".env"

print(f"Loading config from {ENV_CONFIG_FILE}")


class QdrantConfig(BaseModel):
    search_k: int = 10
    host: str
    port: int
    collection: str


class EmbeddingConfig(BaseModel):
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    vector_size: int = 1024
    public_url: str


class KnowledgeBaseConfig(BaseModel):
    poll_interval: int = 10
    public_url: str = "http://localhost:3002"


class ChunkingConfig(BaseModel):
    size: int = 500
    overlap: int = 50


class WhisperConfig(BaseModel):
    model: str = "base"
    batch_size: int = 8


class Config(BaseSettings):
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    knowledge_base: KnowledgeBaseConfig = KnowledgeBaseConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    whisper: WhisperConfig = WhisperConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_CONFIG_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


config = Config()
