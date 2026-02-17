import re
from typing import List, Dict, Optional
from pathlib import Path
from tools.file_ops import read_file, get_project_files, list_directory, get_file_info


def find_definition(symbol_name: str, project_path: str) -> List[Dict]:
    results = []
    files = get_project_files(project_path)
    
    patterns = [
        (re.compile(rf'(?:public|private|protected)?\s*(?:static|final|abstract)?\s*(?:class|interface|enum)\s+{re.escape(symbol_name)}\s*[<\{{\(\[]'), 'class'),
        (re.compile(rf'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+{re.escape(symbol_name)}\s*\('), 'method'),
        (re.compile(rf'^class\s+{re.escape(symbol_name)}\s*[\(:]', re.MULTILINE), 'class'),
        (re.compile(rf'^def\s+{re.escape(symbol_name)}\s*\(', re.MULTILINE), 'function'),
        (re.compile(rf'(?:function\s+{re.escape(symbol_name)}\s*\(|const\s+{re.escape(symbol_name)}\s*=\s*(?:async\s*)?\(|let\s+{re.escape(symbol_name)}\s*=\s*(?:async\s*)?\()'), 'function'),
        (re.compile(rf'^func\s+(?:\([^)]+\)\s*)?{re.escape(symbol_name)}\s*\(', re.MULTILINE), 'function'),
        (re.compile(rf'(?:public|private|protected)?\s*(?:static)?\s*function\s+{re.escape(symbol_name)}\s*\('), 'function'),
    ]
    
    for file_path in files:
        try:
            content = read_file(file_path)
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, def_type in patterns:
                    if pattern.search(line):
                        results.append({
                            "file": file_path,
                            "line": line_num,
                            "content": line.strip(),
                            "symbol": symbol_name,
                            "type": "definition",
                            "definition_type": def_type
                        })
                        break
        except:
            continue
    
    return results


def find_references(symbol_name: str, project_path: str, max_results: int = 100) -> List[Dict]:
    results = []
    files = get_project_files(project_path)
    
    pattern = re.compile(rf'\b{re.escape(symbol_name)}\b')
    
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
                        "symbol": symbol_name,
                        "type": "reference"
                    })
                    
                    if len(results) >= max_results:
                        return results
        except:
            continue
    
    return results


