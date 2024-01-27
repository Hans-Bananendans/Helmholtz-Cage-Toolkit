
import socket

from time import time, sleep
from logbase import LogBase
from server_config import config as server_config
from scc1 import SCC1

# # HOST = "169.254.241.64"  # whatever outside connection
# HOST = "127.0.0.1"  # localhost
# PORT = 7777
# BUFFER_SIZE = 1024
#
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.bind((HOST, PORT))
#     s.listen()
#     print("Socket created. Listening for client requests...")
#     conn, addr = s.accept()
#     with conn:
#         print(f"Connected by {addr}")
#         while True:
#             data = conn.recv(BUFFER_SIZE)
#             if not data:
#                 break
#             conn.sendall(data)
#             print(f"Echoed '{data.decode()}'")
#
#     print("Terminating...")
#     s.shutdown(1)
#     s.close()
#     print("Connection terminated.")


class Server(LogBase):
    def __init__(self, config):
        self._tstart = time()
        self._config = config
        self.codec = SCC1

        self.conn = None
        self.addr = None

        self.log(2, "Instantiating server...  ", end="")

        self.log(2, "DONE", pts=False)

    def __del__(self):
        pass

    def uptime(self):
        return time() - self._tstart

    def _ts(self, ss_round=6):
        """Generates an UpTimeStamp, basically just an organized time string.
        Overrides the _ts() from LogBase to print these timestamps instead.
        """
        ut = self.uptime()

        r, ss = divmod(ut, 1)           # subseconds
        d, r = divmod(round(r), 86400)  # days
        h, r = divmod(r, 3600)          # hours
        m, s = divmod(r, 60)            # minutes, seconds

        def rj(item, n=2, char="0"):
            return str(item).rjust(n, char)
        if d == 0:
            return f"{rj(h)}:{rj(m)}:{rj(s)}.{rj(int(ss*10*ss_round), n=ss_round)}"
        else:
            return f"{d}:{rj(h)}:{rj(m)}:{rj(s)}.{rj(int(ss*10**ss_round), n=ss_round)}"

    def start(self):
        """Begins default active state of server. In this state, it listens
        on the ports and establishes a connection when a client tries to
        connect.
        """
        self.log(2, "Setting up socket...")
        self.create_socket()
        self.socket.listen()
        self.log(2, "Socket created. Listening for client requests...")

        self.conn, self.addr = self.socket.accept()

        self.break_serve = False
        self.break_conn = False

        with self.conn:
            self.log(2, f"Connected to client from {self.addr[0]}:{self.addr[1]}")

            while True:
                if self.break_serve:
                    self.break_serve = False
                    if self.break_conn:
                        self.stop()
                    break
                else:
                    self.serve()


    def serve(self):

        packet = self.conn.recv(self._config["BUFFER_SIZE"])
        if not packet:
            self.break_serve = True

        self.log(4, f"Received SC1 packet (size {len(packet)} B): {self.codec.decode(packet)}")

        dd = self.codec.decode(packet)
        pkg_id, cmd, args, field = self.codec.decode(packet)


        # Decision tree # TODO: find out if there's a smarter way of parsing
        if pkg_id == "c":
            if cmd == "echo":
                self.a_echo(field)
            elif cmd == "uptime":
                self.a_echo_uptime()
            elif cmd == "stop":
                self.log(2, "Received 'stop' request")
                self.break_serve = True
                self.break_conn = True
            else:
                self.a_handle_error(11, f"Received SC1 package contains invalid command: '{cmd}'")
        elif pkg_id == "q":
            self.log(2, "Received 'stop' request (q-packet)")
            self.break_serve = True
            self.break_conn = True
        elif pkg_id == "m":
            self.a_handle_message(dd[3])  # Placeholder TODO: Implement
        else:
            self.a_handle_error(10, f"Received SC1 package has invalid pkg_id: '{pkg_id}'")


    def a_echo(self, msg):
        self.conn.sendall(self.codec.encode_message(msg))
        self.log(4, f"Echoed '{msg}' to {self.addr[0]}:{self.addr[1]}")

    def a_echo_uptime(self):
        ut = self.uptime()
        print("DEBUG: uptime:", ut, type(ut))
        self.conn.sendall(self.codec.encode_message(ut))
        self.log(4, f"Echoed uptime to {self.addr[0]}:{self.addr[1]}")

    def a_handle_message(self, msg):
        self.log(2, f"Server received message: {msg}")

    def a_stop(self):
        self.conn.sendall(self.codec.encode_quit())

    def a_handle_error(self, error_id, error_msg):
        self.conn.sendall(self.codec.encode_error(error_id, error_msg))
        self.log(2, f"Server returned error message: {error_id}, {error_msg}")

    def stop(self):
        """Attempts to gracefully terminate a connection and end a socket.
        """
        self.a_stop()
        self.log(2, f"Sent stop notice to client")
        self.log(2, f"Stopping active socket...", end="")
        if self.conn is not None:
            self.socket.shutdown(0)
        self.socket.close()
        self.conn = None
        self.addr = None
        self.log(2, "DONE", pts=False)

    def create_socket(self):
        addr = self._config["SERVER_ADDRESS"]
        port = self._config["SERVER_PORT"]

        self.log(2, f"Creating socket on {addr}:{port}... ", end="")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((addr, port))

        self.log(2, "DONE", pts=False)


server1 = Server(config=server_config)
server1.start()

server1.stop()

