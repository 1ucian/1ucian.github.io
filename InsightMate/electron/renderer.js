const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');
const marked = require('marked');

const input = document.getElementById('input');
const messagesDiv = document.getElementById('messages');
const logPath = path.join(require('os').homedir(), 'InsightMate', 'logs');
if (!fs.existsSync(logPath)) fs.mkdirSync(logPath, { recursive: true });
const logFile = path.join(logPath, 'chatlog.txt');

function addMessage(sender, text) {
  const div = document.createElement('div');
  div.innerHTML = `<b>${sender}:</b> ` + marked.parse(text);
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  fs.appendFileSync(logFile, `${sender}: ${text}\n`);
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

document.getElementById('input').addEventListener('input', (e) => {
  e.target.style.height = 'auto';
  e.target.style.height = e.target.scrollHeight + 'px';
});

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addMessage('You', text);
  input.value = '';
  fetch('http://localhost:5000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: text })
  })
    .then(res => res.json())
    .then(data => addMessage('Assistant', data.reply))
    .catch(err => addMessage('Error', err.toString()));
}
