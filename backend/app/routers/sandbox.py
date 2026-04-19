from fastapi import APIRouter, Depends
from pydantic import BaseModel
import httpx

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


@router.post("/sandbox/poc")
async def generate_poc(body: AnalyzeRequest, settings: Settings = Depends(get_settings)):
    analyzer = CodeAnalyzer(settings)
    poc = await analyzer.generate_poc(body.code, body.language)
    return {"poc": poc}


@router.post("/sandbox/run")
async def run_code(body: AnalyzeRequest):
    # Map languages to Piston API format
    lang_map = {
        "python": ("python", "3.10.0"),
        "javascript": ("javascript", "18.15.0"),
        "typescript": ("typescript", "5.0.3"),
        "go": ("go", "1.16.2"),
        "rust": ("rust", "1.68.2"),
        "c": ("c", "10.2.0"),
        "cpp": ("cpp", "10.2.0"),
        "java": ("java", "15.0.2"),
        "php": ("php", "8.2.3"),
        "ruby": ("ruby", "3.0.1"),
        "bash": ("bash", "5.2.0"),
        "shell": ("bash", "5.2.0")
    }
    
    lang_info = lang_map.get(body.language.lower())
    if not lang_info:
        return {"output": f"Язык {body.language} не поддерживается для выполнения.", "error": True}
        
    payload = {
        "language": lang_info[0],
        "version": lang_info[1],
        "files": [{"content": body.code}],
        "stdin": "",
        "args": [],
        "compile_timeout": 10000,
        "run_timeout": 3000,
        "compile_memory_limit": -1,
        "run_memory_limit": -1
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://emacs.piston.rs/api/v2/execute", json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            output = ""
            if "compile" in data and data["compile"].get("output"):
                output += data["compile"]["output"] + "\n"
            if "run" in data and data["run"].get("output"):
                output += data["run"]["output"]
                
            return {"output": output.strip() or "Успешно выполнено (нет вывода)", "error": False}
    except Exception as e:
        return {"output": f"Ошибка выполнения: {str(e)}", "error": True}
