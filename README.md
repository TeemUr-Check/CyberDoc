# CyberDoc Pro

Веб-платформа для проверки безопасности (FastAPI + фронтенд). ИИ-чат: LangFlow (опционально) и прямой вызов Mistral API (fallback).

## Установка и запуск (Docker)

**Нужно:** установленные Git, Docker и Docker Compose (v2).

### Linux / macOS

```bash
git clone https://github.com/TeemUr-Check/CyberDoc.git
cd CyberDoc
cp .env.example .env
```

Откройте `.env` в редакторе и заполните переменные (минимум для чата: **`MISTRAL_API_KEY`**). Затем:

```bash
docker compose up -d --build
```

### Windows (PowerShell)

```powershell
git clone https://github.com/TeemUr-Check/CyberDoc.git
cd CyberDoc
copy .env.example .env
notepad .env
docker compose up -d --build
```

После запуска откройте в браузере:

- приложение: **http://localhost:8000**
- LangFlow: **http://localhost:7860** (логин по умолчанию: `langflow` / `langflow`)

Первый запуск LangFlow может занять 1-2 минуты, пока контейнер станет `healthy`.

### Остановка

```bash
docker compose down
```

### LangFlow и чат

- В `.env` задайте **`LANGFLOW_FLOW_ID`** и **`LANGFLOW_API_KEY`**, если бэкенд должен вызывать ваш поток в LangFlow (ключ: LangFlow → Settings → API Keys).
- Если поток не настроен или ID не совпадает с новой установкой, чат может отвечать через **Mistral**, если указан **`MISTRAL_API_KEY`**.

### Другое устройство

Файл `.env` в репозиторий не попадает. Перенесите его вручную или снова выполните `cp` / `copy .env.example .env` и вставьте ключи.
