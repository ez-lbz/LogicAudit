from typing import List
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from prompts.business_vuln import BUSINESS_VULN_PROMPT


def create_business_vuln_agent(llm, tools: List[FunctionTool]) -> FunctionAgent:
    return FunctionAgent(
        name="BusinessVulnAgent",
        description="Detect business logic vulnerabilities like IDOR, privilege escalation, mass assignment",
        system_prompt=f"""{BUSINESS_VULN_PROMPT}

## Your Task
1. Read the project analysis from previous agent's output
2. Use tools to examine authentication, authorization, and business workflows
3. Focus on endpoints handling user data and permissions
4. Output TOP 10 most critical business vulnerabilities in JSON format

## CRITICAL: When you finish detection
After outputting your vulnerabilities JSON, you MUST hand off to ReportGenerator.
Say: "Handing off to ReportGenerator for final report compilation."
Then use the handoff function.
""",
        llm=llm,
        tools=tools,
        can_handoff_to=["ReportGenerator"]
    )
