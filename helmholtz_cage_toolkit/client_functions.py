"""
Description here TODO

If implementing this function with QTcpSocket, you can specify a re-usable
QDataStream object to substantially increase performance.

"""

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
         datastream: QDataStream = None):
    """Sends a message `msg` to the server, which will in turn echo it back.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    response = codec.decode_epacket(
        send_and_receive(
            codec.encode_epacket(str(msg)),
            socket,
            datastream=datastream
        )
    )

    return response


# def echo_alt(socket, # TODO EVALUATE
#              msg,
#              datastream: QDataStream = None,
#              timing=False):
#     """Alternative implementation of echo(), implemented with an x-packet as
#     the outbound package, instead of an e-packet. Its purpose is mainly for
#     debugging the x-packet parsing stack on the server side.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#
#     if timing:
#         tstart = time()
#
#     response = codec.decode_epacket(
#         send_and_receive(
#             codec.encode_xpacket("echo", str(msg)),
#             socket,
#             datastream=datastream
#         )
#     )
#
#     if timing:
#         tend = time()
#         print(f"Called echo_alt(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return response


def get_server_uptime(socket,
                      datastream: QDataStream = None):
    """Requests and returns the server uptime.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    server_uptime = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_server_uptime"),
            socket,
            datastream=datastream
        )
    )

    return float(server_uptime)


# def get_socket_uptime(socket, # TODO EVALUATE
#                       datastream: QDataStream = None,
#                       timing=False):
#     """Requests the uptime of the socket connection from the perspective of
#     the server.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     if timing:
#         tstart = time()
#
#     socket_uptime = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("get_socket_uptime"),
#             socket,
#             datastream=datastream
#         )
#     )
#
#     if timing:
#         tend = time()
#         print(f"Called get_socket_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")
#
#     return float(socket_uptime)


def get_socket_info(socket,
                    datastream: QDataStream = None):
    """Request an m-packet with some information about the client from the
    perspective of the server:
    1. The time for which the client socket has been active
    2. The client address
    3. The client port

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    uptime, address, port = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_socket_info"),
            socket,
            datastream=datastream
        )
    ).split(",")

    return float(uptime), address, int(port)


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


# ==== FIELD CONTROL ====
# def get_control_vals(socket, # TODO EVALUATE
#                      datastream: QDataStream = None,
#                      timing=False):
#     """Requests the current control_vals from the server, which is a list of
#     the Bc, Ic and Vc that were applied to the power supplies most recently.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     if timing:
#         tstart = time()
#
#     control_vals_string = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("get_control_vals"),
#             socket,
#             datastream=datastream
#         )
#     ).split(",")
#
#     # socket.sendall(SCC.encode_xpacket("get_control_vals"))
#
#     # control_vals_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
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
           datastream: QDataStream = None):
    """Manually set a control field vector Bc when in manual mode.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    if len(Bc) != 3:
        raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_cpacket(Bc),
            socket,
            datastream=datastream
        )
    )

    return int(confirm)


def get_Bc(socket,
           datastream: QDataStream = None):
    """Requests and returns the most recent Bc value from the server.

    The server will return c-packet with the current Bc value whenever a
    client sends this command.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    Bc = codec.decode_cpacket(
        send_and_receive(
            codec.encode_xpacket("get_Bc"),
            socket,
            datastream=datastream
        )
    )

    return Bc


def reset_Bc(socket,
             datastream: QDataStream = None):
    """Reset a control field vector Bc back to [0. 0. 0.] when in manual mode.

    When in `play mode`, instead use `play_stop()` to stop playback, which
    also automatically calls a Bc reset command.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    confirm = set_Bc(socket, [0., 0., 0.], datastream=datastream)

    return confirm


def get_V_board(socket,
                datastream: QDataStream = None):
    """Requests and returns a m-packet with board voltage from the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    V_board = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_V_board"),
            socket,
            datastream=datastream
        )
    )
    return float(V_board)


def get_aux_adc(socket,
                datastream: QDataStream = None):
    """Requests the voltage of the auxiliary ADC channel on the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    aux_adc = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_aux_adc"),
            socket,
            datastream=datastream
        )
    )
    return float(aux_adc)


def get_aux_dac(socket,
                datastream: QDataStream = None):
    """Requests the voltage of the six auxiliary DAC channels on the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    aux_dac = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_aux_dac"),
            socket,
            datastream=datastream
        )
    ).split(",")

    return [float(val) for val in aux_dac]


