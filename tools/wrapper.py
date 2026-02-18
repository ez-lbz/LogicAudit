from llama_index.core.tools import FunctionTool, QueryEngineTool
from tools.file_ops import read_file, list_directory, get_file_info, get_project_files, get_file_tree
from tools.code_search import search_by_keyword, search_by_regex, find_files_by_name
from tools.code_analysis import (
    find_definition, find_references, extract_routes,
    discover_security_config_files, analyze_security_config_content,
    get_call_graph
)
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


def create_audit_tools(indexer=None, enable_rag: bool = True):
    def wrap(func):
        return log_tool_call(resolve_paths(func))

    tools = [
        FunctionTool.from_defaults(
            fn=wrap(read_file),
            name="read_file",
            description="Read file content. Args: file_path (str) - file path"
        ),
        FunctionTool.from_defaults(
            fn=wrap(list_directory),
            name="list_directory",
            description="List files in directory. Args: directory_path (str), recursive (bool), pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(get_project_files),
            name="get_project_files",
            description="Get all code files in project. Args: project_path (str), extensions (list)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(get_file_tree),
            name="get_file_tree",
            description="Get project directory structure tree. Args: project_path (str), max_depth (int)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(search_by_keyword),
            name="search_by_keyword",
            description="Search keyword in project. Args: project_path (str), keyword (str), case_sensitive (bool), file_pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(search_by_regex),
            name="search_by_regex",
            description="Search code using regex. Args: project_path (str), pattern (str), case_insensitive (bool), file_pattern (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(find_files_by_name),
            name="find_files_by_name",
            description="Find files by name pattern. Args: project_path (str), name_pattern (str), case_insensitive (bool)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(find_definition),
            name="find_definition",
            description="Find symbol definition (function/class). Args: project_path (str), symbol_name (str), file_hint (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(find_references),
            name="find_references",
            description="Find all references of symbol. Args: project_path (str), symbol_name (str), limit (int)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(extract_routes),
            name="extract_routes",
            description="Extract HTTP routes/endpoints automatically from all supported frameworks. Args: project_path (str), framework (str). Supports Spring Boot, Flask, FastAPI, Django, Express.js, Laravel"
        ),
        FunctionTool.from_defaults(
            fn=wrap(discover_security_config_files),
            name="discover_security_config_files",
            description="Smart discovery of security config files by directory and file name patterns. Args: project_path (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(analyze_security_config_content),
            name="analyze_security_config_content",
            description="Deep analysis of security config content (CORS, CSRF, Auth). Args: file_path (str), config_content (str)"
        ),
        FunctionTool.from_defaults(
            fn=wrap(get_call_graph),
            name="get_call_graph",
            description="Get function call graph. Args: project_path (str), function_name (str), max_depth (int)"
        ),
    ]

    if enable_rag and indexer is not None and indexer.index is not None:
        query_engine = indexer.get_query_engine(similarity_top_k=5)
        rag_tool = QueryEngineTool.from_defaults(
            query_engine=query_engine,
            name="rag_search",
            description="Semantic code search using RAG. Use this to find relevant code snippets by meaning. Args: query (str)"
        )
        tools.append(rag_tool)

    return tools
