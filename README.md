# Secure Multi-Client Chat Application

## Course Information
**Course Name:** CSCI463: Introduction to Computer Networks  
**Semester:** Fall 2025

## Team Members
| Name | ID |
|------|----|
| Mohab Islam Ahmed | 212002286 |
| Malik Ahmed Nagy | 221001253 |
| Medhat Mohamed Zakareya | 212002364 |
| Omar Magdy Abdel Mawla | 1610400 |
| Mina Hany Tadres | 212002333 |

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