def set_aux_dac(socket,
                dac_vals: list,
                datastream: QDataStream = None):
    """Sets the voltage of the six auxiliary DAC channels on the server.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    if len(dac_vals) != 6:
        raise AssertionError(f"dac_vals must be a list of length 6 (given: {len(dac_vals)}!")

    # [ch1, ch2, ch3, ch4, ch5, ch6] = dac_vals
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_aux_dac", *dac_vals),
            socket,
            datastream=datastream
        )
    ).split(",")

    return [float(val) for val in confirm]


def get_output_enable(socket,
                      datastream: QDataStream = None):
    """Requests the state of the <output_enable> hardware enable functionality.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    enable = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_output_enable"),
            socket,
            datastream=datastream
        )
    )

    return bool(int(enable))


def set_output_enable(socket,
                      enable: bool,
                      datastream: QDataStream = None):
    """Enables or disables the current channel outputs via the hardware enable.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_output_enable", str(int(enable))),
            socket,
            datastream=datastream
        )
    )

    return bool(int(confirm))


def set_params_VB(socket,
                  bx0, bx1, by0, by1, bz0, bz1,
                  datastream: QDataStream = None):
    """Manually set the transfer function parameters for PSU control voltage Vc
    to coil pair flux density output B_out. The preferred ways of setting these
    parameters are to either set it once via the server_config, or
    auto-calibrate it on the server. But the possibility to update it here is
    added as a third option.

    Besides the socket and datastream, this function takes six arguments, which
    are three [b0, b1] pairs, one for each coil pairs. These parameters map to
    a linear transfer function; for example by0 and by1:

        B_out_y = b0y + b1y * Vc

    In other words, b0 is the constant term, b1 is the linear term.

    You do not have to specify all parameters to run this function. You can
    just specify the ones you wish to update, and input False for all others.
    All False values will be ignored by the server during interpretation.

    The server returns a string that when converted to an integer denotes the
    number of VB parameters that were updated, so six when all were specified.
    This function returns 1 when these two numbers match.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    vals = [bx0, bx1, by0, by1, bz0, bz1]
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_params_VB", *vals),
            socket,
            datastream=datastream
        )
    )

    if int(confirm) == sum([1 for i in vals if i is not False]):
        output = 1
    else:
        output = 0

    return output


def get_params_VB(socket,
                  datastream: QDataStream = None):
    """Requests the transfer function parameters for PSU control voltage Vc to
    coil pair flux density output B_out. This function will output it as:

        [ [bx0, bx1], [by0, by1], [bz0, bz1] ]

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    p = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_params_VB"),
            socket,
            datastream=datastream
        )
    ).split(",")
    output = [
        [float(p[0]), float(p[1])],
        [float(p[2]), float(p[3])],
        [float(p[4]), float(p[5])]
    ]
    return output


# ==== FIELD MEASUREMENT
def get_Bm(socket,
           datastream: QDataStream = None):
    """Requests and returns the most recent Bm value from the server.

    The server will return b-packet with the current Bm value whenever a
    client sends a b-packet. The server just reads the packet type; the
    contents of the b-package sent by the client does not matter, so this
    function sends four zero float values.

    The returning b-package with the Bm values are then decoded and returned.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    r = codec.decode_bpacket(
        send_and_receive(
            codec.encode_bpacket(0., [0.]*3),
            socket,
            datastream=datastream
        )
    )

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

def print_schedule_info(
    socket,
    max_entries: int = 16,
    datastream: QDataStream = None):
    """Prints schedule info to the console *of the server*. Mainly used for
    debugging with visual access to the server console output.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("print_schedule_info", max_entries),
            socket,
            datastream=datastream
        )
    )

    return int(confirm)


def get_schedule_info(
    socket,
    generate_hash=True,
    datastream: QDataStream = None):
    """Gets some information about the schedule on the server side. Gets the
    schedule name, the length, the duration, and the hash.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    info = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_schedule_info", str(int(generate_hash))),
            socket,
            datastream=datastream
        )
    ).split(",")

    [name, length_string, duration_string, schedule_hash] = info

    return name, int(length_string), float(duration_string), schedule_hash


def initialize_schedule(
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


def allocate_schedule(
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
    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("allocate_schedule", name, n_seg, float(duration)),
            socket,
            datastream=datastream
        )
    )

    return int(confirm)


