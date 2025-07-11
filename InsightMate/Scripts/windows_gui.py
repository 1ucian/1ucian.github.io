import os
import sys
import subprocess
import threading
import time
try:
    import requests
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    from PIL import Image
except ImportError as e:
    print(
        f"Missing dependency: {e.name}.\n"
        "Run 'pip install -r requirements.txt' or execute 'windows_setup.ps1'"
        " to install prerequisites."
    )
    time.sleep(5)
    sys.exit(1)

try:
    import pystray
    HAVE_TRAY = True
except ImportError:
    HAVE_TRAY = False
    print(
        "pystray not installed – the system tray icon will be disabled."
    )
from config import load_config, save_config

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("InsightMate")
        self.root.geometry("500x600")
        self.config = load_config()
        self.root.configure(bg="#2b2b2b")
        self.tray = None

        self.text_area = ScrolledText(
            root,
            state="disabled",
            width=60,
            height=25,
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Segoe UI", 10),
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(
            root,
            width=60,
            bg="#2b2b2b",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Segoe UI", 10),
        )
        self.entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.entry.bind("<Return>", self.send_message)

        self.btn_frame = tk.Frame(root, bg=self.root['bg'])
        self.btn_frame.pack(padx=10, pady=(0, 10), fill=tk.X)
        tk.Button(self.btn_frame, text="Voice", command=self.voice_input).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Settings", command=self.open_settings).pack(side=tk.RIGHT)

        self.apply_theme()

        self.server_proc = None
        self.start_server()

        root.protocol("WM_DELETE_WINDOW", self.hide_window)
        root.bind("<Unmap>", self.on_minimize)

    def apply_theme(self):
        theme = self.config.get('theme', 'dark')
        if theme == 'light':
            bg_root = '#f0f0f0'
            area_bg = '#ffffff'
            area_fg = '#000000'
            entry_bg = '#ffffff'
            entry_fg = '#000000'
            user_color = '#003366'
            assistant_color = '#006600'
        else:
            bg_root = '#2b2b2b'
            area_bg = '#1e1e1e'
            area_fg = '#ffffff'
            entry_bg = '#2b2b2b'
            entry_fg = '#ffffff'
            user_color = '#89b4fa'
            assistant_color = '#f9e2af'
        self.root.configure(bg=bg_root)
        self.text_area.configure(bg=area_bg, fg=area_fg, insertbackground=area_fg)
        self.text_area.tag_config('user', foreground=user_color)
        self.text_area.tag_config('assistant', foreground=assistant_color)
        self.entry.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        if hasattr(self, 'btn_frame'):
            self.btn_frame.configure(bg=bg_root)

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
        tag = 'user' if sender == 'You' else 'assistant'
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"{sender}: {text}\n", tag)
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def send_message(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.add_message("You", text)
        self.entry.delete(0, tk.END)
        threading.Thread(target=self.call_api, args=(text,)).start()

    def voice_input(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.add_message("Assistant", "speech_recognition not installed.")
            return
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.add_message("Assistant", "Listening...")
                audio = recognizer.listen(source, phrase_time_limit=5)
        except Exception as e:
            self.add_message("Assistant", f"Microphone error: {e}")
            return
        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            self.add_message("Assistant", "Could not understand audio.")
            return
        except sr.RequestError as e:
            self.add_message("Assistant", f"Speech recognition error: {e}")
            return
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.send_message()

    def on_minimize(self, event):
        if self.root.state() == 'iconic':
            self.hide_window()

    def hide_window(self):
        self.root.withdraw()
        if HAVE_TRAY and not self.tray:
            self.setup_tray()
            threading.Thread(target=self.tray.run, daemon=True).start()

    def setup_tray(self):
        if not HAVE_TRAY:
            return
        image = Image.new('RGB', (64, 64), color='black')
        menu = pystray.Menu(
            pystray.MenuItem('Open', self.show_window),
            pystray.MenuItem('Settings', self.open_settings),
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.tray = pystray.Icon('InsightMate', image, 'InsightMate', menu)

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        if HAVE_TRAY and self.tray:
            self.tray.stop()
            self.tray = None

    def open_settings(self, icon=None, item=None):
        win = tk.Toplevel(self.root)
        win.title('Settings')
        api_var = tk.StringVar(value=self.config.get('api_key', ''))
        llm_var = tk.StringVar(value=self.config.get('llm', 'llama3'))
        theme_var = tk.StringVar(value=self.config.get('theme', 'dark'))

        tk.Label(win, text='OpenAI API Key:').grid(row=0, column=0, sticky='w')
        api_entry = tk.Entry(win, textvariable=api_var, width=40)
        api_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(win, text='LLM:').grid(row=1, column=0, sticky='w')
        llm_box = ttk.Combobox(win, textvariable=llm_var,
                               values=['gpt-4o', 'gpt-4', 'o4-mini', 'o4-mini-high', 'llama3'],
                               state='readonly')
        llm_box.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(win, text='Theme:').grid(row=2, column=0, sticky='w')
        theme_box = ttk.Combobox(win, textvariable=theme_var, values=['dark', 'light'], state='readonly')
        theme_box.grid(row=2, column=1, padx=5, pady=5)

        def save():
            self.config['api_key'] = api_var.get().strip()
            self.config['llm'] = llm_var.get()
            self.config['theme'] = theme_var.get()
            save_config(self.config)
            self.apply_theme()
            win.destroy()

        tk.Button(win, text='Save', command=save).grid(row=3, column=0, columnspan=2, pady=10)

    def quit_app(self, icon=None, item=None):
        self.on_close()

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
        if HAVE_TRAY and self.tray:
            self.tray.stop()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    gui = ChatGUI(root)
    root.mainloop()
