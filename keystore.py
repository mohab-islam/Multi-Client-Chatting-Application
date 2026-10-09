"""Loads the shared Fernet key. Never hard-code it in source control.

Order: the CHAT_SECRET_KEY environment variable, otherwise the file `secret.key` next to the scripts.
The server creates `secret.key` on first start; copy that file (or set the variable) on every client machine.
"""
import os
from cryptography.fernet import Fernet

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret.key")


def load_key(create=False):
    env = os.getenv("CHAT_SECRET_KEY")
    if env:
        return env.encode()
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read().strip()
    if create:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_FILE, 0o600)
        except OSError:
            pass
        print(f"[SETUP] Generated a new shared key in {KEY_FILE}. Copy it to every client.")
        return key
    raise SystemExit("No encryption key found. Copy secret.key from the server next to client_gui.py "
                     "or set CHAT_SECRET_KEY.")
