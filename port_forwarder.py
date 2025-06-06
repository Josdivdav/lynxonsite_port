# port_forwarder.py
import socket
import threading
import os
from flask import Flask  # Required for Render health checks

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

def start_forwarding(remote_host, remote_port):
    local_port = int(os.getenv('PORT', 10000))  # Use Render's assigned port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', local_port))
    server.listen(5)
    
    print(f"Port forwarding started: {local_port} -> {remote_host}:{remote_port}")
    
    # Start forwarding in a separate thread
    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

if __name__ == "__main__":
    # Configuration via environment variables (Render preferred)
    remote_host = os.getenv('REMOTE_HOST', 'example.com')
    remote_port = int(os.getenv('REMOTE_PORT', 80))
    
    start_forwarding(remote_host, remote_port)
    
    # Start Flask app for health checks
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 8080)))
