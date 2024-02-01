import sys
import socket
from time import time, sleep
from hashlib import blake2b

from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.codec.scc2q as scc
import helmholtz_cage_toolkit.client_functions as cf

"""
The scenario is as follows: the GUI application of the Helmholtz Cage Toolkit 
is already connected to the server. This script will connect as a second client
to the server, and will manipulate the server in ways that will be visible in
the GUI application.
 
In a nutshell, this file shows you how you can use a separate script to poke at
server properties in order to debug both the server and the GUI application.
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

        print(""); sleep(1)


        # Server has a functionality using a dummy vector Bdummy, that can be
        # toggled using a serveropt. If this serveropt is active, the server
        # will read fake Bm values from a dummy vector Bdummy. Bdummy is thus
        # a proxy for a real-world magnetic field reading of Bm.
        # First we have to activate the functionality:
        ack = cf.set_serveropt_use_Bdummy(s, True, ds)
        print("set_serveropt_use_Bdummy():", ack)

        confirm = cf.get_serveropt_use_Bdummy(s, ds)
        print("get_serveropt_use_Bdummy():", confirm)

        # This functionality WILL block any incoming field readings coming from
        # the hardware.

        print(""); sleep(1)

        # We can request the current value of Bdummy. The server initializes
        # it as a zero vector.
        print("get_Bdummy():", cf.get_Bdummy(s, ds))

        print(""); sleep(1)

        # Since `serveropt_use_Bdummy` is True, the Bm thread will continually
        # `measure` the value of Bdummy every time it loops. As such, we should
        # see the same value if we request Bm:
        print("get_Bm():", cf.get_Bm(s, ds))

        print(""); sleep(1)


        # Now set Bdummy to a value that will show up on the GUI application.
        # This is expressed in [nT]; internally, the server uses nT as the
        # default field density unit everywhere.
        ack = cf.set_Bdummy(s, [30_000., 40_000., 50_000.], ds)
        print("set_Bdummy(30 uT, 40 uT, 50 uT):", ack)

        print("get_Bdummy():", cf.get_Bdummy(s, ds))

        sleep(0.1)
        # After a Bm thread loop, the `measured` Bm value should be the same:
        print("get_Bm():", cf.get_Bm(s, ds))

        sleep(3)


        cleanup = True # Set to False to keep changes after script ends.

        if cleanup:
            cf.set_Bdummy(s, [0., 0., 0.], ds)
            cf.set_serveropt_use_Bdummy(s, False, ds)


        # ==== Uptimes
        print(f"Socket uptime {round(cf.get_socket_uptime(s), 3)} s")
        print(f"Server uptime {round(cf.get_server_uptime(s), 3)} s")
        print(""); sleep(1)


        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)