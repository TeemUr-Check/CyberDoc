# CyberDoc Pro

Платформа для автоматизированного аудита безопасности веб-ресурсов с ИИ-ассистентом.

## Возможности

- **ИИ-ассистент** на базе LangFlow для консультаций по информационной безопасности
- **Анализ веб-страниц** на уязвимости (XSS, CSRF, Open Redirect, утечка файлов)
- **Сканер портов** (TCP-проверка популярных сервисных портов)
- **Проверка SSL/TLS** (сертификат, срок действия, цепочка доверия)

## Требования

- Docker и Docker Compose
- OpenAI API ключ (для ИИ-ассистента)

## Быстрый запуск

```bash
# 1. Скопируйте .env.example в .env
cp .env.example .env

# 2. Впишите ваш OpenAI API ключ в .env
# OPENAI_API_KEY=sk-ваш-ключ

# 3. Запустите одной командой
docker compose up --build
```

Приложение: `http://localhost:8000`
LangFlow UI: `http://localhost:7860`

## Настройка ИИ-ассистента

1. Откройте LangFlow UI: `http://localhost:7860`
2. Найдите поток **CyberDoc Chatbot**
3. Нажмите на узел **Language Model**
4. Введите ваш OpenAI API ключ
5. Сохраните поток

После этого чат на `http://localhost:8000/chat` начнет отвечать.

## Локальный запуск (без Docker)

```bash
# Запустить LangFlow
docker run -d --name langflow -p 7860:7860 \
  -e LANGFLOW_AUTO_LOGIN=true \
  -e LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true \
  langflowai/langflow:latest

# Запустить backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Переменные окружения

| Переменная | Описание |
| --- | --- |
| `LANGFLOW_FLOW_ID` | Идентификатор потока в LangFlow |
| `LANGFLOW_API_KEY` | Ключ доступа к LangFlow API |
| `OPENAI_API_KEY` | Ключ OpenAI для работы ИИ-ассистента |

## Структура проекта

```
CyberDoc/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── routers/
│       │   ├── chat.py
│       │   └── tools.py
│       └── services/
│           ├── langflow_client.py
│           ├── page_analyzer.py
│           ├── port_scanner.py
│           └── ssl_checker.py
├── frontend/
│   ├── index.html
│   ├── chat.html
│   ├── tools.html
│   ├── css/style.css
│   └── js/
│       ├── chat.js
│       └── tools.js
├── generate_docx.py
└── doc_images/
```

## Стек технологий

- **Backend**: Python 3.12, FastAPI, Uvicorn, httpx, BeautifulSoup4
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **ИИ**: LangFlow + OpenAI (gpt-4o-mini)
- **Инфраструктура**: Docker, Docker Compose
