from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from prompts.report_gen import REPORT_GEN_PROMPT
from tools.state_tools import get_audit_context


def create_report_generator_agent(llm) -> FunctionAgent:
    state_tools = [
        FunctionTool.from_defaults(
            async_fn=get_audit_context,
            name="get_audit_context",
            description="Get ALL audit context (project info + found vulnerabilities) from shared state."
        ),
    ]

    return FunctionAgent(
        name="ReportGenerator",
        description="Consolidate vulnerabilities, deduplicate, assess severity, generate final audit report",
        system_prompt=f"""{REPORT_GEN_PROMPT}

## Tasks
1. Call `get_audit_context` to retrieve both project analysis and all found vulnerabilities.
2. Deduplicate: remove duplicates by type, file, line
3. Severity assessment: re-evaluate severity (CRITICAL/HIGH/MEDIUM/LOW)
4. Exploitability scoring: assess actual exploitability (1-5 score)
5. Output the final audit report as JSON

## Output Format
Output ONLY valid JSON:
```json
{{
  "summary": "Executive summary...",
  "statistics": {{
    "total_count": 0,
    "by_severity": {{"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}},
    "by_type": {{}},
    "high_exploitability_count": 0
  }},
  "vulnerabilities": [
    {{
      "type": "IDOR",
      "severity": "HIGH",
      "exploitability": 4,
      "file": "path/to/file",
      "line": 123,
      "description": "...",
      "recommendation": "..."
    }}
  ],
  "recommendations": ["..."],
  "report_time": "2024-01-01T00:00:00"
}}
```

## Important
- This is the final agent, no handoff needed
- Must generate complete JSON report
- Include all required fields
""",
        llm=llm,
        tools=state_tools,
        can_handoff_to=[]
    )
