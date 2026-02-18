from typing import List
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from prompts.business_vuln import BUSINESS_VULN_KNOWLEDGE_BASE
from tools.state_tools import save_business_vulnerabilities, get_project_analysis, get_project_path


BUSINESS_VULN_TASK = """
## Your Task
1. Call get_project_analysis to read the project context (routes, tech stack, configs)
2. Call get_project_path to get the project root path
3. Use tools to examine authentication, authorization, and business workflows
   **CRITICAL: Execute ONE tool at a time.**
   - Do NOT combine tool names.
   - Do NOT use parallel calls if it causes errors.
   - Wait for each tool result before proceeding.
4. Focus on endpoints handling user data and permissions
5. Call save_business_vulnerabilities with your TOP 10 findings as JSON
6. Hand off to ReportGenerator

## Output Format (for save_business_vulnerabilities)

Pass a LIST of dictionaries to the tool. Each dictionary should follow this structure:

```json
{
  "type": "Mass Assignment",
  "severity": "HIGH",
  "file": "src/controller/UserController.java",
  "line": 45,
  "endpoint": "POST /api/user/update",
  "description": "Endpoint directly binds User entity...",
  "code_snippet": "@RequestBody User user",
  "poc": "POST /api/user/update ...",
  "recommendation": "Use DTO pattern...",
  "confidence": "high"
}
```

## CRITICAL: When you finish detection
After calling save_business_vulnerabilities, hand off to ReportGenerator.
"""

def create_business_vuln_agent(llm, tools: List) -> FunctionAgent:
    state_tools = [
        FunctionTool.from_defaults(
            async_fn=get_project_analysis,
            name="get_project_analysis",
            description="Get project analysis results from shared state (routes, tech stack, security configs)."
        ),
        FunctionTool.from_defaults(
            async_fn=get_project_path,
            name="get_project_path",
            description="Get the project path from shared state."
        ),
        FunctionTool.from_defaults(
            async_fn=save_business_vulnerabilities,
            name="save_business_vulnerabilities",
            description="Save found vulnerabilities to shared state. Args: vulnerabilities (List[Dict]) - List of vulnerability objects"
        ),
    ]

    return FunctionAgent(
        name="BusinessVulnAgent",
        description="Detect business logic vulnerabilities like IDOR, privilege escalation, mass assignment",
        system_prompt=f"{BUSINESS_VULN_KNOWLEDGE_BASE}\n\n{BUSINESS_VULN_TASK}",
        llm=llm,
        tools=tools + state_tools,
        can_handoff_to=["ReportGenerator"]
    )
