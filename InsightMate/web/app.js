const messagesDiv = document.getElementById('messages');
const reminderDiv = document.getElementById('reminder-list');
const taskDiv = document.getElementById('task-list');
const memoryDiv = document.getElementById('memory-list');
const reminderToggle = document.getElementById('reminder-toggle');
const taskToggle = document.getElementById('task-toggle');
const memoryToggle = document.getElementById('memory-toggle');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = new bootstrap.Modal(document.getElementById('settings-modal'));
const themeSelect = document.getElementById('theme-select');
const modelSelect = document.getElementById('model-select');


function processThought(text, durationSec) {
  const start = text.indexOf('Thinking...');
  const end = text.indexOf('...done thinking');
  if (start !== -1 && end !== -1 && end > start) {
    const thought = text.slice(start + 11, end).trim();
    let restStart = end + 16;
    if (text[restStart] === '.') restStart += 1;
    const rest = text.slice(restStart).trim();
    const summary = `Thought for ${durationSec.toFixed(1)} seconds`;
    return `<details><summary>${summary}</summary>\n${thought}\n</details>\n\n${rest}`;
  }
  return text;
}

function addMessage(sender, text) {
  const div = document.createElement('div');
  div.classList.add('message', sender === 'You' ? 'you' : 'assistant');
  const span = document.createElement('span');
  div.innerHTML = `<strong>${sender}:</strong> `;
  div.appendChild(span);
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  span.innerHTML = marked.parse(text);
  const log = JSON.parse(localStorage.getItem('chatlog') || '[]');
  log.push({sender, text});
  localStorage.setItem('chatlog', JSON.stringify(log));
  return div;
}

function renderList(container, items, formatter) {
  container.innerHTML = '';
  items.forEach(i => {
    const d = document.createElement('div');
    d.className = 'small mb-1';
    d.textContent = formatter(i);
    container.appendChild(d);
  });
}

function fetchData() {
  fetch('/reminders').then(r => r.json()).then(d => {
    renderList(reminderDiv, d.reminders || [], r => `${r.time} - ${r.text}`);
  }).catch(() => {});
  fetch('/tasks').then(r => r.json()).then(d => {
    renderList(taskDiv, d.tasks || [], t => `${t.schedule} - ${t.description}`);
  }).catch(() => {});
  fetch('/memory').then(r => r.json()).then(d => {
    renderList(memoryDiv, d.messages || [], m => `${m.sender}: ${m.text}`);
  }).catch(() => {});
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

function saveSettings() {
  localStorage.setItem('theme', themeSelect.value);
  localStorage.setItem('model', modelSelect.value);
  applyTheme(themeSelect.value);
}

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addMessage('You', text);
  input.value = '';
  const placeholder = addMessage('Assistant', '...');
  const start = Date.now();
  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: text, model: localStorage.getItem('model') || 'gpt-4o'})
  })
  .then(res => res.json())
  .then(data => {
    messagesDiv.removeChild(placeholder);
    const duration = (Date.now() - start) / 1000;
    const msg = processThought(data.reply, duration);
    addMessage('Assistant', msg);
  })
  .catch(err => {
    messagesDiv.removeChild(placeholder);
    addMessage('Error', err.toString());
  })
  .finally(fetchData);
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
settingsBtn.addEventListener('click', () => settingsModal.show());
document.getElementById('save-settings').addEventListener('click', saveSettings);

loadSettings();
fetchData();
