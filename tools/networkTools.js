const net = require('net');
const tls = require('tls');

/**
 * Сканер портов
 */
async function scanPorts(host) {
    if (!host) return [];
    
    // Список портов для быстрой проверки
    const ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 8080];
    const results = [];

    const checkPort = (port) => {
        return new Promise((resolve) => {
            const socket = new net.Socket();
            // Увеличим таймаут до 2.5 сек для надежности
            socket.setTimeout(2500); 

            socket.on('connect', () => {
                results.push({ port, status: 'OPEN', service: getServiceName(port) });
                socket.destroy();
                resolve();
            });

            // Любая ошибка или таймаут — считаем порт закрытым/недоступным
            const finish = () => { socket.destroy(); resolve(); };
            socket.on('timeout', finish);
            socket.on('error', finish);

            socket.connect(port, host);
        });
    };

    // Чтобы не "заспамить" систему, можно запускать пачками или через Promise.all
    await Promise.all(ports.map(p => checkPort(p)));
    return results.sort((a, b) => a.port - b.port);
}

/**
 * Проверка SSL сертификата
 */
async function checkSSL(hostname) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname,
            port: 443,
            method: 'GET',
            rejectUnauthorized: false // Чтобы получить инфо даже о просроченных
        };

        const socket = tls.connect(443, hostname, { servername: hostname }, () => {
            const cert = socket.getPeerCertificate();
            socket.end();

            if (!cert || Object.keys(cert).length === 0) {
                return resolve({ valid: false, error: "Сертификат не найден" });
            }

            const now = new Date();
            const validTo = new Date(cert.valid_to);
            
            resolve({
                valid: socket.authorized,
                subject: cert.subject.CN,
                issuer: cert.issuer.O,
                validFrom: cert.valid_from,
                validTo: cert.valid_to,
                daysRemaining: Math.floor((validTo - now) / (1000 * 60 * 60 * 24)),
                fingerprint: cert.fingerprint
            });
        });

        socket.on('error', (err) => resolve({ valid: false, error: err.message }));
    });
}

function getServiceName(port) {
    const services = { 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 443: 'HTTPS', 3306: 'MySQL', 8080: 'HTTP-Proxy' };
    return services[port] || 'Unknown';
}

module.exports = { scanPorts, checkSSL };