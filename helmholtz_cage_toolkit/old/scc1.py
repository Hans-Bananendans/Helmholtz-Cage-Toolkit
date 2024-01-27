"""
Simple Command Codec iteration 1 (SCC1)

Code implementation to facilitate command and message serialization
over a point-to-point TCP/IP connection.
"""

class SCC1:
    # self.sep = "\1D"  # todo: test that this works
    # self.eot = "\17"

    def __init__(self):
        self.sep = "\1D"
        self.eot = "\17"

    def get_sep(self):
        return self.sep

    def set_sep(self, sep):
        self.sep = sep

    def get_eot(self):
        return self.eot

    def set_eot(self, eot):
        self.eot = eot

    # def parse_packet(self, scc1_packet):
    #     msg_id = self.parser.decode(packet)[0]
    #
    #     if msg_id == "c":
    #         self.read_command(scc1_packet)
    #     elif msg_id == "m":
    #         self.read_message(scc1_packet)
    #     elif msg_id == "q":
    #
    #
    # def decode_command(self, scc1_packet):
    #     pkg_id, cmd, args, field, eot = self.decode(scc1_packet)
    #
    # def decode_message(self, scc1_packet):
    #     return self.decode(scc1_packet)[3]

    def encode_command(self, cmd, args, field):
        print(f"[DEBUG] encode_command({cmd}, {args}, {field})")
        print("[DEBUG] encode_command()")
        return self.encode("c", cmd, args, field)

    def encode_message(self, msg):
        print("[DEBUG] encode_message()")
        return self.encode("m", "", "", msg)

    def encode_error(self, error_id, error_msg):
        return self.encode("e", "", error_id, error_msg)

    def encode_quit(self):
        return self.encode("q", "", "", "")

    def encode(self, msg_id, cmd, args, field):
        print(f"[DEBUG] encode({msg_id}, {cmd}, {args}, {field})")
        return f"{msg_id}{self.sep}{cmd}{self.sep}{args}{self.sep}{field}{self.sep}".encode()

    def decode(self, scc1_packet):
        return scc1_packet.decode().split(self.sep)[:-1]