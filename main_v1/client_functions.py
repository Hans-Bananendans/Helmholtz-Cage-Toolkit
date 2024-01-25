import codec.scc2q as scc
from time import time
from socket import socket
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtCore import QDataStream


def send_and_receive(packet,
                     socket_obj,
                     datastream: QDataStream = None,
                     buffer_size: int = scc.packet_size,
                     t_wait_ms: int = 100):
    """Wrapper for sequentially sending and receiving a packet over TCP, with
    built-in support for the standard `socket` library backend, as well as the
    QTcpSocket backend.

    It is meant to be used to make higher level network function
    implementations, for example an "echo" function or a file send, agnostic
    to TCP socket backend.

    Relevant for the QTcpSocket implementation: For performance reasons, it is
    highly recommended pass a common QDataStream object to this function, using
    the `datastream` keyword argument. If not, this function will create a new
    one for every call of the function, which comes with substantial overhead.

    Superficial testing indicates that pre-specifying a re-usable datastream
    object cuts down a localhost packet exchange from ~500 us to <250 us.
    """

    # Implementation for socket.socket
    if type(socket_obj) == socket:

        # Send package
        socket_obj.sendall(packet)

        # Return package when received
        return socket_obj.recv(buffer_size)

    # Implementation for QTcpSocket
    elif type(socket_obj) == QTcpSocket:

        # If no QDataStream object was passed, create a new one. This decreases
        # performance, so ideally you want to pass one.
        if not datastream:
            datastream = QDataStream(socket_obj)

        # Write packet to TCP socket
        datastream.writeRawData(packet)
        # ts = time()  # [TIMING]
        # Return the response
        if socket_obj.waitForReadyRead(t_wait_ms):
            # tr = time()  # [TIMING]
            # print(f"send_and_receive(): {int((tr-ts)*1E6)} \u03bcs")  # [TIMING]
            return datastream.readRawData(buffer_size)
        # If no response was received within `t_wait_ms`, call it a failure
        else:
            print(f"No response received to packet {packet}")
            return None

    # If something other than a supported socket was given
    else:
        raise AssertionError(f"Unsupported socket type given: `{type(socket_obj)}`")


