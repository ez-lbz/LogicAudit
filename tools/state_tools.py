import json
from typing import List, Dict, Any, Union
from llama_index.core.workflow import Context
from utils.logger import logger


async def save_project_analysis(ctx: Context, analysis: Dict[str, Any]) -> str:
    try:
        data = analysis
        state = await ctx.store.get("state", default={})
        state["project_analysis"] = data
        await ctx.store.set("state", state)
        logger.info(f"[+] Saved project_analysis to state ({len(data)} keys)")
        return "Project analysis saved to shared state."
    except Exception as e:
        logger.error(f"[-] Failed to save project_analysis: {e}")
        return f"Error saving project analysis: {e}"


async def save_business_vulnerabilities(ctx: Context, vulnerabilities: List[Dict[str, Any]]) -> str:
    try:
        vulns = vulnerabilities
        state = await ctx.store.get("state", default={})
        
        # If existing vulns, append new ones
        existing_vulns = state.get("business_vulnerabilities", [])
        if isinstance(existing_vulns, list):
            existing_vulns.extend(vulns)
            state["business_vulnerabilities"] = existing_vulns
        else:
            state["business_vulnerabilities"] = vulns
            
        await ctx.store.set("state", state)
        logger.info(f"[+] Saved {len(vulns)} business vulnerabilities to state")
        return f"Saved {len(vulns)} business vulnerabilities to shared state."
    except Exception as e:
        logger.error(f"[-] Failed to save vulnerabilities: {e}")
        return f"Error saving vulnerabilities: {e}"


async def get_project_analysis(ctx: Context) -> str:
    state = await ctx.store.get("state", default={})
    data = state.get("project_analysis", {})
    return json.dumps(data, indent=2, default=str)


async def get_business_vulnerabilities(ctx: Context) -> str:
    state = await ctx.store.get("state", default={})
    data = state.get("business_vulnerabilities", [])
    return json.dumps(data, indent=2, default=str)


async def get_project_path(ctx: Context) -> str:
    state = await ctx.store.get("state", default={})
    return state.get("project_path", "")


async def get_audit_context(ctx: Context) -> str:
    state = await ctx.store.get("state", default={})
    return json.dumps({
        "project_analysis": state.get("project_analysis", {}),
        "business_vulnerabilities": state.get("business_vulnerabilities", [])
    }, indent=2, default=str)
