from typing import List
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from prompts.project_analysis import PROJECT_ANALYSIS_PROMPT


def create_project_analyzer_agent(llm, tools: List[FunctionTool]) -> FunctionAgent:
    return FunctionAgent(
        name="ProjectAnalyzer",
        description="Analyze project structure, identify tech stack, extract routes and security configs",
        system_prompt=f"""{PROJECT_ANALYSIS_PROMPT}

## Your Task
1. Use tools to explore the project (get_project_files, extract_routes, discover_security_config_files)
2. Identify tech stack, routes, and security configurations
3. Output your analysis in JSON format

## MANDATORY NEXT STEP - YOU MUST DO THIS
After you output the JSON analysis above, you MUST IMMEDIATELY hand off to BusinessVulnAgent.

DO NOT END THE CONVERSATION. DO NOT WAIT FOR USER INPUT.

Say exactly: "I will now hand off to BusinessVulnAgent for vulnerability detection."
Then IMMEDIATELY call the handoff tool to transfer control to BusinessVulnAgent.
""",
        llm=llm,
        tools=tools,
        can_handoff_to=["BusinessVulnAgent"]
    )
