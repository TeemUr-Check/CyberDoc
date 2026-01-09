const express = require('express');
const path = require('path');
const axios = require('axios');
const { runTool } = require('./tools/index'); // Импорт менеджера инструментов

const app = express();
const PORT = 3000;

// Конфигурация твоего Langflow
const CONFIG = {
    apiUrl: 'http://127.0.0.1:7860/api/v1/run/3ab98786-bcff-49e7-a63c-902620357494',
    apiKey: 'sk-dJApwYJW0oL4BtqVKxI2PRQ2ZnJDTlsGEKnUJqHhxkM'
};

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

/**
 * ЭНДПОИНТ ЧАТА (Интеграция с Langflow)
 */
app.post('/api/chat', async (req, res) => {
    try {
        const { message, sessionId } = req.body;
        
        // Защита: если сессия не пришла, создаем временную
        const activeSession = sessionId || `temp_${Date.now()}`;
        
        console.log(`[LOG] Отправка: "${message.substring(0, 30)}..." | Session: ${activeSession}`);

        const response = await axios.post(CONFIG.apiUrl, {
            input_value: message,
            output_type: "chat",
            input_type: "chat",
            session_id: activeSession
        }, {
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CONFIG.apiKey}`,
                'x-api-key': CONFIG.apiKey 
            },
            timeout: 20000 
        });

        // ГЛУБОКОЕ ИЗВЛЕЧЕНИЕ ТЕКСТА (твоя логика из Langflow 1.0+)
        const resultData = response.data?.outputs?.[0]?.outputs?.[0]?.results;
        
        const reply = resultData?.message?.text || 
                      resultData?.message?.data?.text || 
                      "Ответ получен, но текст не найден в структуре JSON.";
        
        res.json({ reply });

    } catch (e) {
        console.error("--- ОШИБКА ЧАТА ---");
        if (e.response) {
            console.error(`Статус: ${e.response.status}`);
            console.error("Данные:", JSON.stringify(e.response.data, null, 2));
        } else {
            console.error("Сеть/Таймаут:", e.message);
        }
        res.status(500).json({ reply: "⚠️ Ошибка связи. Убедитесь, что Langflow запущен." });
    }
});

/**
 * ЭНДПОИНТ ИНСТРУМЕНТОВ (Модульная архитектура)
 */
app.post('/api/tool', async (req, res) => {
    const { toolName, params } = req.body;
    
    if (!toolName) {
        return res.status(400).json({ success: false, error: "Не указано имя инструмента" });
    }

    try {
        // Вызываем логику из папки tools через менеджер
        const result = await runTool(toolName, params);
        res.json(result);
    } catch (error) {
        console.error(`Ошибка инструмента [${toolName}]:`, error.message);
        res.status(500).json({ 
            success: false, 
            error: error.message || "Ошибка сервера при выполнении инструмента" 
        });
    }
});

// Запуск без endl (как ты просил)
app.listen(PORT, () => process.stdout.write(`CyberDoc Pro: http://localhost:${PORT}`));