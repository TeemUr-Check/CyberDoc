import httpx
import json
import logging

from app.config import Settings

logger = logging.getLogger(__name__)


class LangFlowClient:
    """Async client for communicating with a LangFlow instance."""

    def __init__(self, settings: Settings):
        self._url = settings.langflow_run_url
        self._api_key = settings.langflow_api_key
        self._timeout = settings.request_timeout

    async def send_message(self, message: str, session_id: str) -> str:
        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "session_id": session_id,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }
        async with httpx.AsyncClient(
            timeout=self._timeout,
            verify=False,
            trust_env=False,
        ) as client:
            try:
                resp = await client.post(self._url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return self._extract_reply(data)
            except httpx.TimeoutException:
                logger.error("LangFlow request timed out")
                return "Превышено время ожидания ответа от LangFlow."
            except httpx.HTTPStatusError as exc:
                return self._parse_http_error(exc)
            except httpx.ConnectError:
                logger.error("Cannot connect to LangFlow")
                return (
                    "Не удалось подключиться к LangFlow. "
                    "Убедитесь, что LangFlow запущен (docker ps)."
                )
            except Exception as exc:
                logger.error("LangFlow connection error: %s", exc)
                return "Не удалось связаться с LangFlow. Проверьте, что сервис запущен."

    @staticmethod
    def _parse_http_error(exc: httpx.HTTPStatusError) -> str:
        code = exc.response.status_code
        body = exc.response.text[:500]
        logger.error("LangFlow HTTP %s: %s", code, body)

        if "api_key" in body.lower() or "api key" in body.lower():
            return (
                "Для работы AI-ассистента необходимо настроить ключ OpenAI API. "
                "Откройте LangFlow (http://localhost:7860), выберите поток "
                "'CyberDoc Chatbot', нажмите на узел 'Language Model' и "
                "введите ваш OpenAI API ключ."
            )
        if code == 403:
            return "Ошибка авторизации LangFlow. Проверьте API-ключ."
        if code == 404:
            return "Поток LangFlow не найден. Проверьте конфигурацию."

        try:
            data = json.loads(body)
            detail = data.get("detail", "")
            if isinstance(detail, str) and "message" in detail:
                inner = json.loads(detail)
                msg = inner.get("message", "")
                if msg:
                    return f"Ошибка LangFlow: {msg[:200]}"
        except (json.JSONDecodeError, KeyError):
            pass

        return f"Ошибка LangFlow (HTTP {code})."

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
