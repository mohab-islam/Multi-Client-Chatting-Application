import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import socket
import threading
import json
from cryptography.fernet import Fernet

# Configuration
SECRET_KEY = b'Z7w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w=' 
cipher_suite = Fernet(SECRET_KEY)

class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure LAN Chat - Login") # Initial title
        self.root.geometry("700x500")

        # Network Variables
        self.client_socket = None
        self.connected = False
        self.username = None

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
        
        self.send_button = tk.Button(root, text="Send Secure Message", command=self.send_action, bg="#28a745", fg="white")
        self.send_button.pack(pady=5)

        # Initial Prompts (Auth)
        self.perform_auth()

    def perform_auth(self):
        self.username = simpledialog.askstring("Login", "Enter Username:") or "Guest"
        self.password = simpledialog.askstring("Login", "Enter Password:", show="*") or ""
        self.server_ip = simpledialog.askstring("Server Connection", "Enter Server IP Address:", initialvalue="localhost")
        
        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, 6789))
            
            # Send Auth Handshake
            creds = json.dumps({"user": self.username, "pass": self.password})
            self.client_socket.sendall(cipher_suite.encrypt(creds.encode('utf-8')))
            
            # Receive Auth Response
            response = self.client_socket.recv(4096)
            decrypted = cipher_suite.decrypt(response).decode('utf-8')
            auth_data = json.loads(decrypted)
            
            if not auth_data.get("success"):
                messagebox.showerror("Login Failed", auth_data.get("msg"))
                self.client_socket.close()
                self.root.destroy()
                return

            messagebox.showinfo("Login Success", auth_data.get("msg"))
            self.connected = True
            
            # Update Title
            self.root.title(f"Secure LAN Chat - {self.username}")
            
            # Start Listening Thread
            listen_thread = threading.Thread(target=self.receive_messages, daemon=True)
            listen_thread.start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.root.destroy()

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

    def receive_messages(self):
        buffer = b""
        while self.connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                while b'\n' in buffer:
                    message_bytes, buffer = buffer.split(b'\n', 1)
                    if not message_bytes:
                        continue
                        
                    # Decrypt and Process
                    try:
                        decrypted_text = cipher_suite.decrypt(message_bytes).decode('utf-8')
                        data_json = json.loads(decrypted_text)
                        
                        # Use root.after to safely update GUI from background thread
                        self.root.after(0, self.handle_incoming_json, data_json)
                        
                    except Exception as e:
                        print(f"Decryption/Parse Error: {e}")
                        
            except Exception as e:
                print(f"Connection lost: {e}")
                self.connected = False
                break
        
        if self.connected: # Only show error if we didn't close it intentionally
             self.root.after(0, lambda: messagebox.showerror("Disconnected", "Server connection lost."))

    def handle_incoming_json(self, data):
        m_type = data.get("type")
        
        if m_type == "user_list":
            self.refresh_user_sidebar(data['users'])
        elif m_type == "history":
            for entry in data['data']:
                user = entry.get('user')
                text = entry.get('text')
                etype = entry.get('type')
                if etype == "priv":
                    self.log_to_screen(f"[PRIVATE] {user}: {text}")
                else:
                    self.log_to_screen(f"{user}: {text}")
        elif m_type == "priv":
            sender = data.get('from', 'You')
            self.log_to_screen(f"[PRIVATE FROM {sender}]: {data['text']}")
        elif m_type == "sys":
            self.log_to_screen(f"SYSTEM: {data['text']}")
        else:
            self.log_to_screen(f"{data.get('user')}: {data.get('text')}")

    def send_action(self):
        text = self.msg_entry.get()
        if text and self.connected:
            try:
                # Encrypt
                payload = json.dumps({"text": text})
                encrypted_payload = cipher_suite.encrypt(payload.encode('utf-8'))
                
                # Send with delimiter
                self.client_socket.sendall(encrypted_payload + b'\n')
                
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Send Error", f"Failed to send: {e}")
    
    def on_closing(self):
        """Handle window closing event."""
        if self.connected:
            self.connected = False
            try:
                self.client_socket.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()