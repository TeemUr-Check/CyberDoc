const pageAnalyzer = require('./pageAnalyzer');
const networkTools = require('./networkTools');

async function runTool(toolName, params) {
    switch (toolName) {
        case 'page-analyzer':
            return await pageAnalyzer.analyze(params);
        case 'port-scanner':
            return await networkTools.scanPorts(params);
        case 'ssl-checker':
            return await networkTools.checkSSL(params);
        default:
            throw new Error(`Инструмент ${toolName} не найден`);
    }
}

module.exports = { runTool };