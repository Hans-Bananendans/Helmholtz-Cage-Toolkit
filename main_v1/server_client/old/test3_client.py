import socket
from scc2 import SCC
import sys
from client_config import config
from time import time, sleep



# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777
BUFFER_SIZE = 256


# ==== CLIENT FUNCTIONS

def get_Bm(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_bpacket([0.] * 4))

    # ##
    # resp = socket.recv(BUFFER_SIZE)
    # print("[DEBUG] b-packet returned:", resp.decode())
    # Bm = SCC.decode_bpacket(resp)
    # print("[DEBUG] decoded Bm:", Bm)
    # ##

    Bm = SCC.decode_bpacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called get_Bm(). Executed in {round((tend-tstart)*1E6, 3)} us")

    return Bm

def get_server_uptime(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("server_uptime"))
    server_uptime = SCC.decode_mpacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called get_server_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(server_uptime)

def get_socket_uptime(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("socket_uptime"))
    socket_uptime = SCC.decode_mpacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called get_socket_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(socket_uptime)

def echo(socket, msg, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_epacket(str(msg)))
    response = SCC.decode_epacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called echo(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response

def echo_alt(socket, msg, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("echo", msg))
    response = SCC.decode_epacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called echo_alt(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response

# High-level ping, echoes a single byte package, returns the response time
# in s. Returns -1 if no response is received.
def ping(socket):
    packet_out = SCC.encode_epacket("")

    tstart = time()
    socket.sendall(packet_out)              # Send 1 byte message: '0x65'
    packet_in = socket.recv(BUFFER_SIZE)    # Receive response
    tend = time()

    response = SCC.decode_epacket(packet_in)

    if response == "":
        return tend - tstart
    else:
        return -1

def set_Bc(socket, Bc, timing=False):
    if len(Bc) != 3:
        raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")

    if timing:
        tstart = time()

    socket.sendall(SCC.encode_cpacket(Bc))
    confirm = SCC.decode_mpacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called set_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

def reset_Bc(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_cpacket([0., 0., 0.]))
    confirm = SCC.decode_mpacket(socket.recv(BUFFER_SIZE))

    if timing:
        tend = time()
        print(f"Called reset_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

def message(socket, msg):
    socket.sendall(SCC.encode_mpacket(str(msg)))


if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((HOST, PORT))
            print(f"Connection to {HOST}:{PORT} established.")
            print(f"Accessing from {s.getsockname()}.")
        except:  # noqa
            print("Connection failed!")
            sys.exit(0)


        # ==== Demonstrating some functions
        timing = False  # Turn off to hide timing statistics


        print(""); sleep(1)


        # Ping and print response time:
        i = 0
        n_pings = 16
        pings = [0.]*n_pings
        print(f"Testing connection with {n_pings} pings...")
        while i < n_pings:
            pings[i] = ping(s)
            print(f" {str(i).rjust(3)}: {round(pings[i]*1E6, 1)} us")
            i += 1

        print(f"Average ping time: {round(sum(pings)/n_pings*1E6, 3)} us")

        print(""); sleep(1)


        # Echo to server using e-packet:
        print("Echo (e-packet):", echo(s, "Hello World!", timing=timing))

        # Echo to server using x-packet:
        print("Echo (x-packet):", echo_alt(s, "Hello World!", timing=timing))


        print(""); sleep(1)


        # Sending a text message to the server
        msg = "Hello server!"
        message(s, msg)
        print(f"Sent message '{msg}'")


        print(""); sleep(1)


        # Polling the server for magnetic field data:
        print("Fetching magnetic field data:")
        i = 0
        while i < 5:
            Bm = get_Bm(s, timing=timing)
            print(f"At time {Bm[0]}, Bm = [{round(Bm[1], 1)}, {round(Bm[2], 1)}, {round(Bm[3], 1)}] nT")
            i += 1
            sleep(1)


        print(""); sleep(1)


        # Setting Helmholtz cage to output to certain field strength vector Bc [nT]:
        print("Set Helmholtz cage to certain field vector Bc...", end=" ")
        confirm = set_Bc(s, [10_000., 0., -30_000.], timing=timing)
        if confirm == 1:
            print(f"{confirm} -> SUCCES")
        else:
            print(f"{confirm} -> FAILED")


        print(""); sleep(1)


        # Setting Helmholtz cage output to zero:
        print("Resetting Helmholtz cage output...", end=" ")
        confirm = reset_Bc(s, timing=timing)
        if confirm == 1:
            print(f"{confirm} -> SUCCES")
        else:
            print(f"{confirm} -> FAILED")


        print(""); sleep(1)


        # Requesting server uptime:
        server_uptime = get_server_uptime(s, timing=timing)
        print(f"Server uptime: {round(server_uptime, 3)} s")

        # Requesting connection socket uptime:
        socket_uptime = get_socket_uptime(s, timing=timing)
        print(f"Socket uptime: {round(socket_uptime, 3)} s")


        print(""); sleep(1)

        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)