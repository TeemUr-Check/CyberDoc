(() => {
    "use strict";

    const PROGRESS_KEY = "cyberdoc_ctf_progress";
    let missions = [];
    let currentMission = null;
    let hintIndex = 0;
    let progress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || "{}");

    const $ = (sel) => document.querySelector(sel);

    async function init() {
        try {
            const resp = await fetch("/api/ctf/missions");
            missions = await resp.json();
            renderMissionList();
            renderStats();
        } catch (e) {
            $("#mission-list").innerHTML =
                '<p style="padding:16px;color:var(--text-muted)">Ошибка загрузки миссий</p>';
        }
    }

    function saveProgress() {
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
    }

    function getTotalScore() {
        let total = 0;
        for (const id in progress) {
            total += progress[id].score || 0;
        }
        return total;
    }

    function renderStats() {
        const completed = Object.values(progress).filter((p) => p.passed).length;
        const total = missions.length;
        const score = getTotalScore();
        $("#ctf-score").textContent = score + " очков";
        $("#ctf-stats").innerHTML =
            '<div class="stat-cards">' +
            '<div class="stat-card"><div class="stat-num">' + total + '</div><div class="stat-label">Миссий</div></div>' +
            '<div class="stat-card"><div class="stat-num">' + completed + '</div><div class="stat-label">Пройдено</div></div>' +
            '<div class="stat-card"><div class="stat-num">' + score + '</div><div class="stat-label">Очков</div></div>' +
            "</div>";
    }

    function renderMissionList() {
        const list = $("#mission-list");
        list.innerHTML = "";
        missions.forEach((m) => {
            const done = progress[m.id] && progress[m.id].passed;
            const card = document.createElement("div");
            card.className = "ctf-mission-card" + (currentMission && currentMission.id === m.id ? " active" : "") + (done ? " completed" : "");
            card.innerHTML =
                '<div class="mission-card-top">' +
                '<span class="difficulty-dot diff-' + m.difficulty + '"></span>' +
                '<span class="mission-card-title">' + escapeHtml(m.title) + "</span>" +
                (done ? '<span class="mission-check">&#10003;</span>' : "") +
                "</div>" +
                '<div class="mission-card-bottom">' +
                '<span class="mission-card-cat">' + escapeHtml(m.category) + "</span>" +
                '<span class="mission-card-pts">' + m.points + " очк.</span>" +
                "</div>";
            card.addEventListener("click", () => loadMission(m.id));
            list.appendChild(card);
        });
    }

    async function loadMission(id) {
        try {
            const resp = await fetch("/api/ctf/mission/" + id);
            const data = await resp.json();
            currentMission = data;
            hintIndex = 0;

            $("#ctf-empty").style.display = "none";
            $("#ctf-mission").style.display = "block";
            $("#mission-title").textContent = data.title;
            $("#mission-desc").textContent = data.description;
            $("#mission-difficulty").textContent = { easy: "Легко", medium: "Средне", hard: "Сложно" }[data.difficulty] || data.difficulty;
            $("#mission-difficulty").className = "difficulty-badge diff-" + data.difficulty;
            $("#mission-category").textContent = data.category;
            $("#mission-points").textContent = data.points + " очков";
            $("#mission-lang").textContent = data.language;
            $("#hint-counter").textContent = "(0/" + data.total_hints + ")";

            const codeEl = $("#mission-code");
            codeEl.textContent = data.code;
            codeEl.className = "language-" + data.language;
            hljs.highlightElement(codeEl);

            $("#answer-input").value = "";
            $("#hint-area").style.display = "none";
            $("#hint-area").innerHTML = "";
            $("#result-area").style.display = "none";

            if (progress[id] && progress[id].answer) {
                $("#answer-input").value = progress[id].answer;
            }

            renderMissionList();
        } catch (e) {
            console.error(e);
        }
    }

    async function submitAnswer() {
        if (!currentMission) return;
        const answer = $("#answer-input").value.trim();
        if (!answer) return;

        const btn = $("#submit-btn");
        btn.disabled = true;
        btn.textContent = "Проверка...";

        try {
            const resp = await fetch("/api/ctf/check", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mission_id: currentMission.id, answer }),
            });
            const data = await resp.json();

            if (data.error) {
                showResult(false, 0, 30, data.error);
                return;
            }

            const scores = data.scores || {};
            const total = data.total || 0;
            const passed = data.passed || false;
            const feedback = data.feedback || "";

            if (passed) {
                const earned = Math.round((total / 30) * currentMission.points);
                const prev = (progress[currentMission.id] || {}).score || 0;
                if (earned > prev) {
                    progress[currentMission.id] = { passed: true, score: earned, answer };
                    saveProgress();
                }
            } else {
                if (!progress[currentMission.id]) {
                    progress[currentMission.id] = { passed: false, score: 0, answer };
                    saveProgress();
                }
            }

            showResult(passed, total, 30, feedback, scores);
            renderStats();
            renderMissionList();
        } catch (e) {
            showResult(false, 0, 30, "Ошибка соединения: " + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = "Отправить ответ";
        }
    }

    function showResult(passed, total, max, feedback, scores) {
        const area = $("#result-area");
        area.style.display = "block";

        const pct = Math.round((total / max) * 100);
        $("#result-header").innerHTML =
            '<div class="result-status ' + (passed ? "passed" : "failed") + '">' +
            (passed ? "&#10003; Миссия пройдена!" : "&#10007; Попробуйте ещё раз") +
            "</div>" +
            '<div class="result-score-main">' + total + " / " + max + " (" + pct + "%)</div>";

        if (scores) {
            $("#result-scores").innerHTML =
                '<div class="score-bars">' +
                scorebar("Определение", scores.identification, 10) +
                scorebar("Объяснение", scores.explanation, 10) +
                scorebar("Исправление", scores.fix, 10) +
                "</div>";
        } else {
            $("#result-scores").innerHTML = "";
        }

        $("#result-feedback").innerHTML = '<p>' + escapeHtml(feedback) + "</p>";
        area.scrollIntoView({ behavior: "smooth" });
    }

    function scorebar(label, val, max) {
        const pct = (val / max) * 100;
        const color = pct >= 70 ? "#2ECC71" : pct >= 40 ? "#F39C12" : "#FF4C4C";
        return (
            '<div class="score-bar-row">' +
            '<span class="score-bar-label">' + label + "</span>" +
            '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + pct + "%;background:" + color + '"></div></div>' +
            '<span class="score-bar-val">' + val + "/" + max + "</span></div>"
        );
    }

    async function requestHint() {
        if (!currentMission) return;
        if (hintIndex >= currentMission.total_hints) return;

        try {
            const resp = await fetch("/api/ctf/hint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mission_id: currentMission.id, hint_index: hintIndex }),
            });
            const data = await resp.json();
            if (data.hint) {
                const area = $("#hint-area");
                area.style.display = "block";
                const hintEl = document.createElement("div");
                hintEl.className = "hint-item";
                hintEl.innerHTML =
                    '<span class="hint-num">Подсказка ' + (hintIndex + 1) + "</span>" +
                    '<p>' + escapeHtml(data.hint) + "</p>";
                area.appendChild(hintEl);
                hintIndex++;
                $("#hint-counter").textContent = "(" + hintIndex + "/" + currentMission.total_hints + ")";
            }
        } catch (e) {
            console.error(e);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str || "";
        return div.innerHTML;
    }

    window.submitAnswer = submitAnswer;
    window.requestHint = requestHint;

    init();
})();
