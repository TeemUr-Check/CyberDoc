import json
import logging
import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

THREAT_PROMPT = (
    "Ты — эксперт по моделированию угроз. На основе результатов сканирования "
    "построй граф цепочки атак. Покажи, как злоумышленник может использовать "
    "найденные уязвимости последовательно для достижения цели.\n\n"
    "Результаты сканирования ({tool_name}, цель: {target}):\n{results_text}\n\n"
    "Верни СТРОГО JSON без markdown:\n"
    '{{"nodes":['
    '{{"id":"1","label":"Название шага","group":"vulnerability","title":"Подробное описание"}}'
    '],"edges":['
    '{{"from":"1","to":"2","label":"связь"}}'
    ']}}\n\n'
    "Группы узлов (group):\n"
    "- recon: разведка и сбор информации\n"
    "- vulnerability: обнаруженная уязвимость\n"
    "- attack: шаг эксплуатации\n"
    "- impact: последствия (утечка, компрометация)\n"
    "- fix: рекомендация по защите\n\n"
    "Создай 6-12 узлов и покажи реалистичную цепочку. "
    "Для каждого узла fix добавь ребро с dashes:true к узлу, который он закрывает. "
    "Отвечай на русском."
)


class ThreatModeler:
    def __init__(self, settings: Settings):
        self._key = settings.mistral_api_key
        self._timeout = settings.request_timeout

    async def model(self, tool_name: str, target: str, results: dict) -> dict:
        if not self._key:
            return _fallback_graph()

        results_text = json.dumps(results, ensure_ascii=False, default=str)[:3000]
        prompt = THREAT_PROMPT.format(
            tool_name=tool_name, target=target, results_text=results_text
        )
        payload = {
            "model": "codestral-latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "temperature": 0.3,
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
                data = json.loads(text)
                if "nodes" in data and "edges" in data:
                    return data
                return _fallback_graph()
        except Exception as exc:
            logger.error("Threat modeling error: %s", exc)
            return _fallback_graph()


def _fallback_graph() -> dict:
    return {
        "nodes": [
            {"id": "1", "label": "Сбор информации", "group": "recon", "title": "Сканирование цели"},
            {"id": "2", "label": "Обнаружение уязвимости", "group": "vulnerability", "title": "Найдена потенциальная брешь"},
            {"id": "3", "label": "Эксплуатация", "group": "attack", "title": "Использование уязвимости"},
            {"id": "4", "label": "Доступ к данным", "group": "impact", "title": "Компрометация системы"},
            {"id": "5", "label": "Обновить конфигурацию", "group": "fix", "title": "Закрыть уязвимость"},
        ],
        "edges": [
            {"from": "1", "to": "2", "label": "обнаружение"},
            {"from": "2", "to": "3", "label": "эксплуатация"},
            {"from": "3", "to": "4", "label": "последствия"},
            {"from": "5", "to": "2", "label": "закрывает", "dashes": True},
        ],
    }
