from typing import Dict, Any, List
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.tools import FunctionTool
from tools.wrapper import create_audit_tools, set_project_root
from prompts.project_analysis import PROJECT_ANALYSIS_PROMPT
from prompts.business_vuln import BUSINESS_VULN_PROMPT
from prompts.report_gen import REPORT_GEN_PROMPT
from utils.logger import logger
from utils.report_formatter import format_project_analysis, format_vulnerabilities, format_final_report, print_agent_status
import json


def _tool_to_openai_spec(tool: FunctionTool) -> dict:
    """Convert a FunctionTool to OpenAI function-calling dict format."""
    fn_schema = tool.metadata.get_parameters_dict()
    return {
        "type": "function",
        "function": {
            "name": tool.metadata.name,
            "description": tool.metadata.description or "",
            "parameters": fn_schema,
        }
    }


class AuditAgentWorkflow:

    def __init__(self, llm):
        self.llm = llm
        self.tools = create_audit_tools()
        self.tool_map = {t.metadata.name: t for t in self.tools}
        self.openai_tools = [_tool_to_openai_spec(t) for t in self.tools]

        logger.info("=" * 60)
        logger.info("[*] Initializing AgentWorkflow")
        logger.info("=" * 60)
        logger.info("[+] Created tool-based serial workflow")
        logger.info(f"[+] Available tools: {list(self.tool_map.keys())}")
        logger.info("[+] Pipeline: ProjectAnalyzer -> BusinessVuln -> ReportGenerator")
        logger.info("=" * 60)

    async def _run_agent_step(self, system_prompt: str, user_prompt: str, use_tools: bool = True, max_iterations: int = 25) -> str:
        """Run a single agent step with manual tool-call loop."""
        # Enforce forward slashes globally to prevent JSON escape errors (e.g. \b -> backspace)
        system_prompt += "\n\nCRITICAL: ALWAYS use forward slashes `/` for file paths (e.g. `backend/app/main.py`), even heavily on Windows. Python handles forward slashes correctly on all OS. DO NOT use backslashes `\\` to avoid JSON escape sequence errors."
        
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]

        extra_kwargs = {}
        if use_tools:
            extra_kwargs["tools"] = self.openai_tools

        for i in range(max_iterations):
            response = await self.llm.achat(messages, **extra_kwargs)
            assistant_msg = response.message
            messages.append(assistant_msg)

            tool_calls = assistant_msg.additional_kwargs.get("tool_calls")
            if not tool_calls:
                return assistant_msg.content or ""

            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                logger.info(f"  [TOOL] {fn_name}({fn_args})")

                if fn_name in self.tool_map:
                    try:
                        result = self.tool_map[fn_name].call(**fn_args)
                        result_str = str(result)
                        if len(result_str) > 8000:
                            result_str = result_str[:8000] + "\n... [truncated]"
                    except Exception as e:
                        result_str = f"Error calling {fn_name}: {e}"
                        logger.error(f"  [TOOL ERROR] {fn_name}: {e}")
                else:
                    result_str = f"Unknown tool: {fn_name}"

                messages.append(ChatMessage(
                    role=MessageRole.TOOL,
                    content=result_str,
                    additional_kwargs={"tool_call_id": tc.id, "name": fn_name},
                ))

        return messages[-1].content or ""

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text."""
        start = text.find('```json')
        end = text.find('```', start + 7) if start != -1 else -1
        if start != -1 and end != -1:
            try:
                return json.loads(text[start + 7:end].strip())
            except json.JSONDecodeError:
                pass

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse JSON from response. Raw text length: {len(text)}")
        return {}

    async def run_async(self, project_path: str, user_msg: str = None) -> Dict[str, Any]:
        # Normalize path to forward slashes for LLM consistency
        project_path = project_path.replace('\\', '/')
        
        logger.info(f"[*] Starting audit workflow: {project_path}")
        logger.info("=" * 80)

        # Set project root for path resolution
        set_project_root(project_path)

        final_state = {
            "project_path": project_path,
            "project_analysis": {},
            "business_vulnerabilities": [],
            "final_report": {}
        }

        # ── Step 1: ProjectAnalyzer ──
        logger.info("\n[1/3] Running ProjectAnalyzer...")
        print_agent_status("ProjectAnalyzer", "Analyzing project structure")

        try:
            analysis_text = await self._run_agent_step(
                system_prompt=PROJECT_ANALYSIS_PROMPT,
                user_prompt=f"""Analyze the project at: {project_path}

