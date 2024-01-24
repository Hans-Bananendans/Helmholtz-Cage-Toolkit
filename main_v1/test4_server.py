from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from threading import Thread, Lock, main_thread, active_count

from numpy.random import random
from time import time, sleep
import codec.scc2q as scc


# Dummy functions
def instruct_DACs(Bc):  # TODO: Dummy - Implement actual functionality
    """Dummy for writing values to DAC"""
    print(f"[DEBUG] Called instruct_DACs({Bc})!")
    Ic = [B/200. for B in Bc]
    Vc = [0., 0., 0.]
    for i, B in enumerate(Bc):
        if abs(B) <= 0.1:
            Vc[i] = 0.0
        else:
            Vc[i] = 60.0

    # Return control_vals
    return [Bc, Ic, Vc]


def sample_ADCs():  # TODO: DUMMY - Implement actual functionality
    """Dummy for reading values from ADC. Outputs a Bm sample"""
    # print(f"[DEBUG] Called sample_ADCs()!")

    t = time()
    # Generate 3 dummy values of [-50,000 , +50,000] nT
    bx, by, bz = (random(3) * 100_000 - 50_000).round(1)
    return [t, bx, by, bz]


def threaded_write_Bm(datapool):
    """The thread running this function periodically samples a Bm value
     from the ADC, and thread-safely writes it to the datapool.

    To gracefully kill this thread, set datapool.kill_write_Bm to True

    TODO: Currently, this thread cannot be stopped, restarted, or its period
    adjusted. This would however be desirable. To fix this, the way this
    thread is initiated in the server thread should be changed.
    """
    print(f"Started write_Bm thread with period {datapool.write_Bm_period}")
    datapool.kill_write_Bm = False

    while not datapool.kill_write_Bm:    # Break loop when set to True
        if not datapool.pause_write_Bm:  # Pause loop when set to True
            t0 = time()
            datapool.write_Bm(sample_ADCs())
            sleep(max(0., datapool.write_Bm_period - (time() - t0)))
        else:
            sleep(datapool.write_Bm_period)


    print(f"Closing write_Bm thread")


def threaded_apply_Bc(datapool):
    """The thread running this function will periodically read the value of
    Bc from the datapool, and apply it to the actual hardware. It can do so
    in manual mode, where it applies the value every time Bc is changed, or it
    can do it in play mode, where it plays the pre-defined schedule stored in
    datapool.schedule.

    The basic idea is this:
    -1. Run until datapool.kill_apply_Bc is set to True, then finish up
    0. Determine if in "play mode" or not ("manual mode" -> default)
    If in "play mode":
        1. Compare current time to the time of next point in schedule
        2. If time of next point is reached, move forward, write Bc value to
            DACs, and calculate next time to move


    If in "manual mode":
        1. Thread-safely read datapool.Bc
        2. Compare value to previously stored value
        3. If no change was made, sleep for 'period' and start again
        4. If a change was detected, apply this change by instructing the DACs
        5. Also store a copy to datapool.Bc_applied


    The thread running this function will be in charge of controlling hardware.
    It is important for this hardware that in the event of a software
    exception, the hardware is reset to zero before the code is fully
    terminated. Otherwise, the power supplies will hang at a non-zero value
    and remain uncontrollable until the server is restarted.

    In order to ensure that this is done properly, the thread should not be
    run as a daemon, and when calling .join() on it, the parent thread should
    give this thread a timeout that is larger than the period.

    So, in order to gracefully kill the thread you do the following:
    1. Set datapool.kill_apply_Bc to True
    2. Join thread with nonzero timeout; e.g. Thread.join(timeout=1.0)
    This will end the thread on its next cycle, and should ensure that the
    code is never terminated with a non-zero value on the power supplies.

    TODO: Currently, this thread cannot be stopped, restarted, or its period
    adjusted. This would however be desirable. To fix this, the way this
    thread is initiated in the server thread should be changed.
    """

    print(f"Started apply_Bc thread with period {datapool.apply_Bc_period}")
    datapool.kill_apply_Bc = False

    Bc_prev = [0., 0., 0.]
    while not datapool.kill_apply_Bc:        # Kill loop when set to True

        # ==== PLAY MODE ====
        if datapool.play_mode:
            # Do only if play_status = "play"
            if datapool.play_status == "play":
                # Measure current time since start of play
                datapool.t_current = time()-datapool.t_play

                # If it is time, move to the next step, unless end of schedule is reached
                if datapool.t_current >= datapool.t_next:
                    if datapool.step_current == datapool.steps - 2:
                        datapool.step_current += 1
                        instruct_DACs(datapool.schedule[datapool.step_current][3])
                        print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")
                        print(f"[DEBUG] Reached end of schedule -> STOPPING")
                        confirm = datapool.play_stop()
                    else:
                        datapool.step_current += 1
                        instruct_DACs(datapool.schedule[datapool.step_current][3])
                        datapool.t_next = datapool.schedule[datapool.step_current+1][2]
                        print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")

                else:
                    sleep(datapool.apply_Bc_period)

            else:
                sleep(datapool.apply_Bc_period)



        # ==== MANUAL MODE ====
        else:
            if not datapool.pause_apply_Bc:  # Pause loop when set to True
                t0 = time()
                Bc_read = datapool.read_Bc()
                if Bc_read == Bc_prev:
                    sleep(max(0., datapool.apply_Bc_period - (time() - t0)))
                else:
                    control_vals = instruct_DACs(Bc_read)
                    datapool.write_control_vals(control_vals)
                    Bc_prev = Bc_read
            else:
                sleep(datapool.apply_Bc_period)

    # When loop is broken, set power supply values to zero.
    instruct_DACs([0., 0., 0.])
    print(f"Closing apply_Bc thread")


