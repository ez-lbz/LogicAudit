from typing import List, Dict, Optional
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from utils.logger import logger


class CodeRetriever:
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.retriever = None
        
        if indexer.index is not None:
            self.retriever = indexer.get_retriever(similarity_top_k=10)
        else:
            logger.warning("[!] Index not initialized, please index project first")
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 5, 
        file_filter: Optional[str] = None
    ) -> List[Dict]:
        if self.retriever is None:
            logger.error("[-] Retriever not initialized")
            return []
        
        try:
            query_bundle = QueryBundle(query_str=query)
            
            nodes = self.retriever.retrieve(query_bundle)
            
            results = []
            for node in nodes[:top_k]:
                if file_filter:
                    source_file = node.metadata.get('source_file', '')
                    if file_filter not in source_file:
                        continue
                
                results.append({
                    "content": node.text,
                    "metadata": node.metadata,
                    "score": node.score if hasattr(node, 'score') else 1.0,
                    "node_id": node.node_id
                })
            
            logger.info(f"[+] Semantic search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"[-] Semantic search failed: {e}")
            return []
    
    def search_by_file(self, file_path: str, query: str = None, top_k: int = 5) -> List[Dict]:
        if query:
            return self.semantic_search(query, top_k=top_k, file_filter=file_path)
        else:
            return self._get_file_chunks(file_path, top_k)
    
    def _get_file_chunks(self, file_path: str, limit: int = 5) -> List[Dict]:
        if self.indexer.index is None:
            return []
        
        try:
            docstore = self.indexer.index.docstore
            all_nodes = docstore.docs
            
            results = []
            for node_id, node in all_nodes.items():
                if node.metadata.get('source_file') == file_path:
                    results.append({
                        "content": node.text,
                        "metadata": node.metadata,
                        "score": 1.0,
                        "node_id": node_id
                    })
                    
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            logger.error(f"[-] Get file chunks failed: {e}")
            return []
    
    def get_related_code(self, file_path: str, context_size: int = 3) -> List[str]:
        results = self._get_file_chunks(file_path, limit=context_size)
        return [r["content"] for r in results]
    
    def query_with_context(self, query: str, top_k: int = 5) -> str:
        if self.indexer.index is None:
            logger.error("[-] Index not initialized")
            return ""
        
        try:
            query_engine = self.indexer.get_query_engine(similarity_top_k=top_k)
            response = query_engine.query(query)
            return str(response)
        except Exception as e:
            logger.error(f"[-] Query failed: {e}")
            return ""
    
    def get_retriever_stats(self) -> Dict:
        return {
            "initialized": self.retriever is not None,
            "indexer_stats": self.indexer.get_stats()
        }