Use available tools to:
1. Visualize directory structure (get_file_tree) - **DO THIS FIRST**
2. List project files (get_project_files)
3. Identify tech stack from dependency files (read_file on pom.xml/package.json/requirements.txt)
4. Extract HTTP routes (extract_routes)
5. Find security configs (discover_security_config_files)
6. Search for patterns using RAG (query_with_llm / semantic_search)

Output ONLY valid JSON:
```json
{{
  "tech_stack": {{"language": "...", "framework": "...", "version": "..."}},
  "routes": [{{"path": "...", "method": "...", "handler": "...", "auth_required": true}}],
  "security_configs": [...],
  "high_risk_areas": [...]
}}
```"""
            )
            final_state['project_analysis'] = self._parse_json(analysis_text)
            logger.info(f"[OK] Project analysis: {len(final_state['project_analysis'])} keys")
            if final_state['project_analysis']:
                format_project_analysis(final_state['project_analysis'])
        except Exception as e:
            logger.error(f"[ERROR] ProjectAnalyzer failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        project_ctx = json.dumps(final_state['project_analysis'], indent=2, default=str)

        # ── Step 2: BusinessVulnAgent ──
        logger.info("\n[2/3] Running BusinessVulnAgent...")
        print_agent_status("BusinessVulnAgent", "Scanning for business logic flaws")

        try:
            biz_text = await self._run_agent_step(
                system_prompt=BUSINESS_VULN_PROMPT,
                user_prompt=f"""Find business logic vulnerabilities (IDOR, privilege escalation, mass assignment, race conditions, auth bypass, etc).

**IMPORTANT: The project root path is: {project_path}**
All tool calls MUST use this full absolute path. For example:
- search_by_keyword(project_path="{project_path}", keyword="...")
- read_file(file_path="{project_path}/backend/app/api/v1/auth.py")

**Project Context:**
```json
{project_ctx}
```

Use tools: read_file, search_by_keyword, semantic_search to examine auth, authorization, and business workflows.

Output ONLY valid JSON with TOP 10 vulnerabilities:
```json
{{
  "vulnerabilities": [
    {{
      "type": "IDOR",
      "severity": "HIGH",
      "file": "path/to/file",
      "line": 123,
      "code_snippet": "vulnerable code here",
      "description": "description",
      "poc": "proof of concept",
      "recommendation": "how to fix"
    }}
  ]
}}
```"""
            )
            parsed = self._parse_json(biz_text)
            final_state['business_vulnerabilities'] = parsed.get('vulnerabilities', [])
            logger.info(f"[OK] Found {len(final_state['business_vulnerabilities'])} business vulnerabilities")
            if final_state['business_vulnerabilities']:
                format_vulnerabilities(final_state['business_vulnerabilities'], "BUSINESS VULNERABILITIES")
        except Exception as e:
            logger.error(f"[ERROR] BusinessVulnAgent failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # ── Step 3: ReportGenerator ──
        logger.info("\n[3/3] Running ReportGenerator...")
        print_agent_status("ReportGenerator", "Generating final report")

        all_vulns = {
            "business": final_state['business_vulnerabilities']
        }

        try:
            report_text = await self._run_agent_step(
                system_prompt=REPORT_GEN_PROMPT,
                user_prompt=f"""Generate final audit report.

**All Findings:**
```json
{json.dumps(all_vulns, indent=2, default=str)}
```

Deduplicate, rank by severity, select TOP 10 most critical.

Output ONLY valid JSON:
```json
{{
  "summary": "Executive summary of the audit...",
  "statistics": {{"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}},
  "vulnerabilities": [...]
}}
```""",
                use_tools=False
            )
            final_state['final_report'] = self._parse_json(report_text)
            logger.info("[OK] Report generation complete")
            if final_state['final_report']:
                format_final_report(final_state['final_report'])
        except Exception as e:
            logger.error(f"[ERROR] ReportGenerator failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        logger.info("\n" + "=" * 80)
        logger.info("[+] Audit workflow completed")
        logger.info("=" * 80)

        return {
            "response": "Audit completed",
            "state": final_state
        }

    def run(self, project_path: str, user_msg: str = None) -> Dict[str, Any]:
        import asyncio
        return asyncio.run(self.run_async(project_path, user_msg))
