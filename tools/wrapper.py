from llama_index.core.tools import FunctionTool
from tools.file_ops import read_file, list_directory, get_file_info, get_project_files, get_file_tree
from tools.code_search import search_by_keyword, search_by_regex, find_files_by_name
from tools.code_analysis import (
    find_definition, find_references, extract_routes,
    discover_security_config_files, analyze_security_config_content,
    get_call_graph
)
from tools.rag_tools import semantic_search, get_related_code, search_in_file, query_with_llm
from utils.report_formatter import print_tool_call, print_tool_result
import functools
import os

_project_root = None


def set_project_root(path: str):
    global _project_root
    _project_root = os.path.abspath(path)


def resolve_path(path: str) -> str:
    if path is None:
        return path
    if os.path.isabs(path):
        return path
    if _project_root:
        return os.path.join(_project_root, path)
    return path


_PATH_PARAMS = {
    'file_path', 'dir_path', 'directory_path', 'project_path',
    'config_file_path',
}


def log_tool_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print_tool_call(func.__name__, kwargs if kwargs else dict(zip(func.__code__.co_varnames[:len(args)], args)))
        try:
            result = func(*args, **kwargs)
            result_preview = str(result)[:100] if result else "No result"
            print_tool_result(func.__name__, True, result_preview)
            return result
        except Exception as e:
            print_tool_result(func.__name__, False, str(e))
            raise
    return wrapper


def resolve_paths(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        resolved_kwargs = {}
        for k, v in kwargs.items():
            if k in _PATH_PARAMS and isinstance(v, str):
                resolved_kwargs[k] = resolve_path(v)
            else:
                resolved_kwargs[k] = v

        param_names = list(func.__code__.co_varnames[:func.__code__.co_argcount])
        resolved_args = list(args)
        for i, (name, val) in enumerate(zip(param_names, resolved_args)):
            if name in _PATH_PARAMS and isinstance(val, str):
                resolved_args[i] = resolve_path(val)

        return func(*resolved_args, **resolved_kwargs)
    return wrapper


def create_audit_tools():
    
    def wrap(func):
        return log_tool_call(resolve_paths(func))

    read_file_w = wrap(read_file)
    list_directory_w = wrap(list_directory)
    get_project_files_w = wrap(get_project_files)
    get_file_tree_w = wrap(get_file_tree)
    search_by_keyword_w = wrap(search_by_keyword)
    search_by_regex_w = wrap(search_by_regex)
    find_files_by_name_w = wrap(find_files_by_name)
    find_definition_w = wrap(find_definition)
    find_references_w = wrap(find_references)
    extract_routes_w = wrap(extract_routes)
    discover_security_config_files_w = wrap(discover_security_config_files)
    analyze_security_config_content_w = wrap(analyze_security_config_content)
    get_call_graph_w = wrap(get_call_graph)
    semantic_search_w = log_tool_call(semantic_search)          # no path param
    get_related_code_w = wrap(get_related_code)
    search_in_file_w = wrap(search_in_file)
    query_with_llm_w = log_tool_call(query_with_llm)            # no path param
    
    tools = [
        FunctionTool.from_defaults(
            fn=read_file_w,
            name="read_file",
            description="Read file content. Args: file_path (str) - file path"
        ),
        FunctionTool.from_defaults(
            fn=list_directory_w,
            name="list_directory",
            description="List files in directory. Args: directory_path (str), recursive (bool), pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=get_project_files_w,
            name="get_project_files",
            description="Get all code files in project. Args: project_path (str), extensions (list)"
        ),
        FunctionTool.from_defaults(
            fn=get_file_tree_w,
            name="get_file_tree",
            description="Get project directory structure tree. Args: project_path (str), max_depth (int)"
        ),
        
        FunctionTool.from_defaults(
            fn=search_by_keyword_w,
            name="search_by_keyword",
            description="Search keyword in project. Args: project_path (str), keyword (str), case_sensitive (bool), file_pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=search_by_regex_w,
            name="search_by_regex",
            description="Search code using regex. Args: project_path (str), pattern (str), case_insensitive (bool), file_pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=find_files_by_name_w,
            name="find_files_by_name",
            description="Find files by name pattern. Args: project_path (str), name_pattern (str), case_insensitive (bool)"
        ),
        
        FunctionTool.from_defaults(
            fn=find_definition_w,
            name="find_definition",
            description="Find symbol definition (function/class). Args: project_path (str), symbol_name (str), file_hint (str)"
        ),
        FunctionTool.from_defaults(
            fn=find_references_w,
            name="find_references",
            description="Find all references of symbol. Args: project_path (str), symbol_name (str), limit (int)"
        ),
        FunctionTool.from_defaults(
            fn=extract_routes_w,
            name="extract_routes",
            description="Extract HTTP routes/endpoints automatically from all supported frameworks. Args: project_path (str), framework (str). Supports Spring Boot, Flask, FastAPI, Django, Express.js, Laravel"
        ),
        
        FunctionTool.from_defaults(
            fn=discover_security_config_files_w,
            name="discover_security_config_files",
            description="Smart discovery of security config files by directory and file name patterns. Args: project_path (str)"
        ),
        FunctionTool.from_defaults(
            fn=analyze_security_config_content_w,
            name="analyze_security_config_content",
            description="Deep analysis of security config content (CORS, CSRF, Auth). Args: file_path (str), config_content (str)"
        ),
        FunctionTool.from_defaults(
            fn=get_call_graph_w,
            name="get_call_graph",
            description="Get function call graph. Args: project_path (str), function_name (str), max_depth (int)"
        ),
        
        FunctionTool.from_defaults(
            fn=semantic_search_w,
            name="semantic_search",
            description="RAG semantic search for code snippets. Args: query (str), top_k (int), file_filter (str)"
        ),
        FunctionTool.from_defaults(
            fn=get_related_code_w,
            name="get_related_code",
            description="Get related code context for file. Args: file_path (str), context_size (int)"
        ),
        FunctionTool.from_defaults(
            fn=search_in_file_w,
            name="search_in_file",
            description="RAG search in specified file. Args: file_path (str), query (str), top_k (int)"
        ),
        FunctionTool.from_defaults(
            fn=query_with_llm_w,
            name="query_with_llm",
            description="Intelligent code query using LLM (with RAG context). Args: query (str), top_k (int)"
        ),
    ]
    
    return tools
