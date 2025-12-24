import asyncio
import websockets
import json
import os

# Persistence Configuration
DB_FILE = "chat_history.json"
clients = {} # Dictionary to map {username: websocket_connection}

def save_to_history(msg_obj):
    """Saves message data to a local file for persistence."""
    history = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    history.append(msg_obj)
    # Keep only the last 100 messages to maintain performance
    with open(DB_FILE, "w") as f:
        json.dump(history[-100:], f)

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

        # Step 2: Load Persistence (Send History)
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                try:
                    await ws.send(json.dumps({"type": "history", "data": json.load(f)}))
                except: pass

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
    # Bind to 0.0.0.0 to allow connections from any device on the LAN (Wired/Wireless)
    async with websockets.serve(handle_client, "0.0.0.0", 6789):
        print("Chat Server running on port 6789...")
        print("Ready for Wired/Wireless LAN connections (No Internet Required).")
        await asyncio.Future() # Keep server running indefinitely

if __name__ == "__main__":
    asyncio.run(main())