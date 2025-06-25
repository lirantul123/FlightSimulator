import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 50007

clients = []
clients_lock = threading.Lock()

# Each client sends: {"type": "state"|"bullet"|"chat", ...}

def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    buffer = ""
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                break
            
            buffer += data
            while True:
                try:
                    msg, end_index = json.JSONDecoder().raw_decode(buffer)
                    
                    # If we successfully decoded a message, broadcast it
                    broadcast_data = json.dumps(msg).encode()
                    with clients_lock:
                        for c in clients:
                            if c != conn:
                                try:
                                    c.sendall(broadcast_data)
                                except Exception as e:
                                    print(f"Broadcast error to {c.getpeername()}: {e}")
                    
                    # Remove the processed message from the buffer
                    buffer = buffer[end_index:].lstrip()

                except json.JSONDecodeError:
                    # Not a complete JSON object yet, wait for more data
                    break

        except ConnectionResetError:
            break # Client forcibly closed connection
        except Exception as e:
            print(f"Error with client {addr}: {e}")
            break
            
    print(f"Client disconnected: {addr}")
    with clients_lock:
        if conn in clients:
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
        with clients_lock:
            clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main() 