def extract_routes(project_path: str) -> List[Dict]:
    routes = []
    files = get_project_files(project_path)
    
    route_patterns = [
        (re.compile(r'@(?:Request|Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'), 'Spring'),
        (re.compile(r'@(?:Request|Get|Post|Put|Delete|Patch)Mapping\s*\(\s*path\s*=\s*["\']([^"\']+)["\']'), 'Spring'),
        (re.compile(r'@(?:app|bp|blueprint)\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?'), 'Flask'),
        (re.compile(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'), 'FastAPI'),
        (re.compile(r'(?:router|app)\.(get|post|put|delete|patch|use)\s*\(\s*["\']([^"\']+)["\']'), 'Express'),
        (re.compile(r'Route::(get|post|put|delete|patch|any)\s*\(\s*["\']([^"\']+)["\']'), 'Laravel'),
        (re.compile(r'(?:path|url|re_path)\s*\(\s*r?["\']([^"\']+)["\']'), 'Django'),
        (re.compile(r'(?:router|e)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"'), 'Go'),
    ]
    
    for file_path in files:
        if not any(keyword in file_path.lower() for keyword in ['controller', 'router', 'route', 'api', 'handler', 'view']):
            continue
            
        try:
            content = read_file(file_path)
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, framework in route_patterns:
                    matches = pattern.finditer(line)
                    for match in matches:
                        groups = match.groups()
                        if len(groups) >= 2:
                            method = groups[0]
                            route_path = groups[1] if len(groups) > 1 else groups[0]
                        else:
                            method = 'ANY'
                            route_path = groups[0]
                        
                        routes.append({
                            "file": file_path,
                            "line": line_num,
                            "route": route_path,
                            "method": method.upper() if method else 'ANY',
                            "framework": framework,
                            "content": line.strip()
                        })
        except:
            continue
    
    return routes


def discover_security_config_files(project_path: str) -> List[Dict]:
    config_files = []
    project_root = Path(project_path)
    
    security_file_patterns = [
        '*Security*.java', '*Security*.py', '*Security*.go', '*Security*.php',
        '*Auth*.java', '*Auth*.py', '*Auth*.go', '*Auth*.php',
        '*Filter*.java', '*Interceptor*.java', '*Middleware*.py', '*Middleware*.js',
        'security.py', 'auth.py', 'authentication.py', 'authorization.py',
        'SecurityConfig.java', 'WebSecurityConfig.java',
        'cors.py', 'cors.js', 'CorsConfig.java',
        'settings.py', 'config.py', 'application.yml', 'application.properties',
        'web.xml', 'web.config', 'httpd.conf', 'nginx.conf'
    ]
    
    security_dirs = [
        'config', 'security', 'auth', 'middleware', 'filter', 'interceptor',
        'conf', 'settings'
    ]
    
    for dir_name in security_dirs:
        config_dir = project_root / dir_name
        if config_dir.exists() and config_dir.is_dir():
            try:
                files = list_directory(str(config_dir), recursive=True)
                for file_path in files:
                    file_info = get_file_info(file_path)
                    if file_info['is_file']:
                        config_files.append({
                            "file": file_path,
                            "type": "security_config_dir",
                            "directory": dir_name,
                            "discovery_method": "directory_scan"
                        })
            except:
                continue
    
    for pattern in security_file_patterns:
        try:
            from tools.code_search import find_files_by_name
            matching_files = find_files_by_name(project_path, pattern)
            for file_path in matching_files:
                if not any(cf['file'] == file_path for cf in config_files):
                    config_files.append({
                        "file": file_path,
                        "type": "security_config_file",
                        "pattern": pattern,
                        "discovery_method": "filename_pattern"
                    })
        except:
            continue
    
    return config_files


def analyze_security_config_content(config_file_path: str) -> Dict:
    try:
        content = read_file(config_file_path)
        file_ext = Path(config_file_path).suffix.lower()
        
        config_info = {
            "file": config_file_path,
            "features": [],
            "potential_issues": []
        }
        
        cors_patterns = [
            (re.compile(r'allowedOrigins?\s*[=:]\s*["\']?\*["\']?'), "CORS allows all origins (unsafe)", "high"),
            (re.compile(r'Access-Control-Allow-Origin:\s*\*'), "CORS response header allows all origins", "high"),
            (re.compile(r'cors\s*\(\s*\)'), "CORS middleware with default config", "medium"),
        ]
        
        csrf_patterns = [
            (re.compile(r'csrf.*disable|csrf.*false|csrf\s*=\s*False', re.IGNORECASE), "CSRF protection disabled", "high"),
            (re.compile(r'@csrf_exempt', re.IGNORECASE), "CSRF exempt decorator", "medium"),
        ]
        
        auth_patterns = [
            (re.compile(r'permitAll\(\)'), "Endpoint without authentication", "info"),
            (re.compile(r'@PreAuthorize|@Secured|@RolesAllowed'), "Method-level permission control", "info"),
            (re.compile(r'authenticated\(\)'), "Authentication required", "info"),
        ]
        
        session_patterns = [
            (re.compile(r'session.*timeout|SESSION_COOKIE_AGE', re.IGNORECASE), "Session timeout config", "info"),
            (re.compile(r'sessionCreationPolicy.*STATELESS', re.IGNORECASE), "Stateless session (JWT etc.)", "info"),
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, desc, severity in cors_patterns:
                if pattern.search(line):
                    config_info['features'].append({
                        "type": "CORS",
                        "description": desc,
                        "line": line_num,
                        "content": line.strip(),
                        "severity": severity
                    })
            
            for pattern, desc, severity in csrf_patterns:
                if pattern.search(line):
                    config_info['features'].append({
                        "type": "CSRF",
                        "description": desc,
                        "line": line_num,
                        "content": line.strip(),
                        "severity": severity
                    })
            
            for pattern, desc, severity in auth_patterns:
                if pattern.search(line):
                    config_info['features'].append({
                        "type": "Authentication",
                        "description": desc,
                        "line": line_num,
                        "content": line.strip(),
                        "severity": severity
                    })
            
            for pattern, desc, severity in session_patterns:
                if pattern.search(line):
                    config_info['features'].append({
                        "type": "Session",
                        "description": desc,
                        "line": line_num,
                        "content": line.strip(),
                        "severity": severity
                    })
        
        return config_info
    except:
        return {"file": config_file_path, "features": [], "potential_issues": []}


def get_call_graph(function_name: str, project_path: str, max_depth: int = 2) -> Dict:
    definitions = find_definition(function_name, project_path)
    references = find_references(function_name, project_path, max_results=50)
    
    return {
        "function": function_name,
        "definitions": definitions,
        "references": references,
        "call_count": len(references)
    }
