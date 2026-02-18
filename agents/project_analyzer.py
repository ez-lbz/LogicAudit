from typing import List
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool, AsyncBaseTool
from prompts.project_analysis import PROJECT_ANALYSIS_KNOWLEDGE_BASE
from tools.state_tools import save_project_analysis, get_project_path


PROJECT_ANALYSIS_TASK = """
## Your Task
1. Call get_project_path to get the project path
2. EXPLORE THE PROJECT STEP-BY-STEP (Sequential Only):
   a. Call get_file_tree -> WAIT for result
   b. Call get_project_files -> WAIT for result
   c. Call extract_routes -> WAIT for result
   d. Call discover_security_config_files -> WAIT for result
   
   **CRITICAL RULE: ONE TOOL AT A TIME**
   - Do NOT try to call multiple tools in parallel.
   - Do NOT combine tool names (e.g. "extract_routesdiscover_...").
   - Do NOT combine arguments.
   - Execute strictly sequentially.

3. Identify tech stack, routes, and security configurations
4. Call save_project_analysis with your JSON analysis result
5. Hand off to BusinessVulnAgent

## Output Format (for save_project_analysis)

The analysis JSON object MUST strictly follow this structure:

```json
{
  "tech_stack": {
    "language": "Java",
    "framework": "Spring Boot 2.5.0",
    "orm": "MyBatis 3.5.6",
    "server": "Tomcat 9.0"
  },
  "routes": [
    {
      "path": "/api/user/{id}",
      "method": "GET",
      "handler": "UserController.getUser",
      "auth_required": false
    }
  ],
  "security_configs": [
    {
      "type": "filter",
      "name": "AuthenticationFilter",
      "file": "src/main/java/config/SecurityConfig.java",
      "enabled": true
    }
  ],
  "dependencies": [
    {
      "name": "fastjson",
      "version": "1.2.24",
      "known_cves": ["CVE-2017-18349"],
      "severity": "high"
    }
  ],
  "high_risk_areas": [
    "File upload function lacks type validation",
    "CORS config set to wildcard *"
  ]
}
```

## MANDATORY NEXT STEP
After calling save_project_analysis, you MUST hand off to BusinessVulnAgent.
"""

def create_project_analyzer_agent(llm, tools: List) -> FunctionAgent:
    state_tools = [
        FunctionTool.from_defaults(
            async_fn=save_project_analysis,
            name="save_project_analysis",
            description="Save project analysis results to shared state. Args: analysis (dict) - Analysis JSON object"
        ),
        FunctionTool.from_defaults(
            async_fn=get_project_path,
            name="get_project_path",
            description="Get the project path from shared state."
        ),
    ]

    return FunctionAgent(
        name="ProjectAnalyzer",
        description="Analyze project structure, identify tech stack, extract routes and security configs",
        system_prompt=f"{PROJECT_ANALYSIS_KNOWLEDGE_BASE}\n\n{PROJECT_ANALYSIS_TASK}",
        llm=llm,
        tools=tools + state_tools,
        can_handoff_to=["BusinessVulnAgent"]
    )
