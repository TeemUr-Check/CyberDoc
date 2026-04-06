from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import time

router = APIRouter(tags=["api-tester"])

SECURITY_HEADERS = {
    "strict-transport-security": {
        "name": "Strict-Transport-Security (HSTS)",
        "severity": "HIGH",
        "desc": "Отсутствует HSTS — браузер может загрузить сайт по HTTP.",
        "fix": "Добавьте заголовок: Strict-Transport-Security: max-age=31536000; includeSubDomains",
    },
    "content-security-policy": {
        "name": "Content-Security-Policy (CSP)",
        "severity": "HIGH",
        "desc": "Нет политики CSP — повышен риск XSS-атак.",
        "fix": "Настройте CSP: Content-Security-Policy: default-src 'self'; script-src 'self'",
    },
    "x-content-type-options": {
        "name": "X-Content-Type-Options",
        "severity": "MEDIUM",
        "desc": "Браузер может интерпретировать MIME-тип файла некорректно.",
        "fix": "Добавьте: X-Content-Type-Options: nosniff",
    },
    "x-frame-options": {
        "name": "X-Frame-Options",
        "severity": "MEDIUM",
        "desc": "Страница может быть встроена в iframe — риск clickjacking.",
        "fix": "Добавьте: X-Frame-Options: DENY или SAMEORIGIN",
    },
    "x-xss-protection": {
        "name": "X-XSS-Protection",
        "severity": "LOW",
        "desc": "Встроенный фильтр XSS браузера не активирован.",
        "fix": "Добавьте: X-XSS-Protection: 1; mode=block",
    },
    "referrer-policy": {
        "name": "Referrer-Policy",
        "severity": "LOW",
        "desc": "Не задана политика отправки Referer — возможна утечка URL.",
        "fix": "Добавьте: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "permissions-policy": {
        "name": "Permissions-Policy",
        "severity": "LOW",
        "desc": "Не ограничены разрешения API браузера (камера, микрофон, геолокация).",
        "fix": "Добавьте: Permissions-Policy: camera=(), microphone=(), geolocation=()",
    },
}


class ApiTestRequest(BaseModel):
    method: str
    url: str
    headers: dict[str, str] = {}
    body: str = ""


@router.post("/api-test/send")
async def send_request(body: ApiTestRequest):
    method = body.method.upper()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
        raise HTTPException(400, "Неподдерживаемый HTTP-метод")

    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL должен начинаться с http:// или https://")

    req_kwargs: dict = {
        "method": method,
        "url": body.url,
        "headers": body.headers or {},
    }
    if method in ("POST", "PUT", "PATCH") and body.body:
        req_kwargs["content"] = body.body.encode("utf-8")

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=15.0, verify=False, trust_env=False, follow_redirects=True, max_redirects=5
        ) as client:
            resp = await client.request(**req_kwargs)
    except httpx.TimeoutException:
        raise HTTPException(504, "Превышено время ожидания (15 сек)")
    except Exception as exc:
        raise HTTPException(502, f"Ошибка подключения: {exc}")

    elapsed = round((time.monotonic() - start) * 1000)

    resp_headers = dict(resp.headers)
    resp_body = ""
    try:
        resp_body = resp.text[:50000]
    except Exception:
        resp_body = "(бинарное содержимое)"

    missing = []
    present = []
    lower_headers = {k.lower(): v for k, v in resp_headers.items()}
    for hdr_key, info in SECURITY_HEADERS.items():
        if hdr_key in lower_headers:
            present.append({
                "header": info["name"],
                "value": lower_headers[hdr_key],
                "status": "ok",
            })
        else:
            missing.append({
                "header": info["name"],
                "severity": info["severity"],
                "description": info["desc"],
                "fix": info["fix"],
                "status": "missing",
            })

    cors_origin = lower_headers.get("access-control-allow-origin", "")
    cors_warning = None
    if cors_origin == "*":
        cors_warning = {
            "header": "Access-Control-Allow-Origin",
            "severity": "HIGH",
            "description": "CORS разрешает запросы с любого домена (*) — риск утечки данных.",
            "fix": "Ограничьте origin конкретными доменами.",
        }

    return {
        "status_code": resp.status_code,
        "elapsed_ms": elapsed,
        "response_headers": resp_headers,
        "response_body": resp_body,
        "content_type": lower_headers.get("content-type", ""),
        "security_analysis": {
            "present_headers": present,
            "missing_headers": missing,
            "cors_warning": cors_warning,
            "score": round(len(present) / max(len(present) + len(missing), 1) * 100),
        },
    }
