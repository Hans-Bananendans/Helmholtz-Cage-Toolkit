import socket
from scc1 import SCC1
from time import sleep
from cmd import Cmd

from client_config import config


class ClientShell(Cmd):
    intro = 'This is an interactive shell to communicate with the server. Type help or ? to list commands.'
    prompt = ' > '
    file = None

    def __init__(self, config):
        super().__init__()

        self.codec = SCC1()

        self._config = config

        self.verbosity = self._config["verbosity"]
        self.timing_info = self._config["timing_info"]

        self.server_address = config["SERVER_ADDRESS"]
        self.port = config["SERVER_PORT"]
        self.buffer_size = config["BUFFER_SIZE"]



    def log(self, verbosity_level, string):
        if verbosity_level <= self.verbosity:
            print(string)


    def handle_exception(self):
        self.log(4, "[DEBUG] EXCEPTION HANDLER CALLED")
        if self.socket is not None:
            self.log(4, "[DEBUG] EXCEPTION HANDLER: CLOSED SOCKET")
            self.socket.close()

    def send(self):



    # ==== SHELL COMMANDS ====
    def do_connect(self, arg):
        """Connect to the server"""
        self.log(4, "[DEBUG] CALL do_connect()")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((self.server_address, self.port))
            self.log(4, f"Connected to {self.server_address}:{self.port}")

        except:
            self.handle_exception()


    def do_disconnect(self, arg):
        """Disconnect to the server"""
        self.log(4, "[DEBUG] CALL do_disconnect()")


    def do_quit(self, arg):
        """Disconnect from the server, and then close the session"""
        print('Exiting...')
        return True


    def do_echo(self, arg):
        """Requests the server to echo a certain message."""
        self.log(4, "[DEBUG] CALL do_echo()")


    def do_argtest(self, arg):
        """Requests the server to echo a certain message."""
        self.log(4, "[DEBUG] CALL do_argtest()")
        self.log(4, arg)
        # self.log(4, str(*parse(arg)))


    def do_b(self, arg):
        """Queries the server for magnetic field measurement."""
        self.log(4, "[DEBUG] CALL do_b()")


    def do_uptime(self, arg):
        """Queries the server for uptime."""
        self.log(4, "[DEBUG] CALL do_uptime()")


    def do_ping(self, arg):
        """Sends a short command to the server, waits for a response, and
        returns the time of the interaction.
        """
        self.log(4, "[DEBUG] CALL do_ping()")



def parse_usercommand(arg):  # TODO REWRITE THIS
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

def parse_packet(arg):  # TODO REWRITE THIS
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))


if __name__ == '__main__':

    shell = ClientShell(config)

    shell.cmdloop()




# # HOST = "169.254.241.64"  # whatever outside connection
# HOST = "127.0.0.1"  # localhost
# PORT = 7777
# BUFFER_SIZE = 1024
#
# parser = SC1Parser()
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     print("Connection established. Now you can communicate.")
#     while True:
#         client_command = input("Type input: ")
#         ccsplit = client_command.split(" ")
#         pkg_id = ccsplit[0]
#         cmd = ccsplit[1]
#         args = ccsplit[2]
#         field = ccsplit[3]
#
#         packet = None
#
#         if pkg_id == "q":
#             print("Sent termination request...")
#             packet = parser.encode_quit()
#             sleep(1)
#             break
#         elif pkg_id == "c":
#             if cmd == "echo":
#                 packet = parser.encode_command("echo", "", field)
#             elif cmd == "uptime":
#                 packet = parser.encode_command("uptime", "", "")
#             elif cmd == "stop":
#                 packet = parser.encode_command("stop", "", "")
#             else:
#                 print("ERROR: ENTERED INVALID COMMAND!")  # Todo: update
#         elif pkg_id == "m":
#             packet = parser.encode_message(field)
#         else:
#             print("ERROR: ENTERED INVALID COMMAND!")  # Todo: update
#
#         if packet is not None:
#             s.sendall(packet)
#
#             # Wait for reply
#             r_packet = s.recv(BUFFER_SIZE)
#
#             # TODO: Refine later
#             print(f"Received SC1 packet (size {len(r_packet)} B): {parser.decode(r_packet)}")
#
#     print("Terminating...")
#     s.shutdown(1)
#     s.close()
#     print("Connection terminated.")