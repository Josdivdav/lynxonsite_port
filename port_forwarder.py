# port_forwarder.py
import socket
import threading
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Port forwarder is running", 200

def forward_data(source, destination, description):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
            print(f"{description}: Forwarded {len(data)} bytes")
    except Exception as e:
        print(f"{description} error: {e}")
    finally:
        source.close()
        destination.close()

def handle_client(client_socket, remote_host, remote_port):
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((remote_host, remote_port))
        
        threading.Thread(
            target=forward_data, 
            args=(client_socket, remote_socket, "Client to remote"),
            daemon=True
        ).start()
        
        threading.Thread(
            target=forward_data, 
            args=(remote_socket, client_socket, "Remote to client"),
            daemon=True
        ).start()
        
    except Exception as e:
        print(f"Connection error: {e}")
        client_socket.close()

def start_forwarding():
    remote_host = os.getenv('REMOTE_HOST', 'example.com')
    remote_port = int(os.getenv('REMOTE_PORT', 80))
    local_port = int(os.getenv('PORT', 10000))
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', local_port))
    server.listen(5)
    
    print(f"Port forwarding started: {local_port} -> {remote_host}:{remote_port}")
    
    def accept_connections():
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr[0]}:{addr[1]}")
            threading.Thread(
                target=handle_client,
                args=(client_socket, remote_host, remote_port),
                daemon=True
            ).start()
    
    threading.Thread(target=accept_connections, daemon=True).start()

if __name__ == "__main__":
    # Start the forwarding in a separate thread
    threading.Thread(target=start_forwarding, daemon=True).start()
    
    # Start Flask app for health checks on a different port
    flask_port = int(os.getenv('FLASK_PORT', 8080))
    app.run(host='0.0.0.0', port=flask_port)
