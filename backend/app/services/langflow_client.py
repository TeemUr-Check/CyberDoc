import httpx
import json
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты - CyberDoc Pro AI, эксперт по информационной безопасности и безопасной разработке. "
    "Твоя задача - помогать пользователям находить уязвимости в коде и веб-приложениях, "
    "объяснять механику их эксплуатации и предлагать конкретные исправления. "
    "Ты хорошо знаком с OWASP Top 10, типовыми атаками (XSS, CSRF, SSRF, SQL-инъекции, "
    "небезопасная десериализация, нарушения контроля доступа) и методологиями SAST/DAST. "
    "При анализе кода указывай строку или фрагмент с ошибкой, объясняй, почему это опасно, "
    "и давай исправленный вариант с пояснением. "
    "Если пользователь задает общий вопрос по ИБ, отвечай структурированно: определение, "
    "примеры, рекомендации. "
    "Если пользователь задает вопрос на тему, не связанную с ИТ или информационной безопасностью, "
    "просто отвечай на его вопрос по существу в рамках его темы. Не пытайся искусственно перевести "
    "разговор на программирование и не предлагай обсудить информатику. "
    "Отвечай на русском языке, профессионально, но доступно для начинающих разработчиков. "
    "Используй markdown для форматирования: заголовки, списки, блоки кода."
)


class LangFlowClient:
    """Async client: tries LangFlow first, falls back to direct Mistral API."""

    def __init__(self, settings: Settings):
        self._langflow_url = settings.langflow_run_url
        self._langflow_key = settings.langflow_api_key
        self._mistral_key = settings.mistral_api_key
        self._timeout = settings.request_timeout

    async def send_message(self, message: str, session_id: str) -> str:
        reply = await self._try_langflow(message, session_id)
        if reply:
            return reply
        return await self._try_mistral_direct(message)

    async def _try_langflow(self, message: str, session_id: str) -> str | None:
        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "session_id": session_id,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._langflow_key,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, verify=False, trust_env=False
            ) as client:
                resp = await client.post(
                    self._langflow_url, json=payload, headers=headers
                )
                if resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
                    data = resp.json()
                    text = self._extract_reply(data)
                    if text and "не удалось извлечь" not in text:
                        return text
                resp.raise_for_status()
        except Exception as exc:
            logger.info("LangFlow unavailable (%s), falling back to Mistral direct", exc)
        return None

    async def _try_mistral_direct(self, message: str) -> str:
        if not self._mistral_key:
            return (
                "AI-ассистент не настроен. Укажите MISTRAL_API_KEY в переменных окружения "
                "или настройте LangFlow."
            )
        payload = {
            "model": "codestral-latest",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "max_tokens": 16384,
            "temperature": 0.3,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._mistral_key}",
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
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            return "Превышено время ожидания ответа от Mistral AI."
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            logger.error("Mistral API error %s: %s", code, exc.response.text[:300])
            if code == 401:
                return "Неверный ключ Mistral API. Проверьте MISTRAL_API_KEY."
            return f"Ошибка Mistral AI (HTTP {code})."
        except Exception as exc:
            logger.error("Mistral direct error: %s", exc)
            return "Не удалось связаться с Mistral AI."

    @staticmethod
    def _extract_reply(data: dict) -> str:
        try:
            outputs = data["outputs"][0]["outputs"][0]["results"]
            text = outputs.get("message", {}).get("text")
            if text:
                return text
            text = outputs.get("message", {}).get("data", {}).get("text")
            if text:
                return text
        except (KeyError, IndexError, TypeError):
            pass
        return "Ответ получен, но текст не удалось извлечь."
