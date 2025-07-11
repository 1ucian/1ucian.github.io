const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');
const marked = require('marked');

const input = document.getElementById('input');
const messagesDiv = document.getElementById('messages');
const reminderDiv = document.getElementById('reminder-list');
const taskDiv = document.getElementById('task-list');
const memoryDiv = document.getElementById('memory-list');
const reminderToggle = document.getElementById('reminder-toggle');
const taskToggle = document.getElementById('task-toggle');
const memoryToggle = document.getElementById('memory-toggle');
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = document.getElementById('settings-modal');
const themeSelect = document.getElementById('theme-select');
const modelSelect = document.getElementById('model-select');
const logPath = path.join(require('os').homedir(), 'InsightMate', 'logs');
if (!fs.existsSync(logPath)) fs.mkdirSync(logPath, { recursive: true });
const logFile = path.join(logPath, 'chatlog.txt');

const TYPE_DELAY = 8; // ms per character

function processThought(text, durationSec) {
  const start = text.indexOf('Thinking...');
  const end = text.indexOf('...done thinking');
  if (start !== -1 && end !== -1 && end > start) {
    const thought = text.slice(start + 11, end).trim();
    const rest = text.slice(end + 16).trim();
    const summary = `Thought for ${durationSec.toFixed(1)} seconds`;
    return `<details><summary>${summary}</summary>\n${thought}\n</details>\n\n${rest}`;
  }
  return text;
}

function addMessage(sender, text, typing = false) {
  const div = document.createElement('div');
  div.classList.add('message', sender === 'You' ? 'you' : 'assistant');
  const span = document.createElement('span');
  div.innerHTML = `<strong>${sender}:</strong> `;
  div.appendChild(span);
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  const logIt = () => fs.appendFileSync(logFile, `${sender}: ${text}\n`);
  if (typing) {
    let i = 0;
    const type = () => {
      if (i < text.length) {
        span.textContent += text[i];
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        i++;
        setTimeout(type, TYPE_DELAY);
      } else {
        span.innerHTML = marked.parse(text);
        logIt();
      }
    };
    type();
  } else {
    span.innerHTML = marked.parse(text);
    logIt();
  }
  return div;
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

function applyTheme(theme) {
  document.body.classList.toggle('light', theme === 'light');
}

reminderToggle.addEventListener('click', () => {
  reminderDiv.classList.toggle('d-none');
});
taskToggle.addEventListener('click', () => {
  taskDiv.classList.toggle('d-none');
});
memoryToggle.addEventListener('click', () => {
  memoryDiv.classList.toggle('d-none');
});

function loadSettings() {
  const theme = localStorage.getItem('theme') || 'dark';
  const model = localStorage.getItem('model') || 'gpt-4o';
  themeSelect.value = theme;
  modelSelect.value = model;
  applyTheme(theme);
}

settingsBtn.addEventListener('click', () => {
  settingsModal.style.display = 'flex';
});

document.getElementById('save-settings').addEventListener('click', () => {
  localStorage.setItem('theme', themeSelect.value);
  localStorage.setItem('model', modelSelect.value);
  applyTheme(themeSelect.value);
  settingsModal.style.display = 'none';
});

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
  const placeholder = addMessage('Assistant', '...', false);
  const start = Date.now();
  fetch('http://localhost:5000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: text, model: localStorage.getItem('model') || 'gpt-4o' })
  })
    .then(res => res.json())
    .then(data => {
      messagesDiv.removeChild(placeholder);
      const duration = (Date.now() - start) / 1000;
      const msg = processThought(data.reply, duration);
      addMessage('Assistant', msg, true);
    })
    .catch(err => {
      messagesDiv.removeChild(placeholder);
      addMessage('Error', err.toString());
    })
    .finally(fetchReminders);
}

loadSettings();
fetchReminders();
