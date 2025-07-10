import os
import sys
import subprocess
import threading
import time
import requests
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("InsightMate")

        self.text_area = ScrolledText(root, state='disabled', width=60, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(root, width=60)
        self.entry.pack(padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.server_proc = None
        self.start_server()

    def start_server(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if self.server_proc is None:
            log_path = os.path.join(script_dir, 'chat_server.log')
            self.log_file = open(log_path, 'w')
            self.server_proc = subprocess.Popen(
                [sys.executable, os.path.join(script_dir, 'chat_server.py')],
                stdout=self.log_file,
                stderr=subprocess.STDOUT
            )
            time.sleep(0.5)
            if self.server_proc.poll() is not None:
                self.add_message(
                    "Assistant",
                    "Chat server failed to start. See chat_server.log for details."
                )

    def add_message(self, sender, text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"{sender}: {text}\n")
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def send_message(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.add_message("You", text)
        self.entry.delete(0, tk.END)
        threading.Thread(target=self.call_api, args=(text,)).start()

    def call_api(self, text):
        url = "http://localhost:5000/chat"
        try:
            res = requests.post(url, json={'query': text})
            res.raise_for_status()
            reply = res.json().get('reply', '')
        except requests.exceptions.ConnectionError:
            # server likely isn't running
            self.start_server()
            time.sleep(0.5)
            reply = (
                "Unable to reach InsightMate server. "
                "Make sure dependencies from requirements.txt are installed."
            )
        except Exception as e:
            reply = f"Error: {e}"
        self.root.after(0, self.add_message, "Assistant", reply)

    def on_close(self):
        if self.server_proc:
            self.server_proc.terminate()
        if hasattr(self, 'log_file') and not self.log_file.closed:
            self.log_file.close()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    gui = ChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close)
    root.mainloop()
