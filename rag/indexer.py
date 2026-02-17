from typing import List, Optional
from pathlib import Path
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
import chromadb
from rag.chunker import CodeChunker
from tools.file_ops import get_project_files
from utils.logger import logger


class CodeIndexer:
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "code_audit"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.index = None
        
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        try:
            self.chroma_collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"[*] Loaded existing collection: {collection_name}")
            self._load_existing_index()
        except:
            self.chroma_collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Code audit index"}
            )
            logger.info(f"[+] Created new collection: {collection_name}")
            self.index = None
    
    def _load_existing_index(self):
        try:
            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context
            )
            logger.info("[+] Successfully loaded existing index")
        except Exception as e:
            logger.warning(f"[!]  Failed to load index: {e}")
            self.index = None
    
    def index_project(self, project_path: str, chunk_size: int = 512, chunk_overlap: int = 50) -> int:
        logger.info(f"[*] Starting to index project: {project_path}")
        
        chunker = CodeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        files = get_project_files(project_path)
        
        documents = []
        total_chunks = 0
        
        for idx, file_path in enumerate(files, 1):
            try:
                chunks = chunker.chunk_file(file_path)
                
                for chunk_idx, chunk in enumerate(chunks):
                    doc = Document(
                        text=chunk["content"],
                        metadata={
                            **chunk["metadata"],
                            "chunk_index": chunk_idx,
                            "source_file": file_path
                        },
                        id_=f"{file_path}_{chunk_idx}"
                    )
                    documents.append(doc)
                    total_chunks += 1
                
                if idx % 10 == 0:
                    logger.info(f"[*] Processed {idx}/{len(files)} files")
            except Exception as e:
                logger.warning(f"[!] Failed to process file {file_path}: {e}")
                continue
        
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        logger.info("[*] Building vector index...")
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        logger.info(f"[+] Project indexing completed, {total_chunks} code chunks")
        return total_chunks
    
    def add_documents(self, documents: List[Document]) -> None:
        if self.index is None:
            logger.error("[-] Index not initialized, call index_project first")
            return
        
        for doc in documents:
            self.index.insert(doc)
        
        logger.info(f"[+] Added {len(documents)} documents to index")
    
    def get_query_engine(self, similarity_top_k: int = 5, **kwargs):
        if self.index is None:
            logger.error("[-] Index not initialized")
            return None
        
        return self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            **kwargs
        )
    
    def get_retriever(self, similarity_top_k: int = 5, **kwargs):
        if self.index is None:
            logger.error("[-] Index not initialized")
            return None
        
        return self.index.as_retriever(
            similarity_top_k=similarity_top_k,
            **kwargs
        )
    
    def clear_index(self) -> None:
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            logger.info(f"[+] Deleted collection: {self.collection_name}")
        except:
            pass
        
        self.chroma_collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Code audit index"}
        )
        self.index = None
        logger.info(f"[+] Recreated collection: {self.collection_name}")
    
    def get_stats(self) -> dict:
        count = self.chroma_collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "db_path": self.db_path,
            "index_initialized": self.index is not None
        }