def get_schedule_segment(
    socket,
    segment_id: int,
    datastream: QDataStream = None):
    """Gets some information about the schedule on the server side. Gets the

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    segment = codec.decode_spacket(
        send_and_receive(
            codec.encode_xpacket("get_schedule_segment", segment_id),
            socket,
            datastream=datastream
        )
    )

    return segment


def set_schedule_segment(
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
    datastream: QDataStream = None):
    """Sequentially transfers a schedule to the server.

    This function is meant to be a one-shot solution to transferring a
    schedule. It will first pre-allocate the schedule buffer on the server
    side, and then sequentially transfer the schedule segment by segment.

    Every s-packet contains a single segment, as dictated by the SCC codec.
    The server sends a confirmation for each package received, which this
    function will also examine, raising an exception if something went wrong.

    An optional schedule name can be specified.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    tstart = time()

    # TODO: Schedule integrity and validity should probably be checked once,
    #  but probably not here -> Make separate integrity check function.
    # Checking that segment numbers in schedule match with its length
    if schedule[-1][0]+1 != len(schedule):
        raise AssertionError(f"The segment numbers of schedule '{name}' do not match its length!")


    # [DEV NOTE] To help with performance, transfer_schedule() can be set to
    # assume that it is allowed uninterrupted access to the TCP connection. If
    # using a QTcpSocket and no datastream is pre-specified,
    # `transfer_schedule()` will now make one once, to speed up transfer.
    #
    # However, at this time I am unsure whether this is desirable behaviour,
    # given that user already has control of this aspect by choosing to pass a
    # QDataStream as an argument. In addition, schedule transfer speed does not
    # seem a particularly nasty bottleneck, and will take some time regardless,
    # so it seems better to not congest the TCP connection and attempt to brave
    # the perilous waters of maintaining multi-client compatibility.
    #
    # elif type(socket) == QTcpSocket and not datastream:
    #     datastream = QDataStream(socket_obj)

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

    tend = time()
    # print(f"Transferred schedule in {round((tend - tstart) * 1E3, 3)} ms")

    # Return total transfer time in [s] as output:
    return tend - tstart


def get_schedule_hash(
    socket,
    datastream: QDataStream = None,
    timeout_ms=10000):
    """Requests the server to hash its schedule and send the result. It reuses
    the 'get_schedule_info' command and returns only the hash.

    For large schedules (>1M segments), calculating the hash can take over one
    second, which is the default timeout for the send_and_receive() call.
    Therefore, get_schedule_hash() allows you to raise this limit by specifying
    a value for `timeout_ms`, set to 10 seconds by default.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """

    generate_hash = True

    (_, _, _, hash_string) = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_schedule_info", generate_hash),
            socket,
            datastream=datastream,
            timeout_ms=timeout_ms,
        )
    ).split(",")
    return hash_string


def calculate_schedule_hash(schedule: list):
    """Creates a schedule digest using the BLAKE2b algorithm"""
    return blake2b(array(schedule).tobytes(), digest_size=8).hexdigest()


def verify_schedule(
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
    time, and for schedules of this size, verify_schedule() automatically
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
    hash_schedule_local = calculate_schedule_hash(schedule)

    verify = (hash_schedule_local == hash_schedule_server)

    return verify, hash_schedule_local, hash_schedule_server



# ==== PLAY CONTROLS ====

# def activate_play_mode( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Switches the field vector control thread from `manual mode` to
#     `play mode`. When in play mode, the server will be poised to start schedule
#     playback using the designated controls, so calling activate_play_mode()
#     also serves as an `arming switch`.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     confirm = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("activate_play_mode"),
#             socket,
#             datastream=datastream
#         )
#     )
#     return int(confirm)
#
# def deactivate_play_mode( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Switches the field vector control thread from `play mode` to
#     `manual mode`.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     confirm = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("deactivate_play_mode"),
#             socket,
#             datastream=datastream
#         )
#     )
#     return int(confirm)


def get_play_info(
    socket,
    datastream: QDataStream = None):
    """Requests various information about the server play mode. Returns:
        - play_mode (bool)
        - play (bool)
        - play_looping (bool)
        - n_steps (int)
        - i_step (int)
        - t_play (float)
        - t_current (float)
        - t_next (float)
    in that order.
    """
    play_info = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_play_info"),
            socket,
            datastream=datastream
        )
    ).split(",")

    [play_mode, play, play_looping, n_steps, i_step, t_play, t_current, t_next] \
        = play_info

    return bool(int(play_mode)), bool(int(play)), bool(int(play_looping)), \
        int(n_steps), int(i_step), \
        float(t_play), float(t_current), float(t_next)

