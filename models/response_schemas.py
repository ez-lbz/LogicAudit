from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class TechStack(BaseModel):
    language: str = Field(description="Main programming language")
    framework: Optional[str] = Field(default="unknown", description="Web framework")
    orm: Optional[str] = Field(default=None, description="ORM framework")
    version: Optional[str] = Field(default=None, description="Version info")


class Route(BaseModel):
    path: str = Field(description="Route path")
    method: str = Field(default="GET", description="HTTP method")
    handler: str = Field(default="", description="Handler function name")
    auth_required: bool = Field(default=False, description="Whether auth is required")


class ProjectAnalysisResult(BaseModel):
    tech_stack: TechStack = Field(description="Tech stack info")
    routes: List[Route] = Field(default_factory=list, description="Routes list")
    security_configs: List[Dict] = Field(default_factory=list, description="Security configs list")
    high_risk_areas: List[str] = Field(default_factory=list, description="High risk areas")
    summary: str = Field(default="", description="Analysis summary")


class Vulnerability(BaseModel):
    type: str = Field(description="Vulnerability type")
    severity: str = Field(description="Severity: CRITICAL/HIGH/MEDIUM/LOW")
    exploitability: int = Field(default=3, description="Exploitability score 1-5")
    file: str = Field(description="File path")
    line: Optional[int] = Field(default=None, description="Line number")
    code_snippet: Optional[str] = Field(default=None, description="Vulnerable code snippet")
    description: str = Field(description="Detailed description")
    cwe: Optional[str] = Field(default=None, description="CWE ID")
    poc: Optional[str] = Field(default=None, description="Proof of concept")
    recommendation: Optional[str] = Field(default=None, description="Fix recommendation")


class VulnDetectionResult(BaseModel):
    vulnerabilities: List[Vulnerability] = Field(default_factory=list, description="Vulnerabilities list")


class ReportStatistics(BaseModel):
    total_count: int = Field(default=0, description="Total count")
    by_severity: Dict[str, int] = Field(default_factory=lambda: {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}, description="By severity")
    by_type: Dict[str, int] = Field(default_factory=dict, description="By type")
    high_exploitability_count: int = Field(default=0, description="High exploitability count")


class AuditReport(BaseModel):
    summary: str = Field(default="", description="Executive summary")
    statistics: ReportStatistics = Field(default_factory=ReportStatistics, description="Statistics")
    vulnerabilities: List[Vulnerability] = Field(default_factory=list, description="Vulnerabilities list")
    recommendations: List[str] = Field(default_factory=list, description="Fix recommendations")
    report_time: str = Field(default="", description="Report generation time")
