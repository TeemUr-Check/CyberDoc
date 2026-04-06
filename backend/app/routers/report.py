from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.services.report_generator import generate_report

router = APIRouter(tags=["report"])


class ReportRequest(BaseModel):
    tool_name: str
    target: str
    results: dict


@router.post("/report/generate", response_class=HTMLResponse)
async def create_report(body: ReportRequest):
    html = generate_report(body.tool_name, body.target, body.results)
    return HTMLResponse(content=html)
