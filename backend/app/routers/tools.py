from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.page_analyzer import PageAnalyzer
from app.services.port_scanner import PortScanner
from app.services.ssl_checker import SSLChecker
from app.services.dns_recon import DnsRecon
from app.services.subdomain_scanner import SubdomainScanner
from app.services.dir_scanner import DirScanner

router = APIRouter(tags=["tools"])


class ToolRequest(BaseModel):
    tool_name: str
    params: str


class VulnerabilityReport(BaseModel):
    success: bool
    vulnerabilities: list[str]
    source_code: str


class PortResult(BaseModel):
    port: int
    status: str
    service: str


class SSLReport(BaseModel):
    valid: bool
    subject: str | None = None
    issuer: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    days_remaining: int | None = None
    fingerprint: str | None = None
    error: str | None = None


def _exc_detail(exc: Exception) -> str:
    msg = str(exc)
    return msg if msg else f"{type(exc).__name__}: internal error"


@router.post("/tool/page-analyzer", response_model=VulnerabilityReport)
async def analyze_page(body: ToolRequest):
    analyzer = PageAnalyzer()
    try:
        return await analyzer.analyze(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool/port-scanner")
async def scan_ports(body: ToolRequest) -> list[PortResult]:
    scanner = PortScanner()
    try:
        return await scanner.scan(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool/ssl-checker", response_model=SSLReport)
async def check_ssl(body: ToolRequest):
    checker = SSLChecker()
    try:
        return await checker.check(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool/dns-recon")
async def dns_recon(body: ToolRequest):
    recon = DnsRecon()
    try:
        return await recon.recon(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool/subdomain-scanner")
async def scan_subdomains(body: ToolRequest):
    scanner = SubdomainScanner()
    try:
        return await scanner.scan(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool/dir-scanner")
async def scan_dirs(body: ToolRequest):
    scanner = DirScanner()
    try:
        return await scanner.scan(body.params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_exc_detail(exc))


@router.post("/tool")
async def run_tool(body: ToolRequest):
    """Universal tool endpoint for backward compatibility."""
    handlers = {
        "page-analyzer": analyze_page,
        "port-scanner": scan_ports,
        "ssl-checker": check_ssl,
        "dns-recon": dns_recon,
        "subdomain-scanner": scan_subdomains,
        "dir-scanner": scan_dirs,
    }
    handler = handlers.get(body.tool_name)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {body.tool_name}")
    return await handler(body)
