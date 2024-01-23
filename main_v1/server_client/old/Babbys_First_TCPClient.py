import socket

# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777
BUFFER_SIZE = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Connection established. Now you can communicate to the server or 'quit' to quit.")
    while True:
        msg = input("Type a message for the server to echo: ")
        if msg == "quit":
            break
        s.sendall(msg.encode())
        data = s.recv(BUFFER_SIZE)
        print(f"Received {data.decode()}")
