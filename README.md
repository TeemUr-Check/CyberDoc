# CyberDoc Pro

Веб-платформа для проверки безопасности (FastAPI + фронтенд). ИИ-чат: LangFlow (опционально) и прямой вызов Mistral API (fallback).

## Установка и запуск (Docker)

**Нужно:** Docker и Docker Compose (v2).

1. Клонируйте репозиторий и перейдите в папку проекта.

2. Создайте файл `.env` из шаблона и заполните значения:
   ```bash
   cp .env.example .env
   ```
   Минимум для чата без ручной настройки графа в LangFlow: **`MISTRAL_API_KEY`** (ключ Mistral AI).

3. Запуск:
   ```bash
   docker compose up -d --build
   ```

4. Откройте в браузере:
   - приложение: **http://localhost:8000**
   - LangFlow: **http://localhost:7860** (логин по умолчанию: `langflow` / `langflow`)

Первый запуск LangFlow может занять 1-2 минуты, пока сервис станет `healthy`.

### LangFlow и чат

- В `.env` укажите **`LANGFLOW_FLOW_ID`** и **`LANGFLOW_API_KEY`**, если бэкенд должен ходить в ваш поток LangFlow (ключ создаётся в LangFlow: Settings → API Keys).
- Если поток ещё не создан или ID не совпадает с новой установкой, чат всё равно может отвечать через **Mistral**, если задан **`MISTRAL_API_KEY`**.

### Другое устройство

Файл `.env` в Git не хранится. Скопируйте его вручную или снова создайте из `.env.example` и вставьте свои ключи.
