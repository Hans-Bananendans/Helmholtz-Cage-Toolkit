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
            print(cg + f" {i}/{n} Send message              PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Send message              FAIL")
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


        # ==== Get socket info ====
        t0 = time()
        r = cf.get_socket_info(s, ds)
        t1 = time()
        diff = (t1-t_start)-r[0]
        if type(r[0]) == float and abs(diff) <= 0.01 and type(r[1]) == str \
                and type(r[2]) == int and r[2] >= 0:
            print(cg + f" {i}/{n} Get socket info           PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            print(cg + f"       -> Uptime: {round(r[0], 6)} (diff: {round(diff*1E6)} \u03bcs)" + ce)
            print(cg + f"       -> Socket: {r[1]}:{r[2]}" + ce)
        else:
            print(cr + f" {i}/{n} Get socket info           FAIL" + ce)
            print(cr + f"Uptime: {round(r[0], 6)} (diff: {round(diff*1E6)} \u03bcs)" + ce)
            print(cr + f"Socket: {r[1]}:{r[2]} ({type(r[1])}:{type(r[2])})" + ce)
        i += 1


        # ==== Get Bm ====
        t0 = time()
        tm, Bm = cf.get_Bm(s, ds)
        t1 = time()
        if tm >= 0 and len(Bm) == 3 \
                and [True for v in Bm if type(v) == float] == [True, ]*3:
            print(cg + f" {i}/{n} Get Bm                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            print(cg + f"       -> {tm}, {Bm}" + ce)
        else:
            print(cr + f" {i}/{n} Get Bm                    FAIL")
            print(f"tm: {tm}")
            print(f"Bm: {Bm}" + ce)
        i += 1


        # ==== Set Bc ====
        Bc_test = [3.3, 6.6, -9.9]
        t0 = time()
        r = cf.set_Bc(s, Bc_test, ds)
        t1 = time()
        if r == 1:
            print(cg + f" {i}/{n} Set Bc                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Set Bc                    FAIL")
        i += 1

        # ==== Get Bc ====
        t0 = time()
        Bc = cf.get_Bc(s, ds)
        t1 = time()
        if Bc == Bc_test:
            print(cg + f" {i}/{n} Get Bc                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            print(cg + f"       {Bc} -> {Bc}" + ce)
        else:
            print(cr + f" {i}/{n} Get Bc                    FAIL")
            print(f"Bc set:      {Bc_test}")
            print(f"Bc response: {Bc}" + ce)
        i += 1


        # ==== Set Br ====
        Br_test = [2.2, 5.5, -8.8]
        t0 = time()
        r = cf.set_Br(s, Br_test, ds)
        t1 = time()
        if r == 1:
            print(cg + f"{i}/{n} Set Br                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Set Br                    FAIL")
        i += 1

        # ==== Get Br ====
        t0 = time()
        Br = cf.get_Br(s, ds)
        t1 = time()
        if Br == Br_test:
            print(cg + f"{i}/{n} Get Br                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            print(cg + f"       {Br} -> {Br}" + ce)
        else:
            print(cr + f"{i}/{n} Get Br                    FAIL")
            print(f"Bc set:      {Br_test}")
            print(f"Bc response: {Br}" + ce)
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