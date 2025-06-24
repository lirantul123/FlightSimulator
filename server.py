import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 50007

clients = []

# Each client sends: {"type": "state"|"bullet"|"chat", ...}

def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            try:
                msg = json.loads(data.decode())
            except Exception:
                continue
            # Broadcast to all other clients
            for c in clients:
                if c != conn:
                    try:
                        c.sendall(data)
                    except Exception:
                        pass
        except Exception:
            break
    print(f"Client disconnected: {addr}")
    clients.remove(conn)
    conn.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main() 