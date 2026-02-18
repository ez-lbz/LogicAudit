# LogicAudit - AI-Powered Code Security Audit Tool

A professional code security audit tool powered by LLM and Multi-Agent architecture. Automatically detects traditional vulnerabilities and business logic flaws using LlamaIndex `AgentWorkflow` and `FunctionAgent`.

## Features

- **Multi-Agent Architecture**: 3 specialized agents executing sequentially
  - **ProjectAnalyzer**: Analyzes project structure, tech stack, and routes.
  - **BusinessVulnAgent**: Identifies business logic flaws (IDOR, Mass Assignment, etc.).
  - **ReportGenerator**: Consolidates findings and generates structured reports.

- **Shared Context**: Robust state management using LlamaIndex `Context` store.
- **Resilient Workflow**: 
  - Automatic 3-attempt retry mechanism for handling transient LLM/API errors.
  - Strict "One Tool At A Time" enforcement to prevent hallucinated parallel calls.
- **RAG-Enhanced Analysis**: Optional code indexing and semantic search with ChromaDB via `QueryEngineTool`.
- **Structured Output**: Validated JSON reports using Pydantic models.

## Architecture

```
AgentWorkflow (Serial Execution with Retry Loop)
    |
    +-- ProjectAnalyzer
    |       | (Writes to Context: project_analysis)
    |       v
    |   BusinessVulnAgent
    |       | (Reads analysis, Writes to Context: business_vulnerabilities)
    |       v
    |   ReportGenerator
    |       | (Reads full context via get_audit_context)
    |       v
    |   Final JSON Report
```

### Core Components

- **workflows/**: `AgentWorkflow` setup with event streaming and retry logic.
- **agents/**: `FunctionAgent` definitions with specialized system prompts.
- **tools/**: 
  - `state_tools.py`: Async context access (get_audit_context, save_vulnerabilities).
  - `wrapper.py`: LlamaIndex tool wrappers (File operations, Code search, RAG).
  - `code_analysis.py`, `file_ops.py`, `code_search.py`: Core logic implementation.
- **rag/**: Code indexing and retrieval (CodeIndexer, CodeRetriever).
- **models/**: `response_schemas.py` for structured Pydantic outputs.

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key (or compatible API)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd logicaudit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API settings:
```bash
cp config.json.example config.json
# Edit config.json with your API credentials
```

## Usage

### Basic Audit

```bash
python -m audit_cli.main -p /path/to/project
```

### Advanced Options

```bash
# Reindex project code (force rebuild RAG index)
python -m audit_cli.main -p /path/to/project --reindex

# Disable RAG (faster, no indexing)
python -m audit_cli.main -p /path/to/project --no-rag

# Verbose logging (see tool calls and events)
python -m audit_cli.main -p /path/to/project -v
```

## Configuration

Edit `config.json`:

```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "temperature": 0.1
  },
  "embedding": {
    "api_key": "your-api-key",
    "model": "text-embedding-3-small"
  },
  "rag": {
    "chroma_db_path": "./chroma_db",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "top_k": 5
  },
  "audit": {
    "languages": ["java", "python", "go", "php"],
    "max_workers": 4,
    "enable_parallel": true
  }
}
```

## Project Structure

```
logicaudit/
├── agents/                    # FunctionAgent definitions
│   ├── project_analyzer.py    # Project analysis agent (Stage 1)
│   ├── business_vuln.py       # Vulnerability detection agent (Stage 2)
│   └── report_generator.py    # Report generation agent (Stage 3)
├── workflow/                  # Workflow orchestration
│   └── audit_workflow.py      # AgentWorkflow implementation with retries
├── tools/                     # Audit tools
│   ├── state_tools.py        # Context state management tools
│   ├── wrapper.py            # Tool creation and wrapping
│   ├── file_ops.py           # File system operations
│   ├── code_search.py        # Keyword/Regex search
│   └── code_analysis.py      # Static analysis helpers
├── rag/                       # RAG system
│   ├── indexer.py            # Code indexing with ChromaDB
│   └── retriever.py          # Semantic search implementation
├── prompts/                   # System prompts
├── models/                    # Data models
│   └── response_schemas.py   # Pydantic output schemas
├── utils/                     # Utilities
│   ├── logger.py             # Logging setup
│   └── formatter.py          # Output formatting
├── audit_cli/                 # CLI interface
│   └── main.py               # Entry point
└── config.json.example        # Configuration template
```

## Detection Capabilities

### Business Logic Vulnerabilities
- Horizontal Privilege Escalation (IDOR)
- Vertical Privilege Escalation
- Check Missing Function Level Access Control
- Mass Assignment / Entity Field Exposure
- Weak Validation / Null Bypass
- Race Conditions
- Logic Workflow Bypass

## Technology Stack

- **LlamaIndex 0.14+**: AgentWorkflow framework and RAG
- **ChromaDB**: Vector database for code indexing
- **Pydantic**: Data validation and structured outputs
- **Rich**: Terminal formatting and progress display

## Contributing

Contributions are welcome! Please ensure code follows project style guidelines and passes tests.

## License

MIT License

## Acknowledgments

Built with LlamaIndex AgentWorkflow.