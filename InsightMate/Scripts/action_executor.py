import os
import subprocess

def execute(command: str) -> str:
    cmd = command.lower()
    if 'notepad' in cmd:
        os.startfile('notepad.exe')
        return 'Opening Notepad.'
    if 'spotify' in cmd:
        subprocess.Popen(['spotify'])
        return 'Opening Spotify.'
    if 'open' in cmd:
        program = cmd.split('open',1)[1].strip()
        subprocess.Popen(program, shell=True)
        return f'Opening {program}.'
    return 'Action not recognized.'
