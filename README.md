# Secure Multi-Client Chat Application

## Course Information
**Course Name:** CSCI463: Introduction to Computer Networks  
**Semester:** Fall 2025

## Team Members
| Name |
|------|
| Mohab Islam Ahmed |
| Malik Ahmed Nagy |
| Medhat Mohamed Zakareya |
| Omar Magdy Abdel Mawla |
| Mina Hany Tadres |

## Project Description
This project is a multi-client chatting application developed using Python's socket programming libraries. It relies on a Centralized Server Architecture (TCP) to manage connections, ensuring reliable message delivery between users.

### Key Features
*   **Real-time Communication:** Users can send and receive messages instantly.
*   **Multi-Client Support:** The server uses multithreading to handle multiple clients simultaneously.
*   **Security:** All messages are encrypted using Fernet (symmetric encryption) to ensure confidentiality over the local network.
*   **Authentication:** Users can register and log in with a username and password.
*   **Private Messaging:** Supports direct private messages between users using the `@username` syntax.
*   **Message Persistence:** Chat history is saved server-side (in JSON format) so users can see previous messages upon logging in.
*   **Graphical User Interface (GUI):** A user-friendly interface built with Tkinter.

## How to Run
### Prerequisites
*   Python 3.x
*   `cryptography` library

### Encryption key
All messages are encrypted with one shared Fernet key. It is **not** stored in the source code:

*   The server creates `secret.key` the first time it starts (or reads `CHAT_SECRET_KEY` if you set it).
*   Copy `secret.key` to each client machine next to `client_gui.py` (or set `CHAT_SECRET_KEY`). Keep it private.

### Installation
1.  Install the required library:
    ```bash
    pip install cryptography
    ```

### Running the Application
1.  **Start the Server:**
    Run the server script on the host machine.
    ```bash
    python server.py
    ```
2.  **Start the Client(s):**
    Run the client script on any computer connected to the same network.
    ```bash
    python client_gui.py
    ```
    *   Enter the IP address of the server machine when prompted.


## Notes on data
Passwords are stored as salted scrypt hashes in `users.json`, and chat history in `chat_history.json`. Both files, and `secret.key`, are created at runtime and are git-ignored.
