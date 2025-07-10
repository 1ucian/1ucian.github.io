const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let tray = null;
let win = null;
let serverProcess = null;

function startServer() {
  if (serverProcess) return;
  serverProcess = spawn('python', [path.join(__dirname, '..', 'Scripts', 'chat_server.py')], { stdio: 'ignore' });
}

function createWindow() {
  win = new BrowserWindow({
    width: 400,
    height: 500,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: true, contextIsolation: false }
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  startServer();
  tray = new Tray(path.join(__dirname, 'icon.png'));
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open Chat', click: () => { if (!win) createWindow(); else win.show(); } },
    { label: 'Quit', click: () => { app.quit(); } }
  ]);
  tray.setToolTip('InsightMate');
  tray.setContextMenu(contextMenu);
  createWindow();
});

app.on('window-all-closed', (e) => {
  e.preventDefault();
});

app.on('before-quit', () => {
  if (serverProcess) serverProcess.kill();
});
