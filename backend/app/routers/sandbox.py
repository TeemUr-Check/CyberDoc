from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.code_analyzer import CodeAnalyzer

router = APIRouter(tags=["sandbox"])


class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"


@router.post("/sandbox/analyze")
async def analyze_code(body: AnalyzeRequest, settings: Settings = Depends(get_settings)):
    analyzer = CodeAnalyzer(settings)
    return await analyzer.analyze(body.code, body.language)