def get_Bm(socket,
           datastream: QDataStream = None,
           timing=False
           ):
    """Requests and returns the most recent Bm value from the server.

    The server will return b-packet with the current Bm value whenever a
    client sends a b-packet. The server just reads the packet type; the
    contents of the b-package sent by the client does not matter, so this
    function sends four zero float values.

    The returning b-package with the Bm values are then decoded and returned.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    Bm = scc.decode_bpacket(
        send_and_receive(
            scc.encode_bpacket([0.]*4),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called get_Bm(). Executed in {int((tend-tstart)*1E6)} us")

    return Bm


def echo(socket,
         msg,
         datastream: QDataStream = None,
         timing=False):
    """Sends a message `msg` to the server, which will in turn echo it back.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if timing:
        tstart = time()

    response = scc.decode_epacket(
        send_and_receive(
            scc.encode_epacket(str(msg)),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called echo(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response


def get_control_vals(socket,
                     datastream: QDataStream = None,
                     timing=False):
    """Requests the current control_vals from the server, which is a list of
    the Bc, Ic and Vc that were applied to the power supplies most recently.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    control_vals_string = scc.decode_mpacket(
        send_and_receive(
            scc.encode_xpacket("get_control_vals"),
            socket,
            datastream=datastream
        )
    ).split(",")

    # socket.sendall(SCC.encode_xpacket("get_control_vals"))

    # control_vals_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
    control_vals = [
        [float(B) for B in control_vals_string[0:3]],
        [float(I) for I in control_vals_string[3:6]],
        [float(V) for V in control_vals_string[6:9]]]

    if timing:
        tend = time()
        print(f"Called get_control_vals(). Executed in {round((tend-tstart)*1E6, 3)} us")

    return control_vals

# def get_control_vals(socket, timing=False):
#     """Fetches control_vals from the server, which is a list of the Bc, Ic and
#     Vc that was applied to the power supplies most recently.
#     """
#     if timing:
#         tstart = time()
#
#     socket.sendall(SCC.encode_xpacket("get_control_vals"))
#
#     control_vals_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
#     control_vals = [
#         [float(B) for B in control_vals_string[0:3]],
#         [float(I) for I in control_vals_string[3:6]],
#         [float(V) for V in control_vals_string[6:9]]]
#
#     if timing:
#         tend = time()
#         print(f"Called get_control_vals(). Executed in {round((tend-tstart)*1E6, 3)} us")
#
#     return control_vals


def set_Bc(socket,
           Bc,
           datastream: QDataStream = None,
           timing=False):
    if len(Bc) != 3:
        raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")

    if timing:
        tstart = time()

    confirm = scc.decode_mpacket(
        send_and_receive(
            scc.encode_cpacket(Bc),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called set_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)


def reset_Bc(socket,
             datastream: QDataStream = None,
             timing=False):
    if timing:
        tstart = time()

    confirm = set_Bc(socket, [0., 0., 0.], datastream=datastream)

    if timing:
        tend = time()
        print(f"Called reset_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

# def set_Bc(socket, Bc, timing=False):  # TODO UPDATE
#     if len(Bc) != 3:
#         raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")
#
#     if timing:
#         tstart = time()
#
#     socket.sendall(SCC.encode_cpacket(Bc))
#     confirm = SCC.decode_mpacket(socket.recv(SSC.buffer_size))
#
#     if timing:
#         tend = time()
#         print(f"Called set_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return int(confirm)
#
# def reset_Bc(socket, timing=False):  # TODO UPDATE
#     if timing:
#         tstart = time()
#
#     socket.sendall(SCC.encode_cpacket([0., 0., 0.]))
#     confirm = SCC.decode_mpacket(socket.recv(SSC.buffer_size))
#
#     if timing:
#         tend = time()
#         print(f"Called reset_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return int(confirm)


def get_server_uptime(socket,
                      datastream: QDataStream = None,
                      timing=False):
    if timing:
        tstart = time()

    server_uptime = scc.decode_mpacket(
        send_and_receive(
            scc.encode_xpacket("server_uptime"),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called get_server_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(server_uptime)

# def get_socket_uptime(socket, timing=False):  # TODO UPDATE
#     if timing:
#         tstart = time()
#
#     socket.sendall(SCC.encode_xpacket("socket_uptime"))
#     socket_uptime = SCC.decode_mpacket(socket.recv(SSC.buffer_size))
#
#     if timing:
#         tend = time()
#         print(f"Called get_socket_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return float(socket_uptime)


def echo_alt(socket, msg, timing=False):  # TODO UPDATE
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("echo", msg))
    response = SCC.decode_epacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called echo_alt(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response

# High-level ping, echoes a single byte package, returns the response time
# in s. Returns -1 if no response is received.
def ping(socket):  # TODO UPDATE
    packet_out = SCC.encode_epacket("")

    tstart = time()
    socket.sendall(packet_out)              # Send 1 byte message: '0x65'
    packet_in = socket.recv(SSC.buffer_size)    # Receive response
    tend = time()

    response = SCC.decode_epacket(packet_in)

    if response == "":
        return tend - tstart
    else:
        return -1



def message(socket, msg):  # TODO UPDATE
    socket.sendall(SCC.encode_mpacket(str(msg)))

def print_schedule_info(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("print_schedule_info"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def print_schedule(socket, max_entries: int = 32):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("print_schedule", max_entries))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def initialize_schedule(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("initialize_schedule"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def allocate_schedule(socket, name: str, n_seg: int, duration: float):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket(
        "allocate_schedule", name, n_seg, duration)
    )
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def transfer_segment(socket, vals):  # TODO UPDATE
    socket.sendall(SCC.encode_spacket_fromvals(*vals))
    # Return value is the segment number, as verification.
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def transfer_schedule(socket, schedule: list, name="schedule1", timing=False):  # TODO UPDATE
    # TODO: Schedule integrity and validity should probably be checked once, and probably not here

    if timing:
        tstart = time()

    # Checking that segment numbers match with length
    if schedule[-1][0]+1 != len(schedule):
        raise AssertionError(f"The segment numbers of schedule '{name}' do not match its length!")

    # First allocate schedule
    check = allocate_schedule(s, name, len(schedule), schedule[-1][2])

    if int(check) != 1:
        raise AssertionError(f"Something went wrong transferring schedule '{name}'!")

    for i, seg in enumerate(schedule):
        socket.sendall(SCC.encode_spacket_fromvals(*(schedule[i])))
        confirm = int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
        if confirm != i:
            raise AssertionError(f"Something went wrong transferring schedule '{name}'!")
        # print("[DEBUG] Check:", i, confirm)

    if timing:
        tend = time()
        print(f"transfer_schedule(). Transferred schedule in {round((tend - tstart) * 1E3, 3)} ms")

    return 1


# Play controls
def activate_play_mode(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("activate_play_mode"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def deactivate_play_mode(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("deactivate_play_mode"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def play_start(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("play_start"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def play_stop(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("play_stop"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def get_current_step_time(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("get_current_step_time"))
    step_time_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
    return int(step_time_string[0]), int(step_time_string[1]), float(step_time_string[2])

def get_apply_Bc_period(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("get_apply_Bc_period"))
    return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def get_write_Bm_period(socket):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("get_write_Bm_period"))
    return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def set_apply_Bc_period(socket, period: float):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("set_apply_Bc_period", period))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def set_write_Bm_period(socket, period: float):  # TODO UPDATE
    socket.sendall(SCC.encode_xpacket("set_write_Bm_period", period))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
