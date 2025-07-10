@echo off
python -m venv venv
venv\Scripts\pip install -r Scripts\requirements.txt
start "ChatServer" venv\Scripts\python Scripts\chat_server.py
cd electron
npm install
npm start
