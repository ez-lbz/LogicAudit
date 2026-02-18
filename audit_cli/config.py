import json
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 180


class EmbeddingConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "text-embedding-3-small"


class RAGConfig(BaseModel):
    enabled: bool = True
    chroma_db_path: str = "./chroma_db"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5


class AuditConfig(BaseModel):
    languages: list[str] = Field(default_factory=lambda: ["java", "python", "go", "php"])
    max_workers: int = 4
    enable_parallel: bool = True


class Config(BaseModel):
    llm: LLMConfig
    embedding: EmbeddingConfig
    rag: RAGConfig
    audit: AuditConfig


def load_config(config_path: str) -> Config:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return Config(**data)
