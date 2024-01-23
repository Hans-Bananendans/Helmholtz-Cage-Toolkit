import socket
from scc1 import SCC1
from time import sleep

# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777
BUFFER_SIZE = 1024

codec = SCC1()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Connection established. Now you can communicate.")
    while True:
        client_command = input("Type input: ")
        ccsplit = client_command.split(" ")
        pkg_id = ccsplit[0]
        cmd = ccsplit[1]
        args = ccsplit[2]
        field = ccsplit[3]

        packet = None

        if pkg_id == "q":
            print("Sent termination request...")
            packet = codec.encode_quit()
            sleep(1)
            break
        elif pkg_id == "c":
            if cmd == "echo":
                packet = codec.encode_command("echo", "", field)
            elif cmd == "uptime":
                packet = codec.encode_command("uptime", "", "")
            elif cmd == "stop":
                packet = codec.encode_command("stop", "", "")
            else:
                print("ERROR: ENTERED INVALID COMMAND!")  # Todo: update
        elif pkg_id == "m":
            packet = codec.encode_message(field)
        else:
            print("ERROR: ENTERED INVALID COMMAND!")  # Todo: update

        if packet is not None:
            s.sendall(packet)

            # Wait for reply
            r_packet = s.recv(BUFFER_SIZE)

            # TODO: Refine later
            print(f"Received SC1 packet (size {len(r_packet)} B): {codec.decode(r_packet)}")

    print("Terminating...")
    s.shutdown(1)
    s.close()
    print("Connection terminated.")