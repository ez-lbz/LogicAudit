from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def print_section_header(title: str):
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("=" * 60)


def print_progress(message: str):
    console.print(f"[*] {message}", style="dim")


def format_vulnerability_report(vulnerabilities: list) -> str:
    if not vulnerabilities:
        return "[+] No vulnerabilities found"
    
    table = Table(title="Vulnerabilities")
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="red")
    table.add_column("File", style="green")
    table.add_column("Line", justify="right")
    
    for vuln in vulnerabilities:
        table.add_row(
            vuln.get("type", "Unknown"),
            vuln.get("severity", "UNKNOWN"),
            vuln.get("file", ""),
            str(vuln.get("line", ""))
        )
    
    console.print(table)
    return ""
