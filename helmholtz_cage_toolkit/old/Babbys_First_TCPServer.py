# Babby's First TCP Server - Sets up a basic TCP server and echoes anything sent to it

import socket

# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777
BUFFER_SIZE = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Socket created. Listening for client requests...")
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            conn.sendall(data)
            print(f"Echoed '{data.decode()}'")
    print("Connection terminated.")
