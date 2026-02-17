from typing import List
from pathlib import Path
from llama_index.core.node_parser import CodeSplitter
from llama_index.core.schema import Document
from tools.file_ops import read_file


class CodeChunker:
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.language_map = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.php': 'php',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
        }
    
    def chunk_file(self, file_path: str) -> List[dict]:
        ext = Path(file_path).suffix.lower()
        content = read_file(file_path)
        
        language = self.language_map.get(ext, 'python')
        
        splitter = CodeSplitter(
            language=language,
            chunk_lines=40,
            chunk_lines_overlap=15,
            max_chars=self.chunk_size
        )
        
        document = Document(
            text=content,
            metadata={
                "file_path": file_path,
                "language": language
            }
        )
        
        nodes = splitter.get_nodes_from_documents([document])
        
        chunks = []
        for node in nodes:
            chunks.append({
                "content": node.get_content(),
                "metadata": {
                    "file_path": file_path,
                    "source_file": file_path,
                    "language": language,
                    "chunk_type": "code",
                    **node.metadata
                }
            })
        
        return chunks