# DataPool object
class DataPool:
    def __init__(self):
        # Thread controls
        self._lock_Bm = Lock()
        self._lock_Bc = Lock()
        self._lock_control_vals = Lock()
        self._lock_schedule = Lock()

        self.pause_write_Bm = False     # Implemented non-thread-safe
        self.pause_apply_Bc = False     # Implemented non-thread-safe

        self.kill_write_Bm = False      # Implemented non-thread-safe
        self.kill_apply_Bc = False      # Implemented non-thread-safe

        self.apply_Bc_period = 0.1      # Implemented non-thread-safe
        self.write_Bm_period = 0.1      # Implemented non-thread-safe

        # Data values
        self.Bm = [0., 0., 0., 0.]
        self.Bc = [0., 0., 0.]          # Control vector Bc to be applied [nT]
        self.control_vals = [           # Control values actually applied to the power supplies
            [0., 0., 0.],               # Bc_applied [nT]
            [0., 0., 0.],               # Ic_applied [A]
            [0., 0., 0.]]               # Vc_applied [V]

        # Play controls
        self.play_mode = False          # If False, manual control is enabled, if True,
        self.play_status = "stop"       # Valid: "play", "stop"
        self.t_play = 0.0               # UNIX time at which "play" began
        self.steps = 1
        self.step_current = 0          # What step the schedule play is on
        self.t_current = 0.0
        self.t_next = 0.0

        # Initialize schedule
        self.initialize_schedule()

    def activate_play_mode(self):
        print("[DEBUG] activate_play_mode()")
        self.play_mode = True
        instruct_DACs([0., 0., 0.])
        self.steps = len(self.schedule)
        self.play_status = "stop"
        self.t_play = 0.0

        self.t_current = 0.0
        self.step_current = -1
        self.t_next = self.schedule[self.step_current+1][2]

        return 1


    def deactivate_play_mode(self):
        print("[DEBUG] deactivate_play_mode()")
        instruct_DACs([0., 0., 0.])
        self.play_mode = False
        self.play_status = "stop"
        # self.tstart_play = 0.0
        # self.step_current = -1
        return 1


    def play_start(self):
        print("[DEBUG] play_start()")
        self.t_play = time()
        self.play_status = "play"
        return 1


    def play_stop(self):
        print("[DEBUG] play_stop()")
        self.play_status = "stop"
        instruct_DACs([0., 0., 0.])  # This essentially causes the last schedule point to be ignored
        self.t_current = 0.0
        self.step_current = -1
        self.t_next = self.schedule[self.step_current+1][2]
        return 1


    def get_current_step_time(self):
        return self.step_current, self.steps, self.t_current

    def get_apply_Bc_period(self):
        return datapool.apply_Bc_period  # Implemented non-thread-safe

    def get_write_Bm_period(self):
        return datapool.write_Bm_period  # Implemented non-thread-safe

    def set_apply_Bc_period(self, period):
        datapool.apply_Bc_period = period  # Implemented non-thread-safe
        return 1

    def set_write_Bm_period(self, period):
        datapool.write_Bm_period = period  # Implemented non-thread-safe
        return 1


    def set_schedule_segment(self, segment: list):
        print("set_schedule_segment()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule[segment[0]] = segment

        self._lock_schedule.release()

    def initialize_schedule(self):
        print("initialize_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule = [[0, 0, 0., [0., 0., 0.]], ]
        self.schedule_name = "init"
        self.schedule_duration = 0.0

        self._lock_schedule.release()
        return 1

    def allocate_schedule(self, name: str, n_seg: int, duration: float):
        print("allocate_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule_name = name
        self.schedule_duration = duration
        self.schedule = [[0, 0, 0., [0., 0., 0.]], ]*n_seg

        self._lock_schedule.release()
        return 1

    def print_schedule_info(self):
        self._lock_schedule.acquire(timeout=0.001)

        print(" ==== SCHEDULE INFO ==== ")
        print("Name:    ", self.schedule_name)
        print("n_seg:   ", len(self.schedule))
        print("Duration:", self.schedule_duration)
        print(" [Preview]")
        if len(self.schedule) == 1:
            print(self.schedule[0])
        else:
            print(self.schedule[0])
            print("...         ...")
            print(self.schedule[-1])

        self._lock_schedule.release()
        return 1

    def print_schedule(self, max_entries):
        self._lock_schedule.acquire(timeout=0.001)

        if len(self.schedule) == 1:
            print(self.schedule[0])

        else:
            n_prints = min(len(self.schedule), max_entries)

            for i_seg in range(0, int(n_prints/2)):
                print(self.schedule[i_seg])
            if len(self.schedule) > max_entries:
                print("...         ...")
            for i_seg in range(-int(n_prints/2), 0):
                print(self.schedule[i_seg])

        self._lock_schedule.release()
        return 1


    def write_Bm(self, Bm):
        """Thread-safely write Bm to the datapool

        The lock prevents other threads from accessing self.Bm whilst it is
        being updated. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_Bm.acquire(timeout=0.001)
        try:
            self.Bm = Bm
        except:  # noqa
            print("[WARNING] DataPool.write_Bm(): Unable to write to self.Bm!")
        self._lock_Bm.release()


    def read_Bm(self):
        """Thread-safely reads the current Bm field from the datapool

        The lock prevents other threads from updating self.Bm whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_Bm.acquire(timeout=0.001)
        try:
            Bm = self.Bm
        except:  # noqa
            print("[WARNING] DataPool.read_Bm(): Unable to read self.Bm!")
        self._lock_Bm.release()
        return Bm


    def write_Bc(self, Bc):  # TODO: DUMMY - Implement actual functionality
        """Thread-safely write Bc to the datapool

        The lock prevents other threads from accessing self.Bc whilst it is
        being updated. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_Bc.acquire(timeout=0.001)
        try:
            self.Bc = Bc
        except:  # noqa
            print("[WARNING] DataPool.write_Bc(): Unable to write to self.Bc!")
        self._lock_Bc.release()


    def read_Bc(self):
        """Thread-safely reads the current Bc field from the datapool.

        The lock prevents other threads from updating self.Bc whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_Bc.acquire(timeout=0.001)
        try:
            Bc = self.Bc
        except:  # noqa
            print("[WARNING] DataPool.read_Bc(): Unable to read self.Bc!")
        self._lock_Bc.release()
        return Bc


    def write_control_vals(self, control_vals):
        """Thread-safely write the control_vals to the datapool
        """
        self._lock_control_vals.acquire(timeout=0.001)
        try:
            self.control_vals = control_vals
        except:  # noqa
            print("[WARNING] DataPool.write_control_vals(): Unable to write to self.control_vals!")
        self._lock_control_vals.release()


    def read_control_vals(self):
        """Thread-safely reads the applied control_vals from the datapool.
        """
        self._lock_control_vals.acquire(timeout=0.001)
        try:
            control_vals = self.control_vals
        except:  # noqa
            print("[WARNING] DataPool.read_control_vals(): Unable to read self.control_vals!")
        self._lock_control_vals.release()
        return control_vals

# Server object
class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    """ This is a subclassed TCP Server class with threading enabled.

    Its constructor has been overloaded to ensure that the datapool object
    can be passed to it, and so that extra functionality can be added.
    """
    def __init__(self, host, handler, datapool):

        self.datapool = datapool
        self.server_tstart = time()

        super().__init__(host, handler)

    def uptime(self):
        """Returns the uptime of the ThreadedTCPServer instance in [s]"""
        return time() - self.server_tstart


# Thread handler object
class ThreadedTCPRequestHandler(BaseRequestHandler):
    """ This is a subclassed RequestHandler class with threading enabled.

    A unique instance of this class is created every time a client connects
    to the ThreadedTCPServer, and is destroyed when this connection is
    terminated. This server setup supports multiple clients, which all
    interface to the server through their own assigned instance of
    ThreadedTCPRequestHandler.

    Because the DataPool object implements its own thread locks, it should
    also be possible for the clients to safely interact with the datapool, so
    long as the thread-safe read and write functions are used.
    """

    def setup(self):
        """Overloaded from base class. Runs once before handle() loops."""
        self.socket_tstart = time()
        print(f"Client {self.client_address[0]}:{self.client_address[1]} connected.")

    def handle(self):
        while True:
            packet_out = None
            packet_in = self.request.recv(256)
            if packet_in == b"":
                break
            type_id = scc.packet_type(packet_in)

            # print("[DEBUG] packet_in:", packet_in)

            if type_id == "m":
                # print("[DEBUG] Detected m-package")
                msg = scc.decode_mpacket(packet_in)
                print(f"[{self.client_address[0]}:{self.client_address[1]}]", msg)

            elif type_id == "e":
                # print("[DEBUG] Detected e-package")
                packet_out = scc.encode_epacket(scc.decode_epacket(packet_in))

            elif type_id == "b":
                # print("[DEBUG] Detected b-package")
                packet_out = scc.encode_bpacket(self.server.datapool.read_Bm())
                # print(packet_out)

            elif type_id == "c":
                # print("[DEBUG] Detected c-package")
                Bc = scc.decode_cpacket(packet_in)
                try:
                    self.server.datapool.write_Bc(Bc)
                    # print("[DEBUG] Bc written to datapool:", Bc, type(Bc))
                    packet_out = scc.encode_mpacket("1")
                except:  # noqa
                    packet_out = scc.encode_mpacket("-1")

            elif type_id == "s":
                # print("[DEBUG] Detected b-package")

                segment = scc.decode_spacket_tovals(packet_in)
                self.server.datapool.set_schedule_segment(segment)
                # Send segment number back as a verification
                packet_out = scc.encode_mpacket(str(segment[0]))

            elif type_id == "x":
                # print("[DEBUG] Detected x-package")
                fname, args = scc.decode_xpacket(packet_in)
                # print(f"[DEBUG] {fname}({args})")
                packet_out = self.command_handle(fname, args)

            else:
                raise ValueError(f"Encountered uninterpretable type_id '{type_id}' in received packet.")

            # print("[DEBUG] packet_out:", packet_out)

            # If a response was warranted, send it:
            if packet_out is not None:
                self.request.sendall(packet_out)


    def command_handle(self, fname, args):
        packet_out = None

        # Requests the server uptime:
        if fname == "server_uptime":
            packet_out = scc.encode_mpacket(str(self.server.uptime()))

        # Requests the uptime of the communication socket, from the perspective
        # of the server
        elif fname == "socket_uptime":
            packet_out = scc.encode_mpacket(str(time()-self.socket_tstart))

        # Alternative echo, mainly for testing purposes. Echoes the first
        # argument given to it, or an empty string if no arguments were given.
        elif fname == "echo":
            if len(args) == 0:
                packet_out = scc.encode_epacket("")
            else:
                packet_out = scc.encode_epacket(str(args[0]))

        # Requests the value of datapool.control_vals and sends them as a
        # csv string
        elif fname == "get_control_vals":
            control_vals = self.server.datapool.read_control_vals()
            msg = ",".join([str(item) for row in control_vals for item in row])
            packet_out = scc.encode_mpacket(msg)

        # Prints info about the schedule into the terminal
        elif fname == "print_schedule_info":
            confirm = self.server.datapool.print_schedule_info()
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "print_schedule":
            confirm = self.server.datapool.print_schedule(max_entries=args[0])
            packet_out = scc.encode_mpacket(str(confirm))

        # Initialize the schedule (reset)
        elif fname == "initialize_schedule":
            confirm = self.server.datapool.initialize_schedule()
            packet_out = scc.encode_mpacket(str(confirm))

        # Allocate an empty schedule (args: name: str, n_seg: int, duration: float)
        elif fname == "allocate_schedule":
            confirm = self.server.datapool.allocate_schedule(args[0], args[1], args[2])
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "activate_play_mode":
            confirm = self.server.datapool.activate_play_mode()
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "deactivate_play_mode":
            confirm = self.server.datapool.deactivate_play_mode()
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "play_start":
            confirm = self.server.datapool.play_start()
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "play_stop":
            confirm = self.server.datapool.play_stop()
            packet_out = scc.encode_mpacket(str(confirm))


        elif fname == "get_current_step_time":
            # Returns current value of schedule step and time as csv string
            step, steps, time = self.server.datapool.get_current_step_time()
            packet_out = scc.encode_mpacket(f"{step},{steps},{time}")

        elif fname == "get_apply_Bc_period":
            period = self.server.datapool.get_apply_Bc_period()
            packet_out = scc.encode_mpacket(str(period))

        elif fname == "get_write_Bm_period":
            period = self.server.datapool.get_write_Bm_period()
            packet_out = scc.encode_mpacket(str(period))

        elif fname == "set_apply_Bc_period":
            confirm = self.server.datapool.set_apply_Bc_period(args[0])
            packet_out = scc.encode_mpacket(str(confirm))

        elif fname == "set_write_Bm_period":
            confirm = self.server.datapool.set_write_Bm_period(args[0])
            packet_out = scc.encode_mpacket(str(confirm))


        else:
            raise ValueError(f"Function name '{fname}' not recognised!")
        return packet_out


    def finish(self):
        """Overloaded from base class. Runs once after handle() loop ends."""
        print(f"Client {self.client_address[0]}:{self.client_address[1]} disconnected.")


if __name__ == "__main__":
    t0 = time()

    # Initialize common DataPool object
    datapool = DataPool()

    # Server object
    HOST = ("127.0.0.1", 7777)  # TODO replace with config

    server = ThreadedTCPServer(HOST, ThreadedTCPRequestHandler, datapool)

    # When set to True, this makes all child threads of the server thread
    # daemonic, forcing them to terminate when main thread terminates.
    # It is recommended to keep this on False, because operation of the
    # apply_Bc_thread will be safer if it is non-daemonic.
    server.daemon_threads = False

    # Place server in own thread
    server_thread = Thread(target=server.serve_forever)

    # Make server thread daemonic, so it too will terminate upon main thread
    # termination
    server_thread.daemon = True

    # Start server thread
    server_thread.start()

    # Set up thread for continuously polling magnetic field data from ADC, and
    # writing it to datapool.Bm
    datapool.write_Bm_period = 0.1
    thread_write_Bm = Thread(
        name="Measure Bm Thread",
        target=threaded_write_Bm,
        args=(datapool,),
        daemon=True)
    thread_write_Bm.start()

    # Set up thread that finds when a change in datapool.Bc occurs, and when
    # it occurs, that it gets applied to the power supplies.
    datapool.apply_Bc_period = 0.1
    thread_apply_Bc = Thread(
        name="Apply Bc Thread",
        target=threaded_apply_Bc,
        args=(datapool,),
        daemon=False)  # Not set as daemon to ensure that it finishes properly
    thread_apply_Bc.start()

    print(f"Server is up. Time elapsed: {round((time()-t0)*1E3, 3)} ms. Active threads: {active_count()}")


    # ==== Main loop of server ===============================================
    while True:
        try:
            # Do something useful
            sleep(0.1)
            pass

        except:  # noqa
            break


    # ==== Server shutdown ===================================================

    # Gracefully terminate control threads
    print("Shutting down - finishing threads.")
    datapool.kill_apply_Bc = True
    datapool.kill_write_Bm = True

    ttest = time()
    thread_write_Bm.join(timeout=1.0)
    print(f"Shut down measure_Bm_thread in {round((time()-ttest)*1E3, 3)} ms")

    ttest = time()
    thread_apply_Bc.join(timeout=1.0)
    print(f"Shut down apply_Bc_thread in {round((time()-ttest)*1E3, 3)} ms")

    # For safety: set power supplies to zero, separately from apply_Bc_thread
    print(f"Resetting Bc just in case")
    instruct_DACs([0., 0., 0.])

    # Server termination
    total_uptime = server.uptime()
    server.shutdown()
    server.server_close()
    print(f"Server is closed. Total uptime: {round(total_uptime, 3)} s")


