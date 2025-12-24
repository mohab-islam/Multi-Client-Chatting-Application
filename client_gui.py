import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import asyncio
import threading
import json
import websockets

class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Networks Chat Messenger")
        self.root.geometry("700x500")

        # UI Layout: Main Frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # UI Layout: Chat Window (Left)
        self.chat_display = scrolledtext.ScrolledText(self.main_frame, state='disabled', wrap='word', width=50)
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # UI Layout: User List Sidebar (Right)
        self.user_sidebar = tk.Listbox(self.main_frame, width=20, bg="#f8f9fa")
        self.user_sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # UI Layout: Input Field
        self.msg_entry = tk.Entry(root, font=("Arial", 11))
        self.msg_entry.pack(padx=10, pady=5, fill=tk.X)
        self.msg_entry.bind("<Return>", lambda e: self.send_action())
        
        self.send_button = tk.Button(root, text="Send Message", command=self.send_action, bg="#28a745", fg="white")
        self.send_button.pack(pady=5)

        # Initial Prompts
        self.username = simpledialog.askstring("Username", "Enter your display name:") or "Guest"
        self.server_ip = simpledialog.askstring("Server Connection", "Enter Server IP Address:", initialvalue="localhost")
        
        self.websocket = None
        self.loop = None
        # Start the network loop in a background thread
        threading.Thread(target=self.start_async_thread, daemon=True).start()

    def log_to_screen(self, message, tag=None):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n", tag)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def refresh_user_sidebar(self, users):
        self.user_sidebar.delete(0, tk.END)
        self.user_sidebar.insert(tk.END, "--- ONLINE ---")
        for user in users:
            self.user_sidebar.insert(tk.END, f"● {user}")

    async def run_network_logic(self):
        uri = f"ws://{self.server_ip}:6789"
        try:
            async with websockets.connect(uri) as ws:
                self.websocket = ws
                # Register with server
                await ws.send(json.dumps({"user": self.username}))
                
                async for raw_message in ws:
                    data = json.loads(raw_message)
                    m_type = data.get("type")

                    if m_type == "user_list":
                        self.refresh_user_sidebar(data['users'])
                    elif m_type == "history":
                        for entry in data['data']:
                            self.log_to_screen(f"{entry['user']}: {entry['text']}")
                    elif m_type == "priv":
                        sender = data.get('from', 'You')
                        self.log_to_screen(f"[PRIVATE FROM {sender}]: {data['text']}")
                    elif m_type == "sys":
                        self.log_to_screen(f"SYSTEM: {data['text']}")
                    else:
                        self.log_to_screen(f"{data.get('user')}: {data.get('text')}")
        except Exception as e:
            messagebox.showerror("Connection Lost", "Disconnected from server. Check your LAN/Wi-Fi connection.")

    def start_async_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        loop.run_until_complete(self.run_network_logic())

    def send_action(self):
        text = self.msg_entry.get()
        if text and self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({"text": text})), 
                self.loop
            )
            self.msg_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()