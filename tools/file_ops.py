from pathlib import Path
from typing import List, Optional
import os


def read_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin-1') as f:
            return f.read()


def list_directory(dir_path: str, pattern: Optional[str] = None, recursive: bool = False) -> List[str]:
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")
    
    files = []
    if recursive:
        if pattern:
            files = [str(p) for p in path.rglob(pattern)]
        else:
            files = [str(p) for p in path.rglob('*') if p.is_file()]
    else:
        if pattern:
            files = [str(p) for p in path.glob(pattern)]
        else:
            files = [str(p) for p in path.glob('*') if p.is_file()]
    
    return files


def get_file_info(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = path.stat()
    return {
        "path": str(path.absolute()),
        "name": path.name,
        "size": stat.st_size,
        "extension": path.suffix,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "modified_time": stat.st_mtime
    }


def get_project_files(project_path: str, extensions: Optional[List[str]] = None, recursive: bool = True) -> List[str]:
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")
    
    if extensions is None:
        extensions = ['.java', '.py', '.go', '.php', '.js', '.ts']
    
    exclude_dirs = {'.git', '.svn', 'node_modules', '__pycache__', 'venv', 'env', 'target', 'build', 'dist', '.idea', '.vscode'}
    
    files = []
    iterator = path.rglob if recursive else path.glob
    
    for ext in extensions:
        pattern = f'*{ext}' if not ext.startswith('*') else ext
        
        for file_path in iterator(pattern):
            if not any(excluded in file_path.parts for excluded in exclude_dirs):
                files.append(str(file_path))
    
    return files


def get_file_tree(project_path: str, max_depth: int = 3) -> str:
    root = Path(project_path)
    if not root.exists():
        return f"Path not found: {project_path}"
    
    exclude_dirs = {'.git', '.svn', 'node_modules', '__pycache__', 'venv', 'env', 'target', 'build', 'dist', '.idea', '.vscode'}
    
    tree_str = []
    
    def _add_to_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
            
        try:
            items = sorted(list(path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return

        items = [i for i in items if i.name not in exclude_dirs]
        
        count = len(items)
        for i, item in enumerate(items):
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            
            tree_str.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                extension = "    " if is_last else "│   "
                _add_to_tree(item, prefix + extension, depth + 1)

    tree_str.append(root.name)
    _add_to_tree(root, "", 0)
    
    return "\n".join(tree_str)
