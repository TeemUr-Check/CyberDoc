import asyncio
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
    language = body.language.lower()

    # Reliable local execution for Python (primary IDE scenario)
    if language == "python":
        try:
            process = await asyncio.create_subprocess_exec(
                "python3",
                "-I",
                "-c",
                body.code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return {"output": "Ошибка выполнения: превышен лимит времени (5 секунд)", "error": True}

            out_text = (stdout or b"").decode("utf-8", errors="replace").strip()
            err_text = (stderr or b"").decode("utf-8", errors="replace").strip()
            combined = "\n".join([x for x in (out_text, err_text) if x]).strip()
            return {"output": combined or "Успешно выполнено (нет вывода)", "error": process.returncode != 0}
        except Exception as e:
            return {"output": f"Ошибка выполнения Python: {str(e)}", "error": True}

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
    
    lang_info = lang_map.get(language)
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
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post("https://emkc.org/api/v2/piston/execute", json=payload)
            resp.raise_for_status()
            data = resp.json()

            output_parts = []
            compile_data = data.get("compile") or {}
            run_data = data.get("run") or {}

            for key in ("output", "stdout", "stderr"):
                value = compile_data.get(key)
                if value:
                    output_parts.append(str(value))

            for key in ("output", "stdout", "stderr"):
                value = run_data.get(key)
                if value:
                    output_parts.append(str(value))

            return {
                "output": "\n".join(output_parts).strip() or "Успешно выполнено (нет вывода)",
                "error": (run_data.get("code", 0) != 0),
            }
    except Exception as e:
        return {
            "output": (
                "Внешний рантайм сейчас недоступен. "
                "Для стабильного запуска используйте Python-файлы (.py). "
                f"Техническая ошибка: {str(e)}"
            ),
            "error": True,
        }
