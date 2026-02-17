from llama_index.core.agent.workflow import FunctionAgent
from prompts.report_gen import REPORT_GEN_PROMPT


def create_report_generator_agent(llm) -> FunctionAgent:
    return FunctionAgent(
        name="ReportGenerator",
        description="Consolidate vulnerabilities, deduplicate, assess severity, generate final audit report",
        system_prompt=f"""{REPORT_GEN_PROMPT}

## Tasks
1. Collect all vulnerability info from state:
   - traditional_vulnerabilities: traditional vulnerability list
   - business_vulnerabilities: business logic vulnerability list
   - project_analysis: project analysis results
2. Deduplicate: remove duplicates by type, file, line
3. Severity assessment: re-evaluate severity (CRITICAL/HIGH/MEDIUM/LOW)
4. Exploitability scoring: assess actual exploitability (1-5 score)
5. Generate final audit report (JSON format)
6. Write report to state.final_report

## State Fields
Read:
- `project_path`: project path
- `project_analysis`: project info
- `traditional_vulnerabilities`: traditional vulnerability list
- `business_vulnerabilities`: business logic vulnerability list

Write:
- `final_report`: {{
    "executive_summary": "executive summary including overview and top 3 risks",
    "statistics": {{
      "total_count": count,
      "by_severity": {{"CRITICAL": 0, "HIGH": 0, ...}},
      "by_type": {{...}},
      "high_exploitability_count": count
    }},
    "vulnerabilities": [
      {{
        "type": "type",
        "severity": "CRITICAL/HIGH/MEDIUM/LOW",
        "exploitability": 1-5,
        "file": "file",
        "line": line_number,
        "description": "description",
        "recommendation": "fix recommendation"
      }}
    ],
    "recommendations": ["general fix recommendations"],
    "report_time": "generation time"
  }}

## Important
- This is the final agent, no handoff needed
- Must generate complete JSON report
- Include all required fields
""",
        llm=llm,
        tools=[],
        can_handoff_to=[]
    )
