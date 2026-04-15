from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/agentdb",
        env="DATABASE_URL",
    )

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL")

    # Voice
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    voice_mode: str = Field(default="push_to_talk", env="VOICE_MODE")

    # RAG
    docs_dir: Path = Field(default=Path("./docs"), env="DOCS_DIR")
    chroma_persist_dir: Path = Field(default=Path("./chroma_db"), env="CHROMA_PERSIST_DIR")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, env="CHUNK_OVERLAP")

    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
