from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from typing import Dict, Any, List
import json

console = Console()


def format_project_analysis(analysis: Dict[str, Any]) -> None:
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold cyan]PROJECT ANALYSIS REPORT[/bold cyan]", border_style="cyan"))
    console.print("="*80 + "\n")
    
    tech_stack = analysis.get("tech_stack", {})
    if tech_stack:
        console.print("[bold yellow]Tech Stack:[/bold yellow]")
        table = Table(show_header=False, box=None)
        for key, value in tech_stack.items():
            table.add_row(f"  {key}:", f"[green]{value}[/green]")
        console.print(table)
        console.print()
    
    routes = analysis.get("routes", [])
    if routes:
        console.print(f"[bold yellow]HTTP Routes:[/bold yellow] ({len(routes)} endpoints)")
        route_table = Table(show_header=True, header_style="bold magenta")
        route_table.add_column("Method", style="cyan")
        route_table.add_column("Path", style="blue")
        route_table.add_column("Handler", style="green")
        route_table.add_column("Auth", style="yellow")
        
        for route in routes[:10]:
            route_table.add_row(
                route.get("method", ""),
                route.get("path", ""),
                route.get("handler_file", ""),
                "✓" if route.get("auth_required") else "✗"
            )
        console.print(route_table)
        if len(routes) > 10:
            console.print(f"  [dim]... and {len(routes) - 10} more routes[/dim]\n")
        else:
            console.print()
    
    configs = analysis.get("security_configs", [])
    if configs:
        console.print(f"[bold yellow]Security Configs:[/bold yellow] ({len(configs)} items)")
        for cfg in configs:
            console.print(f"  • {cfg.get('type', 'Unknown')}: [green]{cfg.get('file', 'N/A')}[/green]")
        console.print()
    
    deps = analysis.get("dependencies", [])
    if deps:
        risky_deps = [d for d in deps if d.get("known_cves") or d.get("severity") in ["high", "critical"]]
        console.print(f"[bold yellow]Dependencies:[/bold yellow] ({len(deps)} total, {len(risky_deps)} risky)")
        if risky_deps:
            for dep in risky_deps:
                console.print(f"  [red]⚠[/red] {dep.get('name', 'Unknown')} - {dep.get('severity', 'unknown')}")
        console.print()
    
    risks = analysis.get("high_risk_areas", [])
    if risks:
        console.print("[bold red]High Risk Areas:[/bold red]")
        for i, risk in enumerate(risks, 1):
            console.print(f"  {i}. [yellow]{risk}[/yellow]")
        console.print()


def format_vulnerabilities(vulns: List[Dict[str, Any]], title: str = "VULNERABILITIES") -> None:
    if not vulns:
        console.print(f"\n[green]✓ No {title.lower()} found[/green]\n")
        return
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(f"[bold red]{title}[/bold red]", border_style="red"))
    console.print("="*80 + "\n")
    
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_vulns = sorted(vulns, key=lambda v: severity_order.get(v.get("severity", "LOW"), 99))
    
    for i, vuln in enumerate(sorted_vulns[:10], 1):
        severity = vuln.get("severity", "UNKNOWN")
        severity_color = {
            "CRITICAL": "bold red",
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "blue"
        }.get(severity, "white")
        
        console.print(f"\n[bold]#{i} {vuln.get('type', 'Unknown Vulnerability')}[/bold]")
        console.print(f"Severity: [{severity_color}]{severity}[/{severity_color}]")
        console.print(f"File: [cyan]{vuln.get('file', 'N/A')}[/cyan]:{vuln.get('line', 'N/A')}")
        
        if vuln.get("description"):
            console.print(f"\n[yellow]Description:[/yellow]")
            console.print(f"  {vuln['description']}")
        
        if vuln.get("code_snippet"):
            console.print(f"\n[yellow]Code:[/yellow]")
            console.print(f"  [dim]{vuln['code_snippet'][:100]}{'...' if len(vuln['code_snippet']) > 100 else ''}[/dim]")
        
        if vuln.get("poc"):
            console.print(f"\n[yellow]PoC:[/yellow] [cyan]{vuln['poc']}[/cyan]")
        
        if vuln.get("recommendation"):
            console.print(f"\n[green]Fix:[/green] {vuln['recommendation']}")
        
        console.print("[dim]" + "-"*80 + "[/dim]")
    
    if len(vulns) > 10:
        console.print(f"\n[dim]... and {len(vulns) - 10} more vulnerabilities (showing top 10)[/dim]\n")


def format_final_report(report: Dict[str, Any]) -> None:
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold green]FINAL AUDIT REPORT[/bold green]", border_style="green"))
    console.print("="*80 + "\n")
    
    if "summary" in report:
        console.print("[bold cyan]Executive Summary:[/bold cyan]")
        console.print(report["summary"])
        console.print()
    
    stats = report.get("statistics", {})
    if stats:
        console.print("[bold cyan]Statistics:[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = stats.get(severity.lower(), 0)
            if count > 0:
                table.add_row(severity, str(count))
        
        console.print(table)
        console.print()
    
    vulns = report.get("vulnerabilities", [])
    if vulns:
        format_vulnerabilities(vulns, "TOP VULNERABILITIES")


def print_tool_call(tool_name: str, args: Dict[str, Any]) -> None:
    console.print(f"\n[bold blue]→ Tool Call:[/bold blue] [cyan]{tool_name}[/cyan]")
    if args:
        args_str = ", ".join([f"{k}={repr(v)[:50]}" for k, v in args.items()])
        console.print(f"  [dim]Args: {args_str}[/dim]")


def print_tool_result(tool_name: str, success: bool, result_preview: str = None) -> None:
    status = "[green]✓[/green]" if success else "[red]✗[/red]"
    console.print(f"{status} [bold blue]Tool:[/bold blue] {tool_name}")
    if result_preview:
        console.print(f"  [dim]{result_preview[:100]}{'...' if len(result_preview) > 100 else ''}[/dim]")


def print_agent_status(agent_name: str, action: str) -> None:
    console.print(f"\n[bold magenta]{agent_name}[/bold magenta]: [yellow]{action}[/yellow]")

