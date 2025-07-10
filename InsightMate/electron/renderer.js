const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');
const marked = require('marked');

const input = document.getElementById('input');
const messagesDiv = document.getElementById('messages');
const reminderDiv = document.getElementById('reminder-list');
const taskDiv = document.getElementById('task-list');
const memoryDiv = document.getElementById('memory-list');
const logPath = path.join(require('os').homedir(), 'InsightMate', 'logs');
if (!fs.existsSync(logPath)) fs.mkdirSync(logPath, { recursive: true });
const logFile = path.join(logPath, 'chatlog.txt');

function addMessage(sender, text) {
  const div = document.createElement('div');
  div.classList.add('message', sender === 'You' ? 'you' : 'assistant');
  div.innerHTML = `<strong>${sender}:</strong> ` + marked.parse(text);
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  fs.appendFileSync(logFile, `${sender}: ${text}\n`);
}

function renderReminders(items) {
  reminderDiv.innerHTML = '';
  items.forEach(r => {
    const d = document.createElement('div');
    d.className = 'reminder-item';
    d.textContent = `${r.time} - ${r.text}`;
    reminderDiv.appendChild(d);
  });
}

function renderTasks(items) {
  taskDiv.innerHTML = '';
  items.forEach(t => {
    const d = document.createElement('div');
    d.className = 'reminder-item';
    d.textContent = `${t.schedule} - ${t.description}`;
    taskDiv.appendChild(d);
  });
}

function renderMemory(items) {
  memoryDiv.innerHTML = '';
  items.forEach(m => {
    const d = document.createElement('div');
    d.className = 'reminder-item';
    d.textContent = `${m.sender}: ${m.text}`;
    memoryDiv.appendChild(d);
  });
}

function fetchReminders() {
  fetch('http://localhost:5000/reminders')
    .then(res => res.json())
    .then(data => renderReminders(data.reminders || []))
    .catch(() => {});

  fetch('http://localhost:5000/tasks')
    .then(res => res.json())
    .then(data => renderTasks(data.tasks || []))
    .catch(() => {});

  fetch('http://localhost:5000/memory')
    .then(res => res.json())
    .then(data => renderMemory(data.messages || []))
    .catch(() => {});
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
    .catch(err => addMessage('Error', err.toString()))
    .finally(fetchReminders);
}

fetchReminders();
