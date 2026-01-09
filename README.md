Установка и запуск
Клонирование проекта:

Bash

git clone https://github.com/TeemUr-Check/CyberDoc.git
cd CyberDoc
Установка необходимых библиотек:

Bash

npm install
Создание конфигурационного файла: В корневой папке необходимо создать файл .env и добавить в него параметры для работы с Langflow (ключи предоставляются при настройке нейросетевого потока):

Фрагмент кода

PORT=3000
LANGFLOW_API_KEY=your_key_here
Запуск приложения:

Bash

node server.js
