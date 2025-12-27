import socket
import threading
import json
import os
from cryptography.fernet import Fernet

# Configuration
HOST = '0.0.0.0'
PORT = 6789
DB_FILE = "chat_history.json" 
USERS_FILE = "users.json"

SECRET_KEY = b'Z7w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w1w=' 
cipher_suite = Fernet(SECRET_KEY)

clients = {} 
lock = threading.RLock()

# --- AUTHENTICATION ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users_db):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_db, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save users: {e}")

def authenticate_user(username, password):
    """
    Returns (True, msg) if valid/created.
    Returns (False, msg) if invalid.
    """
    with lock:
        users_db = load_users()
        
        if username in users_db:
            # Login
            if users_db[username] == password:
                return True, "Welcome back!"
            else:
                return False, "Incorrect password."
        else:
            # Register
            users_db[username] = password
            save_users(users_db)
            return True, "New account created. Welcome!"


def load_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load history: {e}")
        return []

def save_message(username, message, msg_type="msg", target=None):
    """Save message to JSON file."""
    msg_obj = {
        "user": username, 
        "text": message, 
        "type": msg_type,
        "target": target # None for group, username for private
    }
    
    with lock:
        history = load_history()
        history.append(msg_obj)
        # Keep last 500 messages (increased limit since we store PMs now)
        history = history[-500:] 
        
        try:
            with open(DB_FILE, 'w') as f:
                json.dump(history, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            print(f"[LOG] Saved {msg_type} from {username}. Target: {target}")
        except Exception as e:
            print(f"[ERROR] Failed to save history: {e}")

def get_filtered_history(username):
    """Return history relevant to this user (Public + their PMs)."""
    full_history = load_history()
    filtered = []
    
    for msg in full_history:
        m_type = msg.get("type")
        target = msg.get("target")
        sender = msg.get("user")
        
        if m_type == "msg":
            # Public message
            filtered.append(msg)
        elif m_type == "priv":
            # Private message: show if I sent it OR if sent to me
            if sender == username or target == username:
                filtered.append(msg)
    
    # Return last 100 of the filtered list
    return filtered[-100:]

def broadcast(message_dict, exclude_user=None):
    json_str = json.dumps(message_dict)
    encrypted_bytes = cipher_suite.encrypt(json_str.encode('utf-8'))
    payload = encrypted_bytes + b'\n'
    
    with lock:
        to_remove = []
        for user, socket_conn in clients.items():
            if user == exclude_user:
                continue
            try:
                socket_conn.sendall(payload)
            except:
                to_remove.append(user)
        
        for user in to_remove:
            del clients[user]

def send_private(target_user, message_dict):
    json_str = json.dumps(message_dict)
    encrypted_bytes = cipher_suite.encrypt(json_str.encode('utf-8'))
    payload = encrypted_bytes + b'\n'
    
    with lock:
        if target_user in clients:
            try:
                clients[target_user].sendall(payload)
            except:
                del clients[target_user]

def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    username = None
    
    try:

        encrypted_data = client_socket.recv(4096)
        if not encrypted_data: return
            
        try:
            decrypted = cipher_suite.decrypt(encrypted_data).decode('utf-8')
            creds = json.loads(decrypted)
            user_attempt = creds.get("user")
            pass_attempt = creds.get("pass")
            
            # Authenticate
            is_valid, auth_msg = authenticate_user(user_attempt, pass_attempt)
            
            # Send Auth Result
            auth_response = json.dumps({"success": is_valid, "msg": auth_msg})
            client_socket.sendall(cipher_suite.encrypt(auth_response.encode('utf-8')) + b'\n')
            
            if not is_valid:
                print(f"[AUTH FAIL] {user_attempt} failed login.")
                return # Disconnect
                
            username = user_attempt
            
        except Exception as e:
            print(f"Handshake/Auth failed: {e}")
            return 

        with lock:
  
            clients[username] = client_socket
        
        print(f"[REGISTERED] User: {username}")
        
    
        history = get_filtered_history(username)
        hist_payload = json.dumps({"type": "history", "data": history})
        client_socket.sendall(cipher_suite.encrypt(hist_payload.encode('utf-8')) + b'\n')
        
  
        join_msg = {"type": "sys", "text": f"{username} joined the chat."}
        broadcast(join_msg)
        broadcast({"type": "user_list", "users": list(clients.keys())})
        

        buffer = b""
        while True:
            data = client_socket.recv(4096)
            if not data: break
            buffer += data
            
            while b'\n' in buffer:
                message_bytes, buffer = buffer.split(b'\n', 1)
                if not message_bytes: continue
                
                try:
                    decrypted_text = cipher_suite.decrypt(message_bytes).decode('utf-8')
                    msg_obj = json.loads(decrypted_text)
                    text = msg_obj.get("text", "")
                    
                    if text.startswith("@") and " " in text:
                        parts = text.split(" ", 1)
                        target = parts[0][1:]
                        content = parts[1]
                        
                        # Save Private Message
                        save_message(username, content, "priv", target)
                        
                        if target in clients:
                            priv_msg = {"type": "priv", "from": username, "text": content}
                            send_private(target, priv_msg)
                            send_private(username, priv_msg) 
                        else:
                            send_private(username, {"type": "sys", "text": f"User {target} is offline but will see your message when they login."})
                        continue
                        
                    group_msg = {"type": "msg", "user": username, "text": text}
                    save_message(username, text, "msg") 
                    broadcast(group_msg)
                    
                except Exception as e:
                    print(f"Error processing message: {e}")

    except (ConnectionResetError, ConnectionAbortedError):
        print(f"[DISCONNECT] {addr} forced disconnect.")
    except Exception as e:
        print(f"Client error with {addr}: {e}")
    finally:
        with lock:
            if username and username in clients:
                del clients[username]
                leave_msg = {"type": "sys", "text": f"{username} disconnected."}
                broadcast(leave_msg)
                broadcast({"type": "user_list", "users": list(clients.keys())})
        client_socket.close()
        print(f"[CLOSED] {addr} connection closed.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    print(f"[SECURITY] Encryption Enabled")
    print(f"[AUTH] User/Pass system active")

    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()

if __name__ == "__main__":
    start_server()