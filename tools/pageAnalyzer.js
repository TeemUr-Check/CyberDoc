const axios = require('axios');
const cheerio = require('cheerio');
const beautify = require('js-beautify').html;

async function analyze(url) {
    try {
        const report = {
            vulnerabilities: [],
            data: ""
        };

        // 1. Основной запрос для получения кода и заголовков
        const response = await axios.get(url, {
            timeout: 10000,
            headers: { 'User-Agent': 'CyberDoc-Scanner/2.0' }
        });

        const $ = cheerio.load(response.data);
        const headers = response.headers;

        // --- АКТИВНЫЙ ТЕСТ: Проверка на Open Redirect ---
        try {
            const redirectTest = await axios.get(`${url}/?url=https://evil.com`, { maxRedirects: 0, validateStatus: null });
            if (redirectTest.status === 301 || redirectTest.status === 302) {
                report.vulnerabilities.push("[HIGH] Потенциальный Open Redirect: сервер обрабатывает внешние редиректы через параметры.");
            }
        } catch (e) {}

        // --- АКТИВНЫЙ ТЕСТ: Проверка на XSS в параметрах (Фаззинг) ---
        const xssPayload = "<script>alert(1)</script>";
        try {
            const xssTest = await axios.get(`${url}/?search=${encodeURIComponent(xssPayload)}`);
            if (xssTest.data.includes(xssPayload)) {
                report.vulnerabilities.push("[CRITICAL] Отраженная XSS: полезная нагрузка возвращается в теле ответа без фильтрации.");
            }
        } catch (e) {}

        // --- ПАССИВНЫЙ АНАЛИЗ DOM ---
        
        // Поиск форм без CSRF-защиты
        $('form').each((i, el) => {
            const hasCsrf = $(el).find('input[name*="csrf"], input[name*="token"]').length > 0;
            if (!hasCsrf && $(el).attr('method')?.toUpperCase() === 'POST') {
                report.vulnerabilities.push(`[MEDIUM] Форма обнаружена без видимого CSRF-токена: ${$(el).attr('action') || 'current page'}`);
            }
        });

        // Проверка заголовков (Безопасность транспорта)
        if (!headers['strict-transport-security']) {
            report.vulnerabilities.push("[LOW] Отсутствует HSTS заголовок: риск перехвата трафика (MITM).");
        }
        
        if (headers['server']) {
            report.vulnerabilities.push(`[INFO] Сервер раскрывает свою версию: ${headers['server']}`);
        }

        // Поиск чувствительных файлов в путях (Active Path Discovery)
        const commonPaths = ['/.env', '/.git/config', '/wp-config.php'];
        for (const path of commonPaths) {
            try {
                const check = await axios.head(`${new URL(url).origin}${path}`, { validateStatus: null });
                if (check.status === 200) {
                    report.vulnerabilities.push(`[CRITICAL] Чувствительный файл доступен: ${path}`);
                }
            } catch (e) {}
        }

        // Форматирование исходного кода
        report.data = beautify(response.data, { indent_size: 4 });

        return {
            success: true,
            vulnerabilities: report.vulnerabilities,
            data: report.data
        };

    } catch (error) {
        throw new Error(`Ошибка при активном сканировании: ${error.message}`);
    }
}

module.exports = { analyze };