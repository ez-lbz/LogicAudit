from typing import Dict, Any, Optional
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel
from utils.logger import logger


class LLMConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1" # Corrected from api_base
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4096 # Updated default
    timeout: int = 120 # Added timeout field


class AuditConfig(BaseModel):
    api_key: str
    api_base: Optional[str] = "https://api.openai.com/v1"
    model: str = "gpt-4"
    embed_model: str = "text-embedding-ada-002"
    temperature: float = 0.1
    max_tokens: int = 4000
    
    chunk_size: int = 512
    chunk_overlap: int = 50
    similarity_top_k: int = 5
    max_workers: int = 3


class LlamaIndexConfig:
    
    @staticmethod
    def initialize(config: Dict[str, Any]) -> None:
        logger.info("[*] Initializing LlamaIndex Settings...")
        
        audit_cfg = AuditConfig(**config)
        
        Settings.llm = OpenAI(
            api_key=audit_cfg.api_key,
            api_base=audit_cfg.api_base,
            model=audit_cfg.model,
            temperature=audit_cfg.temperature,
            max_tokens=audit_cfg.max_tokens
        )
        
        Settings.embed_model = OpenAIEmbedding(
            api_key=audit_cfg.api_key,
            api_base=audit_cfg.api_base,
            model=audit_cfg.embed_model
        )
        
        Settings.chunk_size = audit_cfg.chunk_size
        Settings.chunk_overlap = audit_cfg.chunk_overlap
        
        Settings.context_window = 4096
        Settings.num_output = audit_cfg.max_tokens
        
        logger.info(f"[+] Settings configured - LLM: {audit_cfg.model}, Embed: {audit_cfg.embed_model}")
    
    @staticmethod
    def get_llm():
        return Settings.llm
    
    @staticmethod
    def get_embed_model():
        return Settings.embed_model
