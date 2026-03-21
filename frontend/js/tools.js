(() => {
    "use strict";

    const $ = (sel) => document.querySelector(sel);

    const TOOLS = {
        "page-analyzer": {
            title: "Анализ страницы",
            desc: "Сканирование веб-страницы на уязвимости: XSS, CSRF, Open Redirect, утечка конфигураций.",
            placeholder: "Введите URL (например, https://example.com)",
            resultLabel: "Исходный код",
        },
        "port-scanner": {
            title: "Сканер портов",
            desc: "Проверка открытых TCP-портов на указанном хосте. Сканируются популярные сервисные порты.",
            placeholder: "Введите хост (например, scanme.nmap.org)",
            resultLabel: "Результат сканирования",
        },
        "ssl-checker": {
            title: "Проверка SSL",
            desc: "Анализ SSL/TLS-сертификата: срок действия, издатель, цепочка доверия, отпечаток.",
            placeholder: "Введите хост (например, google.com)",
            resultLabel: "Информация о сертификате",
        },
        "dns-recon": {
            title: "DNS-разведка",
            desc: "Получение DNS-записей домена: A, AAAA, MX, NS. Проверка SPF и DMARC.",
            placeholder: "Введите домен (например, example.com)",
            resultLabel: "DNS-записи",
        },
        "subdomain-scanner": {
            title: "Поиск поддоменов",
            desc: "Обнаружение поддоменов перебором по словарю (60+ популярных имен).",
            placeholder: "Введите домен (например, example.com)",
            resultLabel: "Найденные поддомены",
        },
        "dir-scanner": {
            title: "Сканер директорий",
            desc: "Проверка доступности скрытых путей, панелей администратора, конфигурационных файлов.",
            placeholder: "Введите URL (например, https://example.com)",
            resultLabel: "Доступные пути",
        },
    };

    let selectedTool = "page-analyzer";

    function selectTool(el) {
        const tool = el.dataset.tool;
        if (!tool || !TOOLS[tool]) return;

        selectedTool = tool;
        const meta = TOOLS[tool];

        document.querySelectorAll(".tool-nav-item").forEach((i) => i.classList.remove("active"));
        el.classList.add("active");

        $("#tool-title").textContent = meta.title;
        $("#tool-desc").textContent = meta.desc;
        $("#tool-input").placeholder = meta.placeholder;
        $("#main-label").textContent = meta.resultLabel;

        $("#result-vulns").classList.remove("visible");
        $("#result-main").classList.remove("visible");
    }

    function extractHost(value) {
        try {
            if (value.includes("://")) return new URL(value).hostname;
            return value.split("/")[0];
        } catch {
            return value;
        }
    }

    function colorizeVuln(text) {
        const levels = {
            CRITICAL: "vuln-critical",
            HIGH: "vuln-high",
            MEDIUM: "vuln-medium",
            LOW: "vuln-low",
            INFO: "vuln-info",
        };

        return text
            .split("\n")
            .map((line) => {
                for (const [key, cls] of Object.entries(levels)) {
                    if (line.includes(`[${key}]`)) {
                        return `<span class="${cls}">${escapeHtml(line)}</span>`;
                    }
                }
                return escapeHtml(line);
            })
            .join("\n");
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDnsResult(data) {
        let out = `Domain: ${data.domain}\n\n`;
        const records = data.records || {};
        for (const [type, values] of Object.entries(records)) {
            out += `${type} records:\n`;
            if (Array.isArray(values)) {
                values.forEach((v) => (out += `  ${v}\n`));
            } else {
                out += `  ${values}\n`;
            }
            out += "\n";
        }
        const sec = data.security || {};
        out += `Security:\n`;
        out += `  SPF:   ${sec.spf || "N/A"}\n`;
        out += `  DMARC: ${sec.dmarc || "N/A"}\n`;
        return out;
    }

    function formatSubdomainResult(data) {
        let out = `Domain: ${data.domain}\n`;
        out += `Checked: ${data.total_checked} | Found: ${data.found}\n\n`;
        if (data.subdomains && data.subdomains.length > 0) {
            data.subdomains.forEach((s) => {
                out += `[FOUND] ${s.subdomain} -> ${s.ips.join(", ")}\n`;
            });
        } else {
            out += "No subdomains found.\n";
        }
        return out;
    }

    function formatDirResult(data) {
        let out = `Target: ${data.url}\n`;
        out += `Checked: ${data.total_checked} | Found: ${data.found}\n\n`;
        if (data.paths && data.paths.length > 0) {
            data.paths.forEach((p) => {
                out += `[${p.severity}] ${p.path} (HTTP ${p.status})\n`;
            });
        } else {
            out += "No accessible paths found.\n";
        }
        return out;
    }

    async function executeTool() {
        let val = $("#tool-input").value.trim();
        if (!val) return;

        const btn = $("#run-btn");
        const vulnsSection = $("#result-vulns");
        const mainSection = $("#result-main");
        const vulnsOutput = $("#vulns-output");
        const mainOutput = $("#main-output");

        const hostTools = ["port-scanner", "ssl-checker", "dns-recon", "subdomain-scanner"];
        if (hostTools.includes(selectedTool)) {
            val = extractHost(val);
        }

        vulnsSection.classList.remove("visible");
        mainSection.classList.add("visible");
        mainOutput.textContent = "";
        mainOutput.className = "";
        mainOutput.innerHTML = '<span class="loading-spinner"></span> Выполняется анализ...';
        btn.disabled = true;

        try {
            const resp = await fetch("/api/tool", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tool_name: selectedTool, params: val }),
            });
            const result = await resp.json();

            if (resp.ok) {
                if (selectedTool === "page-analyzer") {
                    vulnsSection.classList.add("visible");
                    const vulns = result.vulnerabilities || [];
                    const vulnText = vulns.length > 0
                        ? vulns.join("\n")
                        : "Уязвимостей не обнаружено.";
                    vulnsOutput.innerHTML = colorizeVuln(vulnText);
                    mainOutput.textContent = result.source_code || "";
                    hljs.highlightElement(mainOutput);
                } else if (selectedTool === "port-scanner") {
                    const ports = Array.isArray(result) ? result : [];
                    mainOutput.textContent = ports.length > 0
                        ? ports.map((p) => `[${p.status}] Port ${p.port}: ${p.service}`).join("\n")
                        : "Открытых портов не обнаружено.";
                } else if (selectedTool === "ssl-checker") {
                    if (result.error) {
                        mainOutput.textContent = "Error: " + result.error;
                    } else {
                        const lines = [
                            `Valid:          ${result.valid ? "Yes" : "No"}`,
                            `Subject:        ${result.subject || "N/A"}`,
                            `Issuer:         ${result.issuer || "N/A"}`,
                            `Valid from:     ${result.valid_from || "N/A"}`,
                            `Valid to:       ${result.valid_to || "N/A"}`,
                            `Days remaining: ${result.days_remaining ?? "N/A"}`,
                            `Fingerprint:    ${result.fingerprint || "N/A"}`,
                        ];
                        mainOutput.textContent = lines.join("\n");
                    }
                } else if (selectedTool === "dns-recon") {
                    mainOutput.textContent = formatDnsResult(result);
                } else if (selectedTool === "subdomain-scanner") {
                    mainOutput.textContent = formatSubdomainResult(result);
                } else if (selectedTool === "dir-scanner") {
                    vulnsSection.classList.add("visible");
                    const paths = result.paths || [];
                    const criticals = paths.filter((p) =>
                        ["CRITICAL", "HIGH"].includes(p.severity)
                    );
                    if (criticals.length > 0) {
                        vulnsOutput.innerHTML = colorizeVuln(
                            criticals.map((p) => `[${p.severity}] ${p.path} (HTTP ${p.status})`).join("\n")
                        );
                    } else {
                        vulnsOutput.textContent = "Критических находок нет.";
                    }
                    mainOutput.textContent = formatDirResult(result);
                }
            } else {
                mainOutput.textContent = "Error: " + (result.detail || "Unknown error");
            }
        } catch (e) {
            mainOutput.textContent = "Connection error: " + e.message;
        } finally {
            btn.disabled = false;
        }
    }

    function copyResult(elementId) {
        const el = document.getElementById(elementId);
        if (!el) return;
        navigator.clipboard.writeText(el.textContent).then(() => {
            const btn = el.closest(".result-card").querySelector(".copy-btn");
            if (btn) {
                btn.textContent = "Скопировано";
                setTimeout(() => (btn.textContent = "Копировать"), 2000);
            }
        });
    }

    window.selectTool = selectTool;
    window.executeTool = executeTool;
    window.copyResult = copyResult;
})();
