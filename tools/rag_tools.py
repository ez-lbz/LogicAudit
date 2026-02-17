from typing import List, Dict, Optional
from utils.logger import logger

_global_retriever = None


def initialize_rag_tools(indexer):
    global _global_retriever
    from rag.retriever import CodeRetriever
    _global_retriever = CodeRetriever(indexer)
    logger.info("[+] RAG tools initialized")


def semantic_search(query: str, top_k: int = 5, file_filter: Optional[str] = None) -> List[Dict]:
    if _global_retriever is None:
        logger.error("[-] RAG tools not initialized, call initialize_rag_tools first")
        return []
    
    try:
        results = _global_retriever.semantic_search(query, top_k=top_k, file_filter=file_filter)
        return results
    except Exception as e:
        logger.error(f"[-] RAG search failed: {e}")
        return []


def get_related_code(file_path: str, context_size: int = 3) -> List[str]:
    if _global_retriever is None:
        logger.error("[-] RAG tools not initialized")
        return []
    
    try:
        code_snippets = _global_retriever.get_related_code(file_path, context_size=context_size)
        return code_snippets
    except Exception as e:
        logger.error(f"[-] Get related code failed: {e}")
        return []


def search_in_file(file_path: str, query: str, top_k: int = 5) -> List[Dict]:
    if _global_retriever is None:
        logger.error("[-] RAG tools not initialized")
        return []
    
    try:
        results = _global_retriever.search_by_file(file_path, query=query, top_k=top_k)
        return results
    except Exception as e:
        logger.error(f"[-] Search in file failed: {e}")
        return []


def query_with_llm(query: str, top_k: int = 5) -> str:
    if _global_retriever is None:
        logger.error("[-] RAG tools not initialized")
        return ""
    
    try:
        response = _global_retriever.query_with_context(query, top_k=top_k)
        return response
    except Exception as e:
        logger.error(f"[-] LLM query failed: {e}")
        return ""
