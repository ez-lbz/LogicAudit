import json
import asyncio
from typing import Dict, Any
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.workflow import Context
from tools.wrapper import create_audit_tools, set_project_root
from agents.project_analyzer import create_project_analyzer_agent
from agents.business_vuln import create_business_vuln_agent
from agents.report_generator import create_report_generator_agent
from utils.logger import logger
from utils.report_formatter import format_project_analysis, format_vulnerabilities, format_final_report, print_agent_status


class AuditAgentWorkflow:

    def __init__(self, llm, enable_rag: bool = True, indexer=None):
        self.llm = llm
        self.enable_rag = enable_rag
        self.indexer = indexer

        tools = create_audit_tools(indexer=indexer, enable_rag=enable_rag)

        project_analyzer = create_project_analyzer_agent(llm, tools)
        business_vuln_agent = create_business_vuln_agent(llm, tools)
        report_generator = create_report_generator_agent(llm)

        self.workflow = AgentWorkflow(
            agents=[project_analyzer, business_vuln_agent, report_generator],
            root_agent="ProjectAnalyzer",
            initial_state={
                "project_path": "",
                "project_analysis": {},
                "business_vulnerabilities": [],
                "final_report": {},
            },
        )

        logger.info("=" * 60)
        logger.info("[*] Initializing AgentWorkflow")
        logger.info("=" * 60)
        rag_status = "enabled" if enable_rag and indexer else "disabled"
        logger.info(f"[+] RAG: {rag_status}")
        logger.info("[+] Pipeline: ProjectAnalyzer -> BusinessVulnAgent -> ReportGenerator")
        logger.info("=" * 60)

    def _parse_json(self, text: str) -> Dict[str, Any]:
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
        project_path = project_path.replace('\\', '/')

        logger.info(f"[*] Starting audit workflow: {project_path}")
        logger.info("=" * 80)

        set_project_root(project_path)

        self.workflow.initial_state["project_path"] = project_path

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print_agent_status("AgentWorkflow", f"Starting multi-agent audit pipeline (Attempt {attempt + 1}/{max_retries})")

                # Reset state for retry
                self.workflow.initial_state["project_path"] = project_path

                handler = self.workflow.run(
                    user_msg=user_msg or f"Audit the project at: {project_path}",
                    max_iterations=100
                )

                final_response = ""
                async for event in handler.stream_events():
                    event_type = type(event).__name__
                    if hasattr(event, 'msg'):
                        logger.info(f"  [EVENT] {event_type}: {str(event.msg)[:120]}")
                    elif hasattr(event, 'tool_name'):
                        logger.info(f"  [TOOL] {event.tool_name}")

                final_response = await handler

                ctx: Context = handler.ctx

                state = await ctx.store.get("state", default={})
                project_analysis = state.get("project_analysis", {})
                business_vulnerabilities = state.get("business_vulnerabilities", [])

                if project_analysis:
                    format_project_analysis(project_analysis)

                if business_vulnerabilities:
                    format_vulnerabilities(business_vulnerabilities, "BUSINESS VULNERABILITIES")

                final_report = self._parse_json(str(final_response))
                if final_report:
                    format_final_report(final_report)
                
                return final_report or {}

            except Exception as e:
                logger.error(f"[-] Workflow failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Error occurred: {e}. Retrying...")
                    await asyncio.sleep(2)
                else:
                    logger.error("[-] Max retries reached. Exiting.")
                    raise e
        return {}

        logger.info("\n" + "=" * 80)
        logger.info("[+] Audit workflow completed")
        logger.info("=" * 80)

        return {
            "response": str(final_response),
            "state": {
                "project_path": project_path,
                "project_analysis": project_analysis,
                "business_vulnerabilities": business_vulnerabilities,
                "final_report": final_report,
            }
        }

    def run(self, project_path: str, user_msg: str = None) -> Dict[str, Any]:
        import asyncio
        return asyncio.run(self.run_async(project_path, user_msg))
