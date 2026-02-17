# LogicAudit - AI-Powered Code Security Audit Tool

A professional code security audit tool powered by LLM and Multi-Agent architecture. Automatically detects traditional vulnerabilities and business logic flaws using LlamaIndex AgentWorkflow.

## Features

- **Multi-Agent Architecture**: 3 specialized agents working collaboratively
  - ProjectAnalyzer: Analyzes project structure and tech stack
  - BusinessVulnAgent: Identifies business logic flaws (IDOR, Mass Assignment, etc.)
  - ReportGenerator: Consolidates findings and generates reports

- **RAG-Enhanced Analysis**: Code indexing and semantic search with ChromaDB
- **Multiple Language Support**: Java, Python, Go, PHP, JavaScript
- **Intelligent Detection**: LLM-driven vulnerability analysis with tool usage
- **Automated Workflow**: AgentWorkflow orchestration with handoff mechanism

## Architecture

```
AgentWorkflow (Serial Execution)
    |
    +-- ProjectAnalyzer
    |       |
    |       v
    |   BusinessVulnAgent
    |       |
    |       v
    |   ReportGenerator
```

### Core Components

- **agents/**: FunctionAgent definitions for each specialized agent
- **workflow/**: AgentWorkflow orchestration logic
- **tools/**: Audit tools (file operations, code search, analysis, RAG)
- **rag/**: Code indexing and retrieval (CodeIndexer, CodeRetriever)
- **prompts/**: Agent prompts and security knowledge base
- **models/**: Pydantic schemas for structured outputs

## Installation

### Prerequisites

- Python 3.8+
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
# Reindex project code
python -m audit_cli.main -p /path/to/project --reindex

# Verbose logging
python -m audit_cli.main -p /path/to/project -v

# Custom config
python -m audit_cli.main -p /path/to/project -c custom_config.json
```

## Configuration

Edit `config.json`:

```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
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
│   ├── project_analyzer.py    # Project analysis agent
│   ├── business_vuln.py       # Business logic vulnerability detection
│   └── report_generator.py    # Report generation agent
├── workflow/                  # AgentWorkflow orchestration
│   └── audit_workflow.py      # Main workflow logic
├── tools/                     # Audit tools
│   ├── file_ops.py           # File operations
│   ├── code_search.py        # Code search utilities
│   ├── code_analysis.py      # Code analysis (routes, configs)
│   ├── rag_tools.py          # RAG semantic search
│   └── wrapper.py            # LlamaIndex FunctionTool wrappers
├── rag/                       # RAG system
│   ├── indexer.py            # Code indexing with ChromaDB
│   ├── retriever.py          # Code retrieval
│   └── chunker.py            # Code-aware chunking
├── prompts/                   # Agent prompts
│   ├── project_analysis.py   # Project analysis prompts
│   ├── business_vuln.py      # Business logic prompts
│   └── report_gen.py         # Report generation prompts
├── models/                    # Data models
│   ├── config.py             # Configuration management
│   └── response_schemas.py   # Pydantic response models
├── utils/                     # Utilities
│   ├── logger.py             # Logging setup
│   └── formatter.py          # Output formatting
├── audit_cli/                 # CLI interface
│   ├── main.py               # Entry point
│   └── config.py             # Config loading
└── config.json.example        # Configuration template
```

## Detection Capabilities

### Business Logic Vulnerabilities
- Horizontal Privilege Escalation (IDOR)
- Vertical Privilege Escalation
- Mass Assignment
- Entity Field Exposure
- Null Bypass / Weak Validation
- Hidden Parameter Exploitation
- Race Conditions
- Authentication Bypass
- Workflow Bypass
- Rate Limiting Issues

## Technology Stack

- **LlamaIndex**: Agent framework and RAG
- **ChromaDB**: Vector database for code indexing
- **Pydantic**: Data validation and structured outputs
- **Rich**: Terminal formatting
- **Click**: CLI interface

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project follows:
- No docstrings or comments in code (for clarity)
- Standardized logging format: [+] [-] [*] [!] [>]
- Clean, minimal code style

## License

MIT License

## Contributing

Contributions are welcome! Please ensure:
- Code follows project style guidelines
- All tests pass
- Security vulnerabilities are properly documented

## Acknowledgments

Built with LlamaIndex AgentWorkflow and inspired by professional security audit practices.