document.addEventListener('DOMContentLoaded', function () {
const chatInput = document.querySelector('.chat-input');
const sendBtn = document.querySelector('.send-btn');
const chatContainer = document.querySelector('.chat-container');

// 送出按鈕點擊或按 Enter
sendBtn.addEventListener('click', handleSend);
chatInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        handleSend();
    }
});

function handleSend() {
    const message = chatInput.value.trim();
    if (message === '') return;

    addMessage('user', message); // 插入使用者訊息
    chatInput.value = ''; // 清空輸入欄

    // 模擬 AI 回應
    setTimeout(() => {
        const aiReply = generateFakeAIReply(message);
        addMessage('ai', aiReply);
    }, 1000);
}

// 插入訊息到畫面上
function addMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(role === 'ai' ? 'bot-message' : 'user-message');

    if (role === 'ai') {
        const avatar = document.createElement('img');
        avatar.src = '../static/image/avatars_nbg.jpg';
        avatar.alt = '小江解';
        avatar.classList.add('avatar');
        messageDiv.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');

    const p = document.createElement('p');
    p.classList.add('message-text');
    p.textContent = text;

    bubble.appendChild(p);
    messageDiv.appendChild(bubble);
    chatContainer.appendChild(messageDiv);

    // 自動捲到底
    chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 模擬 AI 回應（可換成真 API）
    function generateFakeAIReply(userInput) {
        return `你剛剛問了：「${userInput}」，這是模擬回覆喔～`;
    }
});
