import json
import logging
import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

ANALYZE_PROMPT = (
    "Ты — статический анализатор безопасности кода (SAST). "
    "Проанализируй код на языке {language} и найди ВСЕ уязвимости безопасности.\n"
    "Ищи: SQL-инъекции, XSS, небезопасный пользовательский ввод, утечки данных, "
    "захардкоженные секреты, небезопасную криптографию, нарушения контроля доступа, "
    "небезопасную десериализацию, SSRF, path traversal, CSRF, open redirect.\n\n"
    "ВАЖНО: весь текст (title, description, fix, fixed_code, summary) пиши НА РУССКОМ ЯЗЫКЕ.\n"
    "Для каждой уязвимости ОБЯЗАТЕЛЬНО предоставь исправленный фрагмент кода в поле fixed_code.\n\n"
    "Верни ответ СТРОГО в JSON без markdown-обёртки:\n"
    '{{"vulnerabilities":['
    '{{"line":1,"severity":"CRITICAL",'
    '"title":"Название уязвимости на русском",'
    '"description":"Подробное описание проблемы на русском",'
    '"fix":"Текстовое объяснение как исправить на русском",'
    '"fixed_code":"исправленный фрагмент кода"}}'
    '],"summary":"Общая оценка безопасности кода на русском"}}\n\n'
    "Допустимые severity: CRITICAL, HIGH, MEDIUM, LOW, INFO.\n"
    "Если уязвимостей нет, верни пустой массив.\n\n"
    "Код для анализа:\n```{language}\n{code}\n```"
)


class CodeAnalyzer:
    def __init__(self, settings: Settings):
        self._key = settings.mistral_api_key
        self._timeout = settings.request_timeout

    async def analyze(self, code: str, language: str) -> dict:
        if not self._key:
            return {"vulnerabilities": [], "summary": "MISTRAL_API_KEY не настроен."}

        prompt = ANALYZE_PROMPT.format(language=language, code=code)
        payload = {
            "model": "codestral-latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 32768,
            "temperature": 0.1,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._key}",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, verify=False, trust_env=False
            ) as client:
                resp = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()
                return json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse SAST response as JSON")
            return {"vulnerabilities": [], "summary": "Не удалось разобрать ответ ИИ."}
        except httpx.TimeoutException:
            return {"vulnerabilities": [], "summary": "Превышено время ожидания."}
        except Exception as exc:
            logger.error("Code analysis error: %s", exc)
            return {"vulnerabilities": [], "summary": f"Ошибка анализа: {exc}"}

    async def generate_poc(self, code: str, language: str) -> str:
        if not self._key:
            return "MISTRAL_API_KEY не настроен."

        prompt = (
            f"Ты — эксперт по информационной безопасности. Проанализируй этот код на {language} "
            "и напиши рабочий Proof of Concept (PoC) эксплойт, который демонстрирует уязвимость "
            "в этом коде. Верни ТОЛЬКО код эксплойта (на Python или bash) с комментариями, "
            "без лишних рассуждений.\n\nКод:\n```{language}\n{code}\n```"
        )
        payload = {
            "model": "codestral-latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 32768,
            "temperature": 0.2,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._key}",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, verify=False, trust_env=False
            ) as client:
                resp = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error("PoC generation error: %s", exc)
            return f"Ошибка генерации PoC: {exc}"
