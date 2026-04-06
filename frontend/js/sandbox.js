(() => {
    "use strict";

    let editor = null;
    let decorations = [];
    const langMap = {
        python: "python",
        javascript: "javascript",
        php: "php",
        java: "java",
        go: "go",
        html: "html",
    };

    require.config({
        paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" },
    });

    require(["vs/editor/editor.main"], function () {
        monaco.editor.defineTheme("cyberdoc", {
            base: "vs-dark",
            inherit: true,
            rules: [],
            colors: {
                "editor.background": "#1A1A1A",
                "editor.foreground": "#E0E0E0",
                "editorLineNumber.foreground": "#555",
                "editorLineNumber.activeForeground": "#FFDD2D",
                "editor.selectionBackground": "#FFDD2D33",
                "editor.lineHighlightBackground": "#FFFFFF08",
                "editorCursor.foreground": "#FFDD2D",
            },
        });

        const sample =
            'from flask import Flask, request\n\napp = Flask(__name__)\n\n@app.route("/search")\ndef search():\n    query = request.args.get("q", "")\n    return f"<h1>Результаты: {query}</h1>"\n';

        editor = monaco.editor.create(document.getElementById("monaco-editor"), {
            value: sample,
            language: "python",
            theme: "cyberdoc",
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: false },
            lineNumbers: "on",
            renderLineHighlight: "line",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 16, bottom: 16 },
            wordWrap: "on",
        });
    });

    document.getElementById("lang-select").addEventListener("change", function () {
        if (editor) {
            monaco.editor.setModelLanguage(editor.getModel(), langMap[this.value] || "plaintext");
        }
    });

    const severityColors = {
        CRITICAL: "#FF4C4C",
        HIGH: "#FF8C00",
        MEDIUM: "#F39C12",
        LOW: "#3498DB",
        INFO: "#6B6B6B",
    };

    const severityBg = {
        CRITICAL: "rgba(255,76,76,0.12)",
        HIGH: "rgba(255,140,0,0.12)",
        MEDIUM: "rgba(243,156,18,0.12)",
        LOW: "rgba(52,152,219,0.12)",
        INFO: "rgba(107,107,107,0.12)",
    };

    function clearResults() {
        decorations = editor ? editor.deltaDecorations(decorations, []) : [];
        document.getElementById("results-list").innerHTML = "";
        document.getElementById("results-summary").style.display = "none";
        document.getElementById("vuln-counter").textContent = "";
    }

    async function runAnalysis() {
        if (!editor) return;
        const code = editor.getValue().trim();
        if (!code) return;

        const lang = document.getElementById("lang-select").value;
        const btn = document.getElementById("analyze-btn");

        clearResults();
        document.getElementById("results-empty").style.display = "none";
        document.getElementById("results-loading").style.display = "flex";
        btn.disabled = true;

        try {
            const resp = await fetch("/api/sandbox/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, language: lang }),
            });
            const data = await resp.json();
            renderResults(data);
        } catch (e) {
            document.getElementById("results-summary").style.display = "block";
            document.getElementById("results-summary").innerHTML =
                '<div class="summary-error">Ошибка соединения: ' + escapeHtml(e.message) + "</div>";
        } finally {
            document.getElementById("results-loading").style.display = "none";
            btn.disabled = false;
        }
    }

    function renderResults(data) {
        const vulns = data.vulnerabilities || [];
        const summary = data.summary || "";
        const listEl = document.getElementById("results-list");
        const summaryEl = document.getElementById("results-summary");
        const counterEl = document.getElementById("vuln-counter");

        if (summary) {
            summaryEl.style.display = "block";
            summaryEl.innerHTML = '<p class="summary-text">' + escapeHtml(summary) + "</p>";
        }

        counterEl.textContent = vulns.length
            ? vulns.length + " " + pluralize(vulns.length)
            : "Чисто";
        counterEl.className = "vuln-counter" + (vulns.length ? " has-vulns" : " clean");

        if (!vulns.length) {
            listEl.innerHTML =
                '<div class="sandbox-results-empty"><p>Уязвимостей не обнаружено</p></div>';
            return;
        }

        const newDecorations = [];
        vulns.forEach((v, i) => {
            const card = document.createElement("div");
            card.className = "vuln-card";
            card.innerHTML =
                '<div class="vuln-card-header">' +
                '<span class="vuln-sev" style="background:' + severityBg[v.severity] +
                ";color:" + severityColors[v.severity] + '">' + v.severity + "</span>" +
                '<span class="vuln-line-badge">строка ' + v.line + "</span>" +
                "</div>" +
                '<div class="vuln-title">' + escapeHtml(v.title) + "</div>" +
                '<div class="vuln-desc">' + escapeHtml(v.description) + "</div>" +
                '<div class="vuln-fix"><strong>Исправление:</strong> ' +
                escapeHtml(v.fix) + "</div>";

            card.addEventListener("click", function () {
                if (editor && v.line) {
                    editor.revealLineInCenter(v.line);
                    editor.setPosition({ lineNumber: v.line, column: 1 });
                    editor.focus();
                }
            });

            listEl.appendChild(card);

            if (v.line && editor) {
                newDecorations.push({
                    range: new monaco.Range(v.line, 1, v.line, 1),
                    options: {
                        isWholeLine: true,
                        className: "vuln-line-highlight-" + v.severity.toLowerCase(),
                        glyphMarginClassName: "vuln-glyph-" + v.severity.toLowerCase(),
                        overviewRuler: {
                            color: severityColors[v.severity],
                            position: monaco.editor.OverviewRulerLane.Full,
                        },
                    },
                });
            }
        });

        if (editor) {
            decorations = editor.deltaDecorations(decorations, newDecorations);
        }
    }

    function pluralize(n) {
        const mod = n % 10;
        const mod100 = n % 100;
        if (mod === 1 && mod100 !== 11) return "уязвимость";
        if (mod >= 2 && mod <= 4 && (mod100 < 10 || mod100 >= 20)) return "уязвимости";
        return "уязвимостей";
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    window.runAnalysis = runAnalysis;
})();
