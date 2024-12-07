from time import time
from socket import socket
from hashlib import blake2b

from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.scc.scc4 as codec


def send_and_receive(packet,
                     socket_obj,
                     datastream: QDataStream = None,
                     buffer_size: int = codec.packet_size,
                     timeout_ms: int = 1000):
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
        if socket_obj.waitForReadyRead(timeout_ms):
            # tr = time()  # [TIMING]
            # print(f"send_and_receive(): {int((tr-ts)*1E6)} \u03bcs")  # [TIMING]
            return datastream.readRawData(buffer_size)
        # If no response was received within `timeout_ms`, call it a failure
        else:
            print(f"No response received to packet {packet}")
            return None

    # If something other than a supported socket was given
    else:
        raise AssertionError(f"Unsupported socket type given: `{type(socket_obj)}`")


# ==== UTILITY ====

def ping(socket, datastream: QDataStream = None):
    """High-level ping, echoes an empty e-packet, returns the response time
    in s. Returns -1 if no response is received.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    # Assemble packet before starting timer
    packet_out = codec.encode_epacket("")  # Packet will be 0x65 + n * 0x23

    tstart = time()
    packet_in = send_and_receive(packet_out, socket, datastream=datastream)
    tend = time()

    # Verification
    # print("[DEBUG] packet_in:", packet_in)  # TODO REMOVE
    response = codec.decode_epacket(packet_in)
    if response == "":
        return tend - tstart
    else:
        return -1


def ping_n(socket, n=8, datastream: QDataStream = None):
    """Pings n times, calculates the average ping time, and returns it.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    # Assemble packet before starting timer
    times = [0.]*n

    for i in range(n):
        packet_out = codec.encode_epacket("")  # Packet will be 0x65 + n * 0x23

        tstart = time()
        packet_in = send_and_receive(packet_out, socket, datastream=datastream)
        tend = time()

        # Verification
        response = codec.decode_epacket(packet_in)
        if response != "":
            return -1
        else:
            times[i] = tend-tstart

    return sum(times)/len(times)


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

    response = codec.decode_epacket(
        send_and_receive(
            codec.encode_epacket(str(msg)),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called echo(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response


def echo_alt(socket, # TODO EVALUATE
             msg,
             datastream: QDataStream = None,
             timing=False):
    """Alternative implementation of echo(), implemented with an x-packet as
    the outbound package, instead of an e-packet. Its purpose is mainly for
    debugging the x-packet parsing stack on the server side.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if timing:
        tstart = time()

    response = codec.decode_epacket(
        send_and_receive(
            codec.encode_xpacket("echo", str(msg)),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called echo_alt(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response

# def echo_alt(socket, msg, timing=False):
#     if timing:
#         tstart = time()
#
#     socket.sendall(SCC.encode_xpacket("echo", msg))
#     response = SCC.decode_epacket(socket.recv(SSC.buffer_size))
#
#     if timing:
#         tend = time()
#         print(f"Called echo_alt(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return response


def get_server_uptime(socket,
                      datastream: QDataStream = None,
                      timing=False):
    """Requests and returns the server uptime.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    server_uptime = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_server_uptime"),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called get_server_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(server_uptime)


def get_socket_uptime(socket, # TODO EVALUATE
                      datastream: QDataStream = None,
                      timing=False):
    """Requests the uptime of the socket connection from the perspective of
    the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    socket_uptime = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_socket_uptime"),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called get_socket_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(socket_uptime)


def get_socket_info(socket,
                    datastream: QDataStream = None,
                    timing=False):
    """Request an m-packet with some information about the client from the
    perspective of the server:
    1. The time for which the client socket has been active
    2. The client address
    3. The client port

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    uptime, address, port = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_socket_info"),
            socket,
            datastream=datastream
        )
    ).split(",")

    if timing:
        tend = time()
        print(f"Called get_socket_info(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(uptime), address, int(port)

# def get_socket_uptime(socket, timing=False):
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


def message(socket,
            msg,
            datastream: QDataStream = None):
    """Requests and returns the server uptime.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_mpacket(str(msg)),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

# def message(socket, msg):
#     socket.sendall(SCC.encode_mpacket(str(msg)))


# ==== FIELD CONTROL ====
def get_control_vals(socket, # TODO EVALUATE
                     datastream: QDataStream = None,
                     timing=False):
    """Requests the current control_vals from the server, which is a list of
    the Bc, Ic and Vc that were applied to the power supplies most recently.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    control_vals_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_control_vals"),
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
    """Manually set a control field vector Bc when in manual mode.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if len(Bc) != 3:
        raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")

    if timing:
        tstart = time()

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_cpacket(Bc),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called set_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)


def get_Bc(socket,
           datastream: QDataStream = None,
           timing=False):
    """Requests and returns the most recent Bc value from the server.

    The server will return c-packet with the current Bc value whenever a
    client sends this command.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if timing:
        tstart = time()

    Bc = codec.decode_cpacket(
        send_and_receive(
            codec.encode_xpacket("get_Bc"),
            socket,
            datastream=datastream
        )
    )

    if timing:
        tend = time()
        print(f"Called get_Bc(). Executed in {int((tend-tstart)*1E6)} us")

    return Bc


def reset_Bc(socket, # TODO DEPRECATED?
             datastream: QDataStream = None,
             timing=False):
    """Reset a control field vector Bc back to [0. 0. 0.] when in manual mode.

    When in `play mode`, instead use `play_stop()` to stop playback, which
    also automatically calls a Bc reset command.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if timing:
        tstart = time()

    confirm = set_Bc(socket, [0., 0., 0.], datastream=datastream)

    if timing:
        tend = time()
        print(f"Called reset_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

# def set_Bc(socket, Bc, timing=False):
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
# def reset_Bc(socket, timing=False):
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


# ==== FIELD MEASUREMENT
def get_Bm(socket,
           datastream: QDataStream = None,
           timing=False):
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

    r = codec.decode_bpacket(
        send_and_receive(
            codec.encode_bpacket(0., [0.]*3),
            socket,
            datastream=datastream
        )
    )
    # packet_in = send_and_receive(
    #     codec.encode_bpacket(0., [0.]*3),
    #     socket,
    #     datastream=datastream
    # )
    # print(packet_in)
    # Bm = codec.decode_bpacket(packet_in)

    if timing:
        tend = time()
        print(f"Called get_Bm(). Executed in {int((tend-tstart)*1E6)} us")

    return r[0], [r[1], r[2], r[3]]


def get_telemetry(socket,
                  datastream: QDataStream = None):
    """Requests and returns a t-packet with telemetry from the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    tm, i_step, Im, Bm, Bc = codec.decode_tpacket(
        send_and_receive(
            codec.encode_tpacket(0., 0, *[[0.]*3]*3),
            socket,
            datastream=datastream
        )
    )
    return tm, i_step, Im, Bm, Bc


# ==== SCHEDULE ====
def print_schedule_info( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Prints schedule info to the console *of the server*. Mainly used for
    debugging with visual access to the server console output.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("print_schedule_info"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def print_schedule( # TODO EVALUATE
    socket,
    max_entries: int = 32,
    datastream: QDataStream = None):
    """Prints schedule info to the console *of the server*. Mainly used for
    debugging with visual access to the server console output.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("print_schedule", max_entries),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_schedule_info( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Gets some information about the schedule on the server side. Gets the

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    name, length_string, duration_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_schedule_info"),
            socket,
            datastream=datastream
        )
    ).split(",")
    return name, int(length_string), float(duration_string)


def get_schedule_hash( # TODO EVALUATE
    socket,
    datastream: QDataStream = None,
    timeout_ms=10000):
    """Requests the server to hash its schedule and send the result.

    For large schedules (>1M segments), calculating the hash can take over one
    second, which is the default timeout for the send_and_receive() call.
    Therefore, get_schedule_hash() allows you to raise this limit by specifying
    a value for `timeout_ms`, set to 10 seconds by default.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    hash_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_schedule_hash"),
            socket,
            datastream=datastream,
            timeout_ms=timeout_ms,
        )
    )
    return hash_string


def initialize_schedule( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Initialize a schedule on the server's end.

    The server has a single dynamic buffer object in which the schedule lives.
    This function resets it to its default state.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("initialize_schedule"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def allocate_schedule( # TODO EVALUATE
    socket,
    name: str,
    n_seg: int,
    duration: float,
    datastream: QDataStream = None):
    """Allocates the schedule buffer on the server's end, in anticipation of
    a schedule.

    The server has a single dynamic buffer object in which the schedule lives.
    This function configures this buffer object so that it will fit the
    schedule. It takes three arguments:
     - name     [str] Name of the schedule
     - n_seg    [int] Number of segments in the schedule
     - duration [float] Realtime duration of the schedule

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    print(f"[DEBUG] allocate_schedule(): {socket}, {name}({type(name)}), {n_seg}({type(n_seg)}), {float(duration)}({type(float(duration))})")
    packet_in = send_and_receive(
        codec.encode_xpacket("allocate_schedule", name, n_seg, float(duration)),
        socket,
        datastream=datastream
    )
    print(f"[DEBUG] allocate_schedule(): packet_in: {packet_in}")
    confirm = codec.decode_mpacket(packet_in)
    return int(confirm)


def transfer_segment( # TODO EVALUATE
    socket,
    segment,
    datastream: QDataStream = None):
    """Transfers a single schedule segment to the server.

    This function is mainly for debugging purposes, and is not intended to be
    wrapped by `transfer_schedule()`.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_spacket(*segment),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def transfer_schedule(  # TODO Incorporate schedule validation tools
    socket,
    schedule,
    name: str = "schedule1",
    datastream: QDataStream = None,
    timing=False):
    """Sequentially transfers a schedule to the server.

    This function is meant to be a one-shot solution to transferring a
    schedule. It will first pre-allocate the schedule buffer on the server
    side, and then sequentially transfer the schedule segment by segment.

    Every s-packet contains a single segment, as dictated by the SCC2 codec.
    The server sends a confirmation for each package received, which this
    function will also examine, raising an exception if something went wrong.

    An optional schedule name can be specified.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if timing:
        tstart = time()

    # TODO: Schedule integrity and validity should probably be checked once,
    #  but probably not here -> Make separate integrity check function.
    # Checking that segment numbers in schedule match with its length
    if schedule[-1][0]+1 != len(schedule):
        raise AssertionError(f"The segment numbers of schedule '{name}' do not match its length!")

    # # TODO: Is this desirable behaviour, given that user already has control
    # #  of this aspect by choosing to pass a QDataStream as an argument?
    # # To help with performance, transfer_schedule() assumes that it is allowed
    # # uninterrupted access to the TCP connection. If using a QTcpSocket and
    # # no datastream is pre-specified, `transfer_schedule()` will now make one
    # # once, to speed up transfer.
    # elif type(socket) == QTcpSocket and not datastream:
    #     datastream = QDataStream(socket_obj)

    print(f"[DEBUG] transfer_schedule(), about to do:")
    print(f"[DEBUG  allocate_schedule({socket}, {name}|{type(name)}, {len(schedule)}|{type(len(schedule))}, {schedule[-1][2]}|{type(schedule[-1][2])}")
    # First allocate schedule
    confirm = allocate_schedule(
        socket, name, len(schedule), schedule[-1][2], datastream=datastream
    )
    if int(confirm) != 1:
        raise AssertionError(f"Failed to allocate schedule '{name}'!")

    # Loop over segments and transfer one by one.
    for i, seg in enumerate(schedule):
        confirm = codec.decode_mpacket(
            send_and_receive(
                codec.encode_spacket(*(schedule[i])),
                socket,
                datastream=datastream
            )
        )
        # Validation (server will return segment number)
        if int(confirm) != i:
            raise AssertionError(f"Failed to transfer segment {i} of schedule '{name}'!")

    if timing:
        tend = time()
        print(f"transfer_schedule(). Transferred schedule in {round((tend - tstart) * 1E3, 3)} ms")

    return 1


def schedule_hash(schedule: list): # TODO EVALUATE
    """Creates a schedule digest using the BLAKE2b algorithm"""
    return blake2b(array(schedule).tobytes(), digest_size=64).hexdigest()


def verify_schedule( # TODO EVALUATE
    socket,
    schedule,
    datastream: QDataStream = None,
    timeout_ms=10000):
    """Function to compare the integrity of a transferred schedule with the
    local copy.

    It achieves this by casting the string into a bytearray by first casting
    it to a Numpy array.
    It does this by hashing the string of the complete schedule
    locally, and requesting the server to send the hash from its side.
    This function then outputs the boolean result of the comparison.

    For large schedules (>1M segments), calculating the hash can take some
    time, and for schedules of this size, verify_schedule automatically
    estimates some appropriate TCP interaction timeout, according to:

    timeout_ms = 125% * ( computation_factor * 1,000 [ms] / 1,000,000 )

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    # For large schedules, estimate raised timeout:
    if len(schedule) >= 1_000_000:
        cf = 1.0
        timeout_ms = int(1.25*(cf*1000/len(schedule)))
        print("Large schedule detected. Dynamically set timeout to {:.3f} s".format(
            timeout_ms))
        print("If the verification fails due to timeout, please increase the timeout limit")


    hash_schedule_server = get_schedule_hash(
        socket,
        timeout_ms=timeout_ms,
        datastream=datastream)
    hash_schedule_local = schedule_hash(schedule)

    return hash_schedule_local == hash_schedule_server



# def print_schedule_info(socket):
#     socket.sendall(SCC.encode_xpacket("print_schedule_info"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#
# def print_schedule(socket, max_entries: int = 32):
#     socket.sendall(SCC.encode_xpacket("print_schedule", max_entries))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#
# def initialize_schedule(socket):
#     socket.sendall(SCC.encode_xpacket("initialize_schedule"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#
# def allocate_schedule(socket, name: str, n_seg: int, duration: float):
#     socket.sendall(SCC.encode_xpacket(
#         "allocate_schedule", name, n_seg, duration)
#     )
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#
# def transfer_segment(socket, vals):
#     socket.sendall(SCC.encode_spacket(*vals))
#     # Return value is the segment number, as verification.
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#
# def transfer_schedule(socket, schedule: list, name="schedule1", timing=False):
#
#     if timing:
#         tstart = time()
#
#     # Checking that segment numbers match with length
#     if schedule[-1][0]+1 != len(schedule):
#         raise AssertionError(f"The segment numbers of schedule '{name}' do not match its length!")
#
#     # First allocate schedule
#     check = allocate_schedule(s, name, len(schedule), schedule[-1][2])
#
#     if int(check) != 1:
#         raise AssertionError(f"Something went wrong transferring schedule '{name}'!")
#
#     for i, seg in enumerate(schedule):
#         socket.sendall(SCC.encode_spacket(*(schedule[i])))
#         confirm = int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))
#         if confirm != i:
#             raise AssertionError(f"Something went wrong transferring schedule '{name}'!")
#         # print("[DEBUG] Check:", i, confirm)
#
#     if timing:
#         tend = time()
#         print(f"transfer_schedule(). Transferred schedule in {round((tend - tstart) * 1E3, 3)} ms")
#
#     return 1


# ==== PLAY CONTROLS ====
def activate_play_mode( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Switches the field vector control thread from `manual mode` to
    `play mode`. When in play mode, the server will be poised to start schedule
    playback using the designated controls, so calling activate_play_mode()
    also serves as an `arming switch`.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("activate_play_mode"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

def deactivate_play_mode( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Switches the field vector control thread from `play mode` to
    `manual mode`.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("deactivate_play_mode"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

def play_start( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Instructs the server to immediately start schedule playback.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("play_start"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

def play_stop( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Instructs the server to immediately stop schedule playback. The
    playback position will be reset to the start, and so this is not a pause,
    but indeed a stop.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("play_stop"),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_current_time_step( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Requests the current instantaneous playback time at the server side.

    The server plays back schedules by time marching, switching to the next
    schedule segments at the appropriate moment. This function provides insight
    into that process at the instant the function is called.

    Returns three values:
        1. Current segment being played back
        2. Total number of segments in schedule
        3. Current instantaneous playback time

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    ts_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_current_time_step"),
            socket,
            datastream=datastream
        )
    ).split(",")
    #      Current segment    n segments         Instantaneous playback time
    return int(ts_string[0]), int(ts_string[1]), float(ts_string[2])


def get_play_mode( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Requests the current value of play_mode.

    True means that the Bc thread on the server is looping in `play mode`
    False means that the Bc thread is looping in `manual mode`.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    play_mode_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_play_mode"),
            socket,
            datastream=datastream
        )
    )
    if play_mode_string == "True":
        return True
    elif play_mode_string == "False":
        return False
    else:
        raise AssertionError("Received invalid play_mode '{play_mode_string}'")

def get_play_status( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Requests the current value of play_status.

    Can only have two values: "play" or "stop".

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    play_status_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_play_status"),
            socket,
            datastream=datastream
        )
    )
    return play_status_string



# def activate_play_mode(socket):
#     socket.sendall(SCC.encode_xpacket("activate_play_mode"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
#
# def deactivate_play_mode(socket):
#     socket.sendall(SCC.encode_xpacket("deactivate_play_mode"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
#
# def play_start(socket):
#     socket.sendall(SCC.encode_xpacket("play_start"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
#
# def play_stop(socket):
#     socket.sendall(SCC.encode_xpacket("play_stop"))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
#
# def get_current_step_time(socket):
#     socket.sendall(SCC.encode_xpacket("get_current_step_time"))
#     step_time_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
#     return int(step_time_string[0]), int(step_time_string[1]), float(step_time_string[2])


# ==== CONFIGURATION ====
def get_apply_Bc_period( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Getter of field control vector thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    period_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_apply_Bc_period"),
            socket,
            datastream=datastream
        )
    )
    return float(period_string)

def set_apply_Bc_period( # TODO EVALUATE
    socket,
    period: float,
    datastream: QDataStream = None):
    """Setter of field control vector thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_apply_Bc_period", period),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_write_Bm_period( # TODO STALE
    socket,
    datastream: QDataStream = None):
    """Getter of field measurement thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    period_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_write_Bm_period"),
            socket,
            datastream=datastream
        )
    )
    return float(period_string)

def set_write_Bm_period( # TODO STALE
    socket,
    period: float,
    datastream: QDataStream = None):
    """Setter of field measurement thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_write_Bm_period", period),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_write_tmBmIm_period( # TODO EVALUATE
    socket,
    datastream: QDataStream = None):
    """Getter of field measurement thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    period_string = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_write_tmBmIm_period"),
            socket,
            datastream=datastream
        )
    )
    return float(period_string)

def set_write_tmBmIm_period( # TODO STALE
    socket,
    period: float,
    datastream: QDataStream = None):
    """Setter of field measurement thread looping period [s].

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_write_tmBmIm_period", period),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def set_Bm_sim( # TODO EVALUATE
    socket,
    Bm_sim,
    datastream: QDataStream = None):
    """Setter of Bm_sim

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if len(Bm_sim) != 3:
        raise AssertionError(f"Bm_sim given is not length 3 but length {len(Bm_sim)}!")

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_Bm_sim",
                                 float(Bm_sim[0]),
                                 float(Bm_sim[1]),
                                 float(Bm_sim[2])),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_Bm_sim(socket, # TODO EVALUATE
               datastream: QDataStream = None):
    """Getter of Bm_sim

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    Bm_sim = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_Bm_sim"),
            socket,
            datastream=datastream
        )
    ).split(",")

    return [float(Bm_sim[0]), float(Bm_sim[1]), float(Bm_sim[2])]


def get_serveropt_spoof_Bm(
    socket,
    datastream: QDataStream = None):
    """Getter of serveropt_spoof_Bm.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    serveropt_spoof_Bm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_serveropt_spoof_Bm"),
            socket,
            datastream=datastream
        )
    )
    return bool(int(serveropt_spoof_Bm))

