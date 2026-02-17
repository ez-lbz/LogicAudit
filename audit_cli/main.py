import click
import sys
from pathlib import Path
from audit_cli.config import load_config
from utils.logger import logger, setup_logger
from utils.formatter import print_section_header, print_progress, console
from rag.indexer import CodeIndexer
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings


@click.command()
@click.option('--project-path', '-p', required=True, help='Project path to audit')
@click.option('--config', '-c', default='config.json', help='Config file path')
@click.option('--reindex', is_flag=True, help='Reindex project code')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def main(project_path: str, config: str, reindex: bool, verbose: bool):
    
    if verbose:
        setup_logger(level=10)
    
    print_section_header("LogicAudit - Code Security Audit Tool")
    
    try:
        print_progress("Loading configuration...")
        cfg = load_config(config)
        
        project_path = Path(project_path).absolute()
        if not project_path.exists():
            logger.error(f"[-] Project path not found: {project_path}")
            sys.exit(1)
        
        print_progress(f"Project path: {project_path}")
        
        print_section_header("Step 1: Initialize LLM")
        import llama_index.llms.openai.utils as _oai_utils
        import llama_index.llms.openai.base as _oai_base
        _original_ctx = _oai_utils.openai_modelname_to_contextsize
        _original_is_chat = _oai_utils.is_chat_model
        def _patched_ctx(modelname: str) -> int:
            try:
                return _original_ctx(modelname)
            except ValueError:
                return 128000
        def _patched_is_chat(model: str) -> bool:
            return True
        def _patched_is_fc(model: str) -> bool:
            return True
        _oai_utils.openai_modelname_to_contextsize = _patched_ctx
        _oai_base.openai_modelname_to_contextsize = _patched_ctx
        _oai_utils.is_chat_model = _patched_is_chat
        _oai_base.is_chat_model = _patched_is_chat
        if hasattr(_oai_utils, 'is_function_calling_model'):
            _oai_utils.is_function_calling_model = _patched_is_fc
        if hasattr(_oai_base, 'is_function_calling_model'):
            _oai_base.is_function_calling_model = _patched_is_fc

        Settings.llm = OpenAI(
            api_key=cfg.llm.api_key,
            api_base=cfg.llm.base_url,
            model=cfg.llm.model,
            temperature=cfg.llm.temperature,
            max_tokens=cfg.llm.max_tokens,
            timeout=cfg.llm.timeout,
            disable_validation=True
        )
        
        Settings.embed_model = OpenAIEmbedding(
            api_key=cfg.embedding.api_key,
            api_base=cfg.embedding.base_url,
            model_name=cfg.embedding.model,
            disable_validation=True
        )
        
        logger.info(f"[+] LLM model: {cfg.llm.model}")
        logger.info(f"[+] Embedding model: {cfg.embedding.model}")
        
        print_section_header("Step 2: Code Indexing")
        indexer = CodeIndexer(
            db_path=cfg.rag.chroma_db_path, 
            collection_name=f"audit_{project_path.name}"
        )
        
        if reindex:
            print_progress("Reindexing project code...")
            indexer.clear_index()
            total_chunks = indexer.index_project(
                str(project_path),
                chunk_size=cfg.rag.chunk_size,
                chunk_overlap=cfg.rag.chunk_overlap
            )
            logger.info(f"[+] Indexing completed: {total_chunks} chunks")
        else:
            stats = indexer.get_stats()
            if stats['total_chunks'] == 0:
                print_progress("First run, indexing project code...")
                total_chunks = indexer.index_project(
                    str(project_path),
                    chunk_size=cfg.rag.chunk_size,
                    chunk_overlap=cfg.rag.chunk_overlap
                )
                logger.info(f"[+] Indexing completed: {total_chunks} chunks")
            else:
                logger.info(f"[*] Using existing index: {stats['total_chunks']} chunks")
        
        print_progress("Initializing RAG tools...")
        from tools.rag_tools import initialize_rag_tools
        initialize_rag_tools(indexer)
        
        print_section_header("Step 3: Execute Multi-Agent Audit")
        print_progress("Initializing audit workflow...")
        from workflow.audit_workflow import AuditAgentWorkflow
        
        workflow = AuditAgentWorkflow(llm=Settings.llm)
        
        print_progress("Starting AgentWorkflow audit...")
        report = workflow.run(project_path=str(project_path))

        
        print_section_header("Audit Report")
        
        from utils.formatter import format_vulnerability_report
        console.print(f"\n[bold cyan]Audit Report Summary[/bold cyan]\n")
        console.print(report.get('executive_summary', str(report)))

        
        console.print(f"\n[bold green][+] Audit completed![/bold green]")
        console.print(f"[dim]Report time: {report.get('report_time', 'N/A')}[/dim]")
        
        console.print("[bold green][+] Framework initialized[/bold green]")
        console.print(f"  - Project path: {project_path}")
        console.print(f"  - Code index: {cfg.rag.chroma_db_path}")
        console.print(f"  - LLM model: {cfg.llm.model}\n")
        
    except FileNotFoundError as e:
        logger.error(f"[-] File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[-] Execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
