import sys
import socket
from time import time, sleep


from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.codec.scc3 as scc
import helmholtz_cage_toolkit.client_functions as cf

"""
Simple script with boilerplate code for interacting with the server.
"""


# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777

timing = False  # Set False to hide timing statistics


if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((HOST, PORT))
            print(f"Connection to {HOST}:{PORT} established.")
            print(f"Accessing from {s.getsockname()[0]}:{s.getsockname()[1]}.")
        except:  # noqa
            print("Connection failed!")
            sys.exit(0)

        ds = QDataStream()
        print(""); sleep(0.1)

        # ==== PUT YOUR CODE HERE ====










        # ============================
        # ==== Uptimes
        print(f"Socket uptime {round(cf.get_socket_uptime(s), 3)} s")
        print(f"Server uptime {round(cf.get_server_uptime(s), 3)} s")
        print(""); sleep(0.1)

        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)