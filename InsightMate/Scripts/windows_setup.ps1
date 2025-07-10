# Windows setup script for InsightMate
# Creates Python venv, installs requirements and launches the backend server.

$ErrorActionPreference = 'Stop'

# Path to the venv inside the Scripts folder
$venvPath = Join-Path $PSScriptRoot 'venv'

if (-Not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv $venvPath
}

$pip = Join-Path $venvPath 'Scripts' 'pip.exe'
Write-Host "Installing Python dependencies..."
& $pip install -r (Join-Path $PSScriptRoot 'requirements.txt')

# Download the local Llama 3 model if Ollama is available
if (Get-Command 'ollama' -ErrorAction SilentlyContinue) {
    Write-Host "Downloading Llama 3 model via Ollama..."
    ollama pull llama3
} else {
    Write-Warning "Ollama is not installed. Install it from https://ollama.ai/ to run Llama 3 locally."
}

$pythonExe = Join-Path $venvPath 'Scripts' 'python.exe'

Write-Host "Starting InsightMate server..."
& $pythonExe ai_server.py