def set_play_mode(
    socket,
    play_mode: bool,
    datastream: QDataStream = None):
    """Setter of server play_mode. Returns 1 if play_mode was set True and 0 if
    it was set to False.
    """

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_play_mode", play_mode),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

def set_play(
    socket,
    play: bool,
    datastream: QDataStream = None):
    """Setter of server play_mode. Returns 1 if playback was started and 0 if
    it was stopped.
    """

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_play", play),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

def set_play_looping(
    socket,
    play_looping: bool,
    datastream: QDataStream = None):
    """Setter of server play_looping. Returns 1 if playback was set to looping
    and 0 if it was set to one-shot.
    """

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_play_looping", play_looping),
            socket,
            datastream=datastream
        )
    )
    return int(confirm)

# def play_start( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Instructs the server to immediately start schedule playback.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     confirm = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("play_start"),
#             socket,
#             datastream=datastream
#         )
#     )
#     return int(confirm)
#
# def play_stop( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Instructs the server to immediately stop schedule playback. The
#     playback position will be reset to the start, and so this is not a pause,
#     but indeed a stop.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     confirm = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("play_stop"),
#             socket,
#             datastream=datastream
#         )
#     )
#     return int(confirm)
#
#
# def get_current_time_step( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Requests the current instantaneous playback time at the server side.
#
#     The server plays back schedules by time marching, switching to the next
#     schedule segments at the appropriate moment. This function provides insight
#     into that process at the instant the function is called.
#
#     Returns three values:
#         1. Current segment being played back
#         2. Total number of segments in schedule
#         3. Current instantaneous playback time
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#     ts_string = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("get_current_time_step"),
#             socket,
#             datastream=datastream
#         )
#     ).split(",")
#     #      Current segment    n segments         Instantaneous playback time
#     return int(ts_string[0]), int(ts_string[1]), float(ts_string[2])
#
#
# def get_play_mode( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Requests the current value of play_mode.
#
#     True means that the Bc thread on the server is looping in `play mode`
#     False means that the Bc thread is looping in `manual mode`.
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#
#     play_mode_string = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("get_play_mode"),
#             socket,
#             datastream=datastream
#         )
#     )
#     if play_mode_string == "True":
#         return True
#     elif play_mode_string == "False":
#         return False
#     else:
#         raise AssertionError("Received invalid play_mode '{play_mode_string}'")
#
# def get_play_status( # TODO EVALUATE
#     socket,
#     datastream: QDataStream = None):
#     """Requests the current value of play_status.
#
#     Can only have two values: "play" or "stop".
#
#     If implementing this function with QTcpSocket, you can specify a re-usable
#     QDataStream object to substantially increase performance.
#     """
#
#     play_status_string = codec.decode_mpacket(
#         send_and_receive(
#             codec.encode_xpacket("get_play_status"),
#             socket,
#             datastream=datastream
#         )
#     )
#     return play_status_string


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


def get_serveropt_mutate_Bm(
    socket,
    datastream: QDataStream = None):
    """Getter of serveropt_mutate_Bm.

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    serveropt_mutate_Bm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_serveropt_mutate_Bm"),
            socket,
            datastream=datastream
        )
    )
    return bool(int(serveropt_mutate_Bm))

def set_serveropt_mutate_Bm(
    socket,
    serveropt_mutate_Bm: bool,
    datastream: QDataStream = None):
    """Setter of serveropt_mutate_Bm

    If implementing this function with QTcpSocket, you can specify a re-usable
    QDataStream object to substantially increase performance.
    """
    # print(f"[DEBUG] get_serveropt_Bm_sim('{serveropt_Bm_sim}')")

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_serveropt_mutate_Bm", serveropt_mutate_Bm),
            socket,
            datastream=datastream
        )
    )
    return bool(int(confirm))

def get_serveropt_inject_Bm(
    socket,
    datastream: QDataStream = None):
    """Getter of serveropt_inject_Bm."""
    serveropt_mutate_Bm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("get_serveropt_inject_Bm"),
            socket,
            datastream=datastream
        )
    )
    return bool(int(serveropt_mutate_Bm))

def set_serveropt_inject_Bm(
    socket,
    serveropt_inject_Bm: bool,
    datastream: QDataStream = None):
    """Setter of serveropt_inject_Bm."""

    confirm = codec.decode_mpacket(
        send_and_receive(
            codec.encode_xpacket("set_serveropt_inject_Bm", serveropt_inject_Bm),
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