def set_serveropt_spoof_Bm(
    socket,
    serveropt_spoof_Bm: bool,
    datastream: QDataStream = None):
    """Setter of serveropt_spoof_Bm

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    # print(f"[DEBUG] get_serveropt_Bm_sim('{serveropt_Bm_sim}')")

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_serveropt_spoof_Bm", int(serveropt_spoof_Bm)),
            socket,
            datastream=datastream
        )
    )
    return bool(int(confirm))


def set_Br(
    socket,
    Br,
    datastream: QDataStream = None):
    """Setter of Br

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if len(Br) != 3:
        raise AssertionError(f"Br given is not length 3 but length {len(Br)}!")

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_Br",
                                 float(Br[0]),
                                 float(Br[1]),
                                 float(Br[2])),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)


def get_Br(socket,
           datastream: QDataStream = None):
    """Getter of Br

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    Br = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_Br"),
            socket,
            datastream=datastream
        )
    ).split(",")

    return [float(Br[0]), float(Br[1]), float(Br[2])]

# def get_apply_Bc_period(socket):
#     socket.sendall(SCC.encode_xpacket("get_apply_Bc_period"))
#     return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

# def get_write_Bm_period(socket):
#     socket.sendall(SCC.encode_xpacket("get_write_Bm_period"))
#     return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

# def set_apply_Bc_period(socket, period: float):
#     socket.sendall(SCC.encode_xpacket("set_apply_Bc_period", period))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

# def set_write_Bm_period(socket, period: float):
#     socket.sendall(SCC.encode_xpacket("set_write_Bm_period", period))
#     return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
