import sys
import socket
from time import time, sleep
from hashlib import blake2b

from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.codec.scc2q as scc
import helmholtz_cage_toolkit.client_functions as cf

"""
Example of how to set up a client using Python scripting. The main 
advantages of using a scripted interface over the GUI are:
 - A greater degree of control over the client behaviour.
 - Lower implementation time for functionality not already in the GUI.
 - This example uses the `socket` standard library, which may come with
 performance benefits over the QTcpSocket implementation.
 
This file shows how to set up the socket, connect to the server, and call most
of the functions included in `client_function.py`.
"""


# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777

test_schedule_name = "test_schedule_name"

test_schedule = [
    [0, 6, 0.0, 0.0, 0.0, 0.0],
    [1, 6, 3.0, 1.0, 0.0, 0.0],
    [2, 6, 5.0, 2.0, 0.0, 0.0],
    [3, 6, 7.0, 3.0, 0.0, 0.0],
    [4, 6, 9.0, 4.0, 0.0, 0.0],
    [5, 6, 10.0, 0.0, 0.0, 0.0],
]

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

        print(""); sleep(1)


        # ==== Ping and print response time:
        i = 0
        n_pings = 8
        pings = [0.]*n_pings
        print(f"Testing connection with {n_pings} pings...")

        while i < n_pings:
            pings[i] = cf.ping(s)
            print(f" {str(i).rjust(3)}: {int(pings[i]*1E6)} \u03bcs")
            i += 1

        print(f"Average ping time: {round(sum(pings)/n_pings*1E6, 3)} \u03bcs")
        print(""); sleep(1)


        # ==== Echo
        echo_message = "Echo message!"
        print("echo():     ", cf.echo(s, echo_message, timing=timing))
        print("echo_alt(): ", cf.echo_alt(s, echo_message, timing=timing))
        print(""); sleep(1)


        # ==== Message to server
        message = "Hello server!"
        print("message(): ", cf.message(s, message))
        print(""); sleep(1)


        # ==== Manual control of Bc
        print("Manual control of Bc:")
        Bc_desired = [20., 30., 40.]
        print("Before:", cf.get_control_vals(s, timing=timing))
        print("set_Bc():", cf.set_Bc(s, Bc_desired, timing=timing))
        sleep(1)
        print("After apply:", cf.get_control_vals(s))
        print("reset_Bc():", cf.reset_Bc(s, timing=timing))
        sleep(1)
        print("After reset", cf.get_control_vals(s))
        print(""); sleep(1)


        # ==== Bm field measurement
        print("Bm:", cf.get_Bm(s, timing=timing), "nT")
        print(""); sleep(1)


        # ==== Schedule initialization and allocation
        print("initialize_schedule():",
              cf.initialize_schedule(s))
        print("allocate_schedule():",
              cf.allocate_schedule(s, "my_cool_schedule", 20, 60.))
        print(""); sleep(1)


        # ==== Schedule transfer
        print("Transferring schedule:")
        print(
            cf.transfer_schedule(
                s, test_schedule, test_schedule_name, timing=timing
            )
        )
        print(""); sleep(1)


        # ==== Schedule info
        sch_name, sch_length, sch_duration = cf.get_schedule_info(s)
        print("Schedule details sent by server:")
        print("Schedule name:    ", sch_name)
        print("Schedule length:  ", sch_length, "segments")
        print("Schedule duration:", sch_duration, "s")
        print(""); sleep(1)


        # ==== Schedule verification
        print("Hash of server-side schedule:", cf.get_schedule_hash(s))
        print("Hash of local copy:", cf.schedule_hash(test_schedule))
        print(""); sleep(1)
        print("Automatic verification of schedule using verify_schedule():")
        print(cf.verify_schedule(s, test_schedule))  # True if hashes match
        print(""); sleep(1)


        # ==== Schedule playback controls
        print("activate_play_mode()", cf.activate_play_mode(s))
        print("play_start()", cf.play_start(s))
        sleep(5)
        step_current, steps, time_current = cf.get_current_time_step(s)
        print(f"Current step: {step_current}/{steps} ({time_current} s)")
        sleep(6)
        print("Schedule is done now")
        print(""); sleep(1)


        # ==== Manually stop playback midway through
        print("play_start()", cf.play_start(s))
        sleep(2)
        step_current, steps, time_current = cf.get_current_time_step(s)
        print(f"Current step: {step_current}/{steps} ({time_current} s)")
        sleep(2)
        print("play_stop()", cf.play_stop(s))
        sleep(0.1)
        # Playback controls should have automatically reset to start (step -1):
        step_current, steps, time_current = cf.get_current_time_step(s)
        print(f"Current step: {step_current}/{steps} ({time_current} s)")
        print("deactivate_play_mode()", cf.deactivate_play_mode(s))
        print(""); sleep(1)


        # ==== Thread loop period configuration
        period_old = cf.get_apply_Bc_period(s)
        period_new = 0.001
        print(f"Setting apply_Bc_period from {period_old} to {period_new}")
        print(cf.set_apply_Bc_period(s, period_new))
        sleep(0.1)

        cf.set_apply_Bc_period(s, 0.1) # Reset back
        print(""); sleep(1)


        # ==== Uptimes
        print(f"Socket uptime {round(cf.get_socket_uptime(s), 3)} s")
        print(f"Server uptime {round(cf.get_server_uptime(s), 3)} s")
        print(""); sleep(3)


        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)