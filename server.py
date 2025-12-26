import asyncio
import websockets
import json
import os

import sqlite3
from cryptography.fernet import Fernet

# Persistence Configuration
DB_FILE = "chat_history.db"
KEY_FILE = "secret.key"
clients = {} # Dictionary to map {username: websocket_connection}

def load_key():
    """Loads the secret key from the current directory or creates one if it doesn't exist."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

SECRET_KEY = load_key()

def init_db():
    """Initializes the SQLite database and creates the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_to_history(msg_obj):
    """Saves message data to the SQLite database."""
    # Only save if it has the expected keys
    if "user" in msg_obj and "text" in msg_obj:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (msg_obj["user"], msg_obj["text"]))
        conn.commit()
        conn.close()

async def broadcast_user_list():
    """Sends the updated list of online users to everyone."""
    if clients:
        user_list = list(clients.keys())
        payload = json.dumps({"type": "user_list", "users": user_list})
        await asyncio.gather(*[ws.send(payload) for ws in clients.values()])

async def handle_client(ws):
    username = None
    try:
        # Step 1: Registration
        # The first message from the client must be their username
        init_data = json.loads(await ws.recv())
        username = init_data.get("user", "Anonymous")
        clients[username] = ws
        print(f"[LOG] {username} connected.")
        
        # Send Encryption Key
        await ws.send(json.dumps({"type": "key", "key": SECRET_KEY.decode()}))

        # Step 2: Load Persistence (Send History)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Retrieve the last 100 messages
        cursor.execute("SELECT username, message FROM messages ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        # Convert back to message objects list (reverse to restore chronological order)
        history = [{"type": "msg", "user": r[0], "text": r[1]} for r in reversed(rows)]
        
        await ws.send(json.dumps({"type": "history", "data": history}))


        # Step 3: Update User List and Notify Group
        await broadcast_user_list()
        join_notif = json.dumps({"type": "sys", "text": f"{username} joined the chat."})
        await asyncio.gather(*[c.send(join_notif) for c in clients.values()])

        # Step 4: Communication Loop
        async for message in ws:
            data = json.loads(message)
            text = data.get("text", "")

            # Logic for Private Messaging (@username message)
            if text.startswith("@") and " " in text:
                try:
                    target_name, priv_msg = text.split(" ", 1)
                    target_name = target_name[1:] # Strip the '@' symbol
                    if target_name in clients:
                        payload = json.dumps({"type": "priv", "from": username, "text": priv_msg})
                        await clients[target_name].send(payload)
                        await ws.send(payload) # Echo back to sender
                        continue
                except ValueError:
                    pass

            # Logic for Group Messaging (Broadcast)
            group_payload = {"type": "msg", "user": username, "text": text}
            save_to_history(group_payload)
            await asyncio.gather(*[c.send(json.dumps(group_payload)) for c in clients.values()])

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Step 5: Graceful Cleanup
        if username in clients:
            del clients[username]
            await broadcast_user_list()
            leave_notif = json.dumps({"type": "sys", "text": f"{username} disconnected."})
            if clients:
                await asyncio.gather(*[c.send(leave_notif) for c in clients.values()])
            print(f"[LOG] {username} disconnected.")

async def main():
    # Initialize the database
    init_db()
    # Bind to 0.0.0.0 to allow connections from any device on the LAN (Wired/Wireless)
    async with websockets.serve(handle_client, "0.0.0.0", 6789):
        print("Chat Server running on port 6789...")
        print("Ready for Wired/Wireless LAN connections (No Internet Required).")
        await asyncio.Future() # Keep server running indefinitely

if __name__ == "__main__":
    asyncio.run(main())