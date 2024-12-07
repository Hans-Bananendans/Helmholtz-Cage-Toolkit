"""
One-stop-shop automated test routine to test most server functionalities.
This implementation uses 'socket' sockets rather than QTcpSocket sockets, which
may make the tests a bit less representative.
"""

import sys
import socket
from time import time, sleep
from hashlib import blake2b
from timeit import timeit

from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.scc.scc4 as codec
import helmholtz_cage_toolkit.client_functions as cf
from helmholtz_cage_toolkit.server.server_config import server_config


HOST = server_config["SERVER_ADDRESS"]
PORT = server_config["SERVER_PORT"]

cc = "\033[96m" # cyan
cg = "\033[92m" # green
cr = "\033[91m" # red
ce = "\033[0m"  # endc


timing = False  # Set False to hide timing statistics


if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((HOST, PORT))
            t_start = time()
            print(f"Connection to {HOST}:{PORT} established.")
            print(f"Accessing from {s.getsockname()[0]}:{s.getsockname()[1]}.")
        except:  # noqa
            print("Connection failed!")
            sys.exit(0)

        ds = QDataStream()


        print("\n ==== Starting tests ====")
        n = 99
        i = 1


        # ==== Test pings ====
        t0 = time()
        r = cf.ping(s, ds)
        t1 = time()
        if r != -1:
            print(cg + f" {i}/{n} Test ping                 PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Test ping                 FAIL" + ce)
        i += 1


        # ==== Test pings ====
        n_pings = 100
        t_pings = cf.ping_n(s, n_pings, ds)
        if t_pings != -1:
            print(cc + f" {i}/{n} Test pings ({n_pings})          {int(1E6*t_pings)} \u03bcs" + ce)
        else:
            print(cr + f" {i}/{n} Test pings ({n_pings})          FAIL" + ce)
        i += 1


        # ==== Echo message ====
        msg = "Test echo message"
        t0 = time()
        r = cf.echo(s, msg, ds)
        t1 = time()
        if r == msg:
            print(cg + f" {i}/{n} Echo message              PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Echo message              FAIL")
            print(f"msg:       {msg}")
            print(f"response:  {r}" + ce)
        i += 1


        # ==== Message packet ====
        msg = "Test message"
        t0 = time()
        r = cf.message(s, msg, ds)
        t1 = time()
        if r == 1:
            print(cg + f" {i}/{n} Echo message              PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Echo message              FAIL")
            print(f"msg:       {msg}")
            print(f"response:  {r}" + ce)
        i += 1


        # ==== Get server uptime ====
        t0 = time()
        r = cf.get_server_uptime(s, ds)
        t1 = time()
        if type(r) == float and r > 0:
            print(cg + f" {i}/{n} Get server uptime         PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Get server uptime         FAIL")
            print(f"response: {r}" + ce)
        i += 1


        # ==== Get socket uptime ====
        t0 = time()
        r = cf.get_socket_uptime(s, ds)
        t1 = time()
        diff = (t1-t_start)-r
        if type(r) == float and abs(diff) <= 0.01:
            print(cg + f" {i}/{n} Get socket uptime:        PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Get socket uptime:        FAIL")
            print(f"socket-side: {t1-t_start}")
            print(f"server-side: {r}")
            print(f"diff:        {t1-t_start-r}" + ce)
        i += 1






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