from codec.scc2 import SCC
from time import time

def get_Bm(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_bpacket([0.] * 4))

    Bm = SCC.decode_bpacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called get_Bm(). Executed in {round((tend-tstart)*1E6, 3)} us")

    return Bm

def get_control_vals(socket, timing=False):
    """Fetches control_vals from the server, which is a list of the Bc, Ic and
    Vc that was applied to the power supplies most recently.
    """
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("get_control_vals"))

    control_vals_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
    control_vals = [
        [float(B) for B in control_vals_string[0:3]],
        [float(I) for I in control_vals_string[3:6]],
        [float(V) for V in control_vals_string[6:9]]]

    if timing:
        tend = time()
        print(f"Called get_control_vals(). Executed in {round((tend-tstart)*1E6, 3)} us")

    return control_vals


def get_server_uptime(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("server_uptime"))
    server_uptime = SCC.decode_mpacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called get_server_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(server_uptime)

def get_socket_uptime(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_xpacket("socket_uptime"))
    socket_uptime = SCC.decode_mpacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called get_socket_uptime(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return float(socket_uptime)

def echo(socket, msg, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_epacket(str(msg)))
    response = SCC.decode_epacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called echo(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return response

def echo_alt(socket, msg, timing=False):
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
def ping(socket):
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

def set_Bc(socket, Bc, timing=False):
    if len(Bc) != 3:
        raise AssertionError(f"Bc must be an array of length 3 (given: {len(Bc)}!")

    if timing:
        tstart = time()

    socket.sendall(SCC.encode_cpacket(Bc))
    confirm = SCC.decode_mpacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called set_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

def reset_Bc(socket, timing=False):
    if timing:
        tstart = time()

    socket.sendall(SCC.encode_cpacket([0., 0., 0.]))
    confirm = SCC.decode_mpacket(socket.recv(SSC.buffer_size))

    if timing:
        tend = time()
        print(f"Called reset_Bc(). Executed in {round((tend - tstart) * 1E6, 3)} us")

    return int(confirm)

def message(socket, msg):
    socket.sendall(SCC.encode_mpacket(str(msg)))

def print_schedule_info(socket):
    socket.sendall(SCC.encode_xpacket("print_schedule_info"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def print_schedule(socket, max_entries: int = 32):
    socket.sendall(SCC.encode_xpacket("print_schedule", max_entries))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def initialize_schedule(socket):
    socket.sendall(SCC.encode_xpacket("initialize_schedule"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def allocate_schedule(socket, name: str, n_seg: int, duration: float):
    socket.sendall(SCC.encode_xpacket(
        "allocate_schedule", name, n_seg, duration)
    )
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def transfer_segment(socket, vals):
    socket.sendall(SCC.encode_spacket_fromvals(*vals))
    # Return value is the segment number, as verification.
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def transfer_schedule(socket, schedule: list, name="schedule1", timing=False):
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
def activate_play_mode(socket):
    socket.sendall(SCC.encode_xpacket("activate_play_mode"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def deactivate_play_mode(socket):
    socket.sendall(SCC.encode_xpacket("deactivate_play_mode"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def play_start(socket):
    socket.sendall(SCC.encode_xpacket("play_start"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def play_stop(socket):
    socket.sendall(SCC.encode_xpacket("play_stop"))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def get_current_step_time(socket):
    socket.sendall(SCC.encode_xpacket("get_current_step_time"))
    step_time_string = SCC.decode_mpacket(socket.recv(SSC.buffer_size)).split(",")
    return int(step_time_string[0]), int(step_time_string[1]), float(step_time_string[2])

def get_apply_Bc_period(socket):
    socket.sendall(SCC.encode_xpacket("get_apply_Bc_period"))
    return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def get_write_Bm_period(socket):
    socket.sendall(SCC.encode_xpacket("get_write_Bm_period"))
    return float(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))

def set_apply_Bc_period(socket, period: float):
    socket.sendall(SCC.encode_xpacket("set_apply_Bc_period", period))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1

def set_write_Bm_period(socket, period: float):
    socket.sendall(SCC.encode_xpacket("set_write_Bm_period", period))
    return int(SCC.decode_mpacket(socket.recv(SSC.buffer_size)))  # Return 1
