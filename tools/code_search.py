import re
from pathlib import Path
from typing import List, Dict, Optional
import fnmatch
from tools.file_ops import get_project_files, read_file


def _filter_files(files: List[str], file_pattern: Optional[str]) -> List[str]:
    if not file_pattern:
        return files
        
    filtered_files = []
    patterns = [p.strip() for p in file_pattern.split(',')]
    
    for file_path in files:
        normalized_path = file_path.replace('\\', '/')
        filename = Path(file_path).name
        
        match = False
        for p in patterns:
            if p.replace('.', '').isalnum() and '/' not in p and '\\' not in p and '*' not in p:
                 if not p.startswith('.'):
                     p = f'*.{p}'
                 else:
                     p = f'*{p}'
            
            if fnmatch.fnmatch(normalized_path, p) or fnmatch.fnmatch(filename, p):
                match = True
                break
        
        if match:
            filtered_files.append(file_path)
            
    return filtered_files


def search_by_keyword(
    project_path: str, 
    keyword: str, 
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False
) -> List[Dict[str, any]]:
    results = []
    
    files = get_project_files(project_path)
    files = _filter_files(files, file_pattern)
    
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(keyword), flags)
    
    for file_path in files:
        try:
            content = read_file(file_path)
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    results.append({
                        "file": file_path,
                        "line": line_num,
                        "content": line.strip(),
                        "keyword": keyword
                    })
        except Exception:
            continue
    
    return results


def search_by_regex(
    project_path: str,
    regex_pattern: str,
    file_pattern: Optional[str] = None
) -> List[Dict[str, any]]:
    results = []
    
    files = get_project_files(project_path)
    files = _filter_files(files, file_pattern)
    
    pattern = re.compile(regex_pattern)
    
    for file_path in files:
        try:
            content = read_file(file_path)
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                matches = pattern.finditer(line)
                for match in matches:
                    results.append({
                        "file": file_path,
                        "line": line_num,
                        "content": line.strip(),
                        "match": match.group(),
                        "groups": match.groups()
                    })
        except Exception:
            continue
    
    return results


def find_files_by_name(project_path: str, name_pattern: str) -> List[str]:
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")
    
    exclude_dirs = {'.git', '.svn', 'node_modules', '__pycache__', 'venv', 'env', 'target', 'build', 'dist'}
    
    files = []
    for file_path in path.rglob(name_pattern):
        if not any(excluded in file_path.parts for excluded in exclude_dirs):
            files.append(str(file_path))
    
    return files
