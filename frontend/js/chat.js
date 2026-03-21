(() => {
    "use strict";

    const STORAGE_KEY = "cyberdoc_chats";
    let chats = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    let currentChatId = null;

    marked.setOptions({ gfm: true, breaks: true });

    const $ = (sel) => document.querySelector(sel);
    const messagesEl = $("#chat-messages");
    const emptyEl = $("#chat-empty");
    const inputEl = $("#chat-input");
    const listEl = $("#chat-list");

    function save() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    }

    function renderChatList() {
        listEl.innerHTML = "";
        chats.forEach((chat) => {
            const item = document.createElement("div");
            item.className = "chat-item" + (chat.id === currentChatId ? " active" : "");
            item.innerHTML = `
                <span>${escapeHtml(chat.title)}</span>
                <button class="chat-delete" title="Удалить">&times;</button>
            `;
            item.addEventListener("click", (e) => {
                if (e.target.closest(".chat-delete")) {
                    deleteChat(chat.id);
                    return;
                }
                loadChat(chat.id);
            });
            listEl.appendChild(item);
        });
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function createNewChat() {
        const id = "sess_" + Date.now();
        chats.unshift({ id, title: "Новый диалог", history: [] });
        save();
        loadChat(id);
    }

    function deleteChat(id) {
        chats = chats.filter((c) => c.id !== id);
        save();
        if (currentChatId === id) {
            currentChatId = null;
            messagesEl.innerHTML = "";
            showEmpty(true);
        }
        renderChatList();
    }

    function loadChat(id) {
        currentChatId = id;
        const chat = chats.find((c) => c.id === id);
        messagesEl.innerHTML = "";
        showEmpty(chat.history.length === 0);

        chat.history.forEach((m) => appendMessage(m.role, m.text, false));
        renderChatList();
        scrollBottom();
    }

    function showEmpty(show) {
        if (emptyEl) emptyEl.style.display = show ? "flex" : "none";
    }

    function appendMessage(role, text, animate = true) {
        showEmpty(false);
        const msg = document.createElement("div");
        msg.className = "message " + role;
        if (!animate) msg.style.animation = "none";

        if (role === "ai") {
            msg.innerHTML = `
                <div class="avatar">C</div>
                <div class="message-content">${marked.parse(text)}</div>
            `;
        } else {
            msg.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
        }

        messagesEl.appendChild(msg);
        msg.querySelectorAll("pre code").forEach((block) => {
            if (!block.dataset.highlighted) hljs.highlightElement(block);
        });
    }

    function showTyping() {
        const id = "typing_" + Date.now();
        const el = document.createElement("div");
        el.className = "message ai";
        el.id = id;
        el.innerHTML = `
            <div class="avatar">C</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesEl.appendChild(el);
        scrollBottom();
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function handleSend() {
        const text = inputEl.value.trim();
        if (!text) return;
        if (!currentChatId) createNewChat();

        appendMessage("user", text);
        inputEl.value = "";
        inputEl.style.height = "auto";
        scrollBottom();

        const typingId = showTyping();

        try {
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, session_id: currentChatId }),
            });
            const data = await resp.json();
            removeTyping(typingId);
            appendMessage("ai", data.reply);

            const chat = chats.find((c) => c.id === currentChatId);
            chat.history.push(
                { role: "user", text },
                { role: "ai", text: data.reply }
            );
            if (chat.title === "Новый диалог") {
                chat.title = text.substring(0, 35);
            }
            save();
            renderChatList();
        } catch {
            removeTyping(typingId);
            appendMessage("ai", "Не удалось получить ответ. Проверьте подключение.");
        }
        scrollBottom();
    }

    inputEl.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
    });

    inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    window.createNewChat = createNewChat;
    window.handleSend = handleSend;

    renderChatList();
    showEmpty(true);
})();
