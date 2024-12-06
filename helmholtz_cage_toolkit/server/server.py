from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from threading import Thread, Lock, main_thread, active_count

from numpy import array
from numpy.random import random
from time import time, sleep

import helmholtz_cage_toolkit.scc.scc4 as codec
import helmholtz_cage_toolkit.server.server_config as sconfig



def threaded_write_DAC(datapool):
    """The thread running this function will periodically read the value of
    DAC inputs from the datapool, and apply it to the DAC hardware. It can do
    so in manual mode, where it applies the value every time a DAC input is
    changed, or it can do it in play mode, where it plays the pre-defined
    schedule stored in datapool.schedule.

    The basic idea is this:
    -1. Run until datapool.kill_threaded_write_DAC is set to True, then finish
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
    1. Set datapool.kill_threaded_write_DAC to True
    2. This will break the loop, and run a hardware shutdown routine.
    3. Join thread with nonzero timeout; e.g. Thread.join(timeout=1.0)
    This will end the thread on its next cycle, and should ensure that the
    code is never terminated with a non-zero value on the power supplies.

    TODO: Currently, this thread cannot be stopped, restarted, or its period
    adjusted. This would however be desirable. To fix this, the way this
    thread is initiated in the server thread should be changed.
    """

    print(f"Started 'write DAC' thread with period {datapool.threaded_write_DAC_period}")
    datapool.kill_threaded_write_DAC = False

    Bc_prev = [0., 0., 0.]

    while not datapool.kill_threaded_write_DAC:  # Kills loop when set to True

        # # ==== PLAY MODE ====
        # if datapool.play_mode:
        #     # Do only if play_status = "play"
        #     if datapool.play_status == "play":
        #         # Measure current time since start of play
        #         datapool.t_current = time()-datapool.t_play
        #
        #         # If it is time, move to the next step, unless end of schedule is reached
        #         if datapool.t_current >= datapool.t_next:
        #             if datapool.step_current == datapool.steps - 2:
        #                 datapool.step_current += 1
        #                 instruct_DACs(datapool, datapool.schedule[datapool.step_current][3:6])
        #                 print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")
        #                 print(f"[DEBUG] Reached end of schedule -> STOPPING")
        #                 confirm = datapool.play_stop()
        #             else:
        #                 datapool.step_current += 1
        #                 instruct_DACs(datapool, datapool.schedule[datapool.step_current][3:6])
        #                 datapool.t_next = datapool.schedule[datapool.step_current+1][2]
        #                 print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")
        #
        #         else:
        #             sleep(datapool.apply_Bc_period)
        #
        #     else:
        #         sleep(datapool.apply_Bc_period)


        # # ==== MANUAL MODE ====
        # else:
        #     if not datapool.pause_threaded_write_DAC:  # Pause loop when set to True
        #         t0 = time()
        #         Bc_read = datapool.read_Bc()
        #         if Bc_read == Bc_prev:
        #             sleep(max(0., datapool.apply_Bc_period - (time() - t0)))
        #         else:
        #             # control_vals = instruct_DACs(datapool, Bc_read)
        #             Bc, Ic, Vc = instruct_DACs(datapool, Bc_read)
        #             # datapool.write_control_vals(control_vals)
        #             datapool.write_control_vals(Bc, Ic, Vc)
        #             Bc_prev = Bc_read
        #     else:
        #         sleep(datapool.threaded_write_DAC_period)

        # ==== MANUAL MODE ====
        if not datapool.pause_threaded_write_DAC:  # Pause loop when set to True
            t0 = time()
            Bc_read = datapool.read_Bc()
            if Bc_read == Bc_prev:
                sleep(max(0., datapool.apply_Bc_period - (time() - t0)))
            else:
                # control_vals = instruct_DACs(datapool, Bc_read)
                Bc, Ic, Vc = instruct_DACs(datapool, Bc_read)
                # datapool.write_control_vals(control_vals)
                datapool.write_control_vals(Bc, Ic, Vc)
                Bc_prev = Bc_read
        else:
            sleep(datapool.threaded_write_DAC_period)

    # When loop is broken, set power supply values to zero.
    # TODO implement safe shutdown
    instruct_DACs(datapool, [0., 0., 0.])
    print(f"Closing apply_Bc thread")

def threaded_read_ADC(datapool):
    """The thread running this function will periodically read the value of
    ADC inputs from the hardware, and write them to the datapool.

    The basic idea is this:
    -1. Run until datapool.kill_threaded_read_ADC is set to True, then finish


    So, in order to gracefully kill the thread you do the following:
    1. Set datapool.kill_threaded_read_ADC to True
    2. Join thread with nonzero timeout; e.g. Thread.join(timeout=1.0)
    This will end the thread on its next cycle, and should ensure that the
    code is never terminated with a non-zero value on the power supplies.

    """

    print(f"Started 'read ADC' thread with rate {1/datapool.threaded_read_ADC_period}")
    datapool.kill_threaded_read_ADC = False

    Bc_prev = [0., 0., 0.]

    while not datapool.kill_threaded_read_ADC:  # Kills loop when set to True

        # # ==== PLAY MODE ====
        # if datapool.play_mode:
        #     # Do only if play_status = "play"
        #     if datapool.play_status == "play":
        #         # Measure current time since start of play
        #         datapool.t_current = time()-datapool.t_play
        #
        #         # If it is time, move to the next step, unless end of schedule is reached
        #         if datapool.t_current >= datapool.t_next:
        #             if datapool.step_current == datapool.steps - 2:
        #                 datapool.step_current += 1
        #                 instruct_DACs(datapool, datapool.schedule[datapool.step_current][3:6])
        #                 print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")
        #                 print(f"[DEBUG] Reached end of schedule -> STOPPING")
        #                 confirm = datapool.play_stop()
        #             else:
        #                 datapool.step_current += 1
        #                 instruct_DACs(datapool, datapool.schedule[datapool.step_current][3:6])
        #                 datapool.t_next = datapool.schedule[datapool.step_current+1][2]
        #                 print(f"[DEBUG] Current step: {datapool.step_current}/{datapool.steps} (+{round(datapool.t_current, 3)} s)")
        #
        #         else:
        #             sleep(datapool.apply_Bc_period)
        #
        #     else:
        #         sleep(datapool.apply_Bc_period)


        # # ==== MANUAL MODE ====
        # else:
        #     if not datapool.pause_threaded_write_DAC:  # Pause loop when set to True
        #         t0 = time()
        #         Bc_read = datapool.read_Bc()
        #         if Bc_read == Bc_prev:
        #             sleep(max(0., datapool.apply_Bc_period - (time() - t0)))
        #         else:
        #             # control_vals = instruct_DACs(datapool, Bc_read)
        #             Bc, Ic, Vc = instruct_DACs(datapool, Bc_read)
        #             # datapool.write_control_vals(control_vals)
        #             datapool.write_control_vals(Bc, Ic, Vc)
        #             Bc_prev = Bc_read
        #     else:
        #         sleep(datapool.threaded_write_DAC_period)

        # ==== MANUAL MODE ====
        if not datapool.pause_threaded_read_ADC:  # Pause loop when set to True
            t0 = time()
            # DO READING STUFF
        else:
            sleep(datapool.threaded_read_ADC_period)

    # When loop is broken, set power supply values to zero.
    # TODO implement safe shutdown
    instruct_DACs(datapool, [0., 0., 0.])
    print(f"Closing apply_Bc thread")


# DataPool object
class DataPool:
    def __init__(self):
        # Thread controls
        self._lock_ADC = Lock()
        self._lock_DAC = Lock()
        self._lock_schedule = Lock()

        self.pause_threaded_read_ADC = False    # Not thread-safe
        self.pause_threaded_write_DAC = False   # Not thread-safe

        self.kill_threaded_read_ADC = False     # Not thread-safe
        self.kill_threaded_write_DAC = False    # Not thread-safe

        self.threaded_read_ADC_period = 1/config["threaded_read_ADC_rate"]  # Not thread-safe
        self.threaded_write_DAC_period = 1/config["threaded_write_DAC_rate"]  # Not thread-safe


        # Data values
        self.tm = 0.                    # Time at which Bm, Im were taken
        self.Im = [0., 0., 0.]          # Measured current Im in [A]
        self.Bm = [0., 0., 0.]          # Measured field Bm in [nT]
        self.Bc = [0., 0., 0.]          # Control vector Bc to be applied [nT]

        self.output_enable = False



        self.i_step = 0
        self.Br = [0., 0., 0.]

        self.Vvc = [0., 0., 0.]
        self.Vcc = [0., 0., 0.]


        # # Play controls
        # self.play_mode = False          # If False, manual control is enabled, if True,
        # self.play_status = "stop"       # Valid: "play", "stop"
        # self.t_play = 0.0               # UNIX time at which "play" began
        # self.steps = 1
        # self.step_current = 0          # What step the schedule play is on
        # self.t_current = 0.0
        # self.t_next = 0.0

        # Initialize schedule
        self.initialize_schedule()

    # def activate_play_mode(self):
    #     print("[DEBUG] activate_play_mode()")
    #     self.play_mode = True
    #     instruct_DACs(datapool, [0., 0., 0.])
    #     self.steps = len(self.schedule)
    #     self.play_status = "stop"
    #     self.t_play = 0.0
    #
    #     self.t_current = 0.0
    #     self.step_current = -1
    #     self.t_next = self.schedule[self.step_current+1][2]
    #
    #     return 1
    #
    #
    # def deactivate_play_mode(self):
    #     print("[DEBUG] deactivate_play_mode()")
    #     instruct_DACs(datapool, [0., 0., 0.])
    #     self.play_mode = False
    #     self.play_status = "stop"
    #     # self.tstart_play = 0.0
    #     # self.step_current = -1
    #     return 1
    #
    #
    # def play_start(self):
    #     print("[DEBUG] play_start()")
    #     self.t_play = time()
    #     self.play_status = "play"
    #     return 1
    #
    #
    # def play_stop(self):
    #     print("[DEBUG] play_stop()")
    #     self.play_status = "stop"
    #     instruct_DACs(datapool, [0., 0., 0.])  # This essentially causes the last schedule point to be ignored
    #     self.t_current = 0.0
    #     self.step_current = -1
    #     self.t_next = self.schedule[self.step_current+1][2]
    #     return 1
    #
    #
    # def get_current_time_step(self):
    #     return self.step_current, self.steps, self.t_current


    # def get_play_mode(self):
    #     # print("[DEBUG] get_play_mode()")
    #     return self.play_mode  # Implemented non-thread-safe
    #
    # def get_play_status(self):
    #     # print("[DEBUG] get_play_status()")
    #     return self.play_status  # Implemented non-thread-safe

    # def set_schedule_segment(self, segment: list):
    #     # print("set_schedule_segment()")
    #
    #     self._lock_schedule.acquire(timeout=0.001)
    #
    #     self.schedule[segment[0]] = segment
    #
    #     self._lock_schedule.release()

    def initialize_schedule(self):
        print("initialize_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule = [[0, 0, 0., 0., 0., 0.], ]
        self.schedule_name = "init"
        self.schedule_duration = 0.0

        self._lock_schedule.release()
        return 1

    def allocate_schedule(self, name: str, n_seg: int, duration: float):
        print("[DEBUG] allocate_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule_name = name
        self.schedule_duration = duration
        self.schedule = [[0, 0, 0., 0., 0., 0.], ]*n_seg

        self._lock_schedule.release()
        return 1

    def get_schedule(self):
        # print("[DEBUG] get_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        schedule = self.schedule

        self._lock_schedule.release()
        return schedule

    def get_schedule_info(self):
        # print("[DEBUG] get_schedule_info()")

        self._lock_schedule.acquire(timeout=0.001)

        name = self.schedule_name
        length = len(self.schedule)
        duration = self.schedule_duration

        self._lock_schedule.release()
        return name, length, duration

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


        # print(str(self.get_schedule()))
        # print(hash(str(self.get_schedule())))
        return 1


    # def write_DAC(self, Bm):  # TODO STALE
    #     """Thread-safely write Bm to the datapool
    #
    #     The lock prevents other threads from accessing self.Bm whilst it is
    #     being updated. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_Bm.acquire(timeout=0.001)
    #     try:
    #         self.Bm = Bm
    #     except:  # noqa
    #         print("[WARNING] DataPool.write_Bm(): Unable to write to self.Bm!")
    #     self._lock_Bm.release()
    #
    # def write_Bm(self, Bm):  # TODO STALE
    #     """Thread-safely write Bm to the datapool
    #
    #     The lock prevents other threads from accessing self.Bm whilst it is
    #     being updated. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_Bm.acquire(timeout=0.001)
    #     try:
    #         self.Bm = Bm
    #     except:  # noqa
    #         print("[WARNING] DataPool.write_Bm(): Unable to write to self.Bm!")
    #     self._lock_Bm.release()
    #
    #
    # def write_tmBmIm(self, tm, Bm, Im):
    #     """Thread-safely write tm, Bm, and Im to the datapool.
    #
    #     The lock prevents other threads from accessing self.Bm and self.Im
    #     whilst they is being updated. Useful to prevent hard-to-debug race
    #     condition bugs.
    #     """
    #     self._lock_tmBmIm.acquire(timeout=0.001)
    #     try:
    #         self.tm = tm
    #         self.Bm = Bm
    #         self.Im = Im
    #     except:  # noqa
    #         print("[WARNING] DataPool.write_tmBmIm(): Unable to write correctly!")
    #     self._lock_tmBmIm.release()
    #
    # def read_telemetry(self):
    #     """Thread-safely reads the current Bm field from the datapool
    #
    #     The lock prevents other threads from updating self.Bm whilst it is
    #     being read. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_tmBmIm.acquire(timeout=0.001)
    #     try:
    #         tm = self.tm
    #         Bm = self.Bm
    #         Im = self.Im
    #         Ic = self.Ic
    #         Vc = self.Vc
    #         Vvc = self.Vvc
    #         Vcc = self.Vcc
    #     except:  # noqa
    #         print("[WARNING] DataPool.read_telemetry(): Unable to read correctly!")
    #     self._lock_tmBmIm.release()
    #     return tm, Bm, Im, Ic, Vc, Vvc, Vcc
    #
    # def read_Bm(self):
    #     """Thread-safely reads the current Bm field from the datapool
    #
    #     The lock prevents other threads from updating self.Bm whilst it is
    #     being read. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_Bm.acquire(timeout=0.001)
    #     try:
    #         tm = self.tm
    #         Bm = self.Bm
    #     except:  # noqa
    #         print("[WARNING] DataPool.read_Bm(): Unable to read self.Bm!")
    #     self._lock_Bm.release()
    #     return tm, Bm
    #
    #
    # def write_Bc(self, Bc):  # TODO: DUMMY - Implement actual functionality
    #     """Thread-safely write Bc to the datapool
    #
    #     The lock prevents other threads from accessing self.Bc whilst it is
    #     being updated. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_Bc.acquire(timeout=0.001)
    #     try:
    #         self.Bc = Bc
    #     except:  # noqa
    #         print("[WARNING] DataPool.write_Bc(): Unable to write to self.Bc!")
    #     self._lock_Bc.release()
    #
    #
    # def read_Bc(self):
    #     """Thread-safely reads the current Bc field from the datapool.
    #
    #     The lock prevents other threads from updating self.Bc whilst it is
    #     being read. Useful to prevent hard-to-debug race condition bugs.
    #     """
    #     self._lock_Bc.acquire(timeout=0.001)
    #     try:
    #         Bc = self.Bc
    #     except:  # noqa
    #         print("[WARNING] DataPool.read_Bc(): Unable to read self.Bc!")
    #     self._lock_Bc.release()
    #     return Bc
    #
    #
    # def write_control_vals(self, Bc, Ic, Vc):  # TODO STALE
    #     """Thread-safely write the control_vals to the datapool
    #     """
    #     print(f"[DEBUG] write_control_vals({Bc}, {Ic}, {Vc})")
    #     self._lock_control_vals.acquire(timeout=0.001)
    #     try:
    #         # self.Bc = Bc
    #         self.Ic = Ic
    #         self.Vc = Vc
    #         # self.control_vals = control_vals
    #     except:  # noqa
    #         print("[WARNING] DataPool.write_control_vals(): Unable to write to self.control_vals!")
    #     self._lock_control_vals.release()
    #
    #
    # def read_control_vals(self):  # TODO STALE
    #     """Thread-safely reads the applied control_vals from the datapool.
    #     """
    #     print("[DEBUG] STALE FUNCTION USED: read_control_vals()")
    #     self._lock_control_vals.acquire(timeout=0.001)
    #     try:
    #         control_vals = self.control_vals
    #     except:  # noqa
    #         print("[WARNING] DataPool.read_control_vals(): Unable to read self.control_vals!")
    #     self._lock_control_vals.release()
    #     return control_vals

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
            # t0 = time()  # [TIMING]
            if packet_in == b"":
                break
            type_id = codec.packet_type(packet_in)
            # t1 = time()  # [TIMING]

            # print("[DEBUG] packet_in:", packet_in)

            if type_id == "m":
                # print("[DEBUG] Detected m-package")
                msg = codec.decode_mpacket(packet_in)
                print(f"[{self.client_address[0]}:{self.client_address[1]}] {msg}")
                packet_out = codec.encode_mpacket("1")  # Send 1 as confirmation

            elif type_id == "e":
                # print("[DEBUG] Detected e-package")
                packet_out = codec.encode_epacket(codec.decode_epacket(packet_in))

            elif type_id == "b":
                # print("[DEBUG] Detected b-package")
                packet_out = codec.encode_bpacket(*self.server.datapool.read_Bm())
                # print(packet_out)

            elif type_id == "t":
                # print("[DEBUG] Detected t-package")
                packet_out = codec.encode_tpacket(
                    *self.server.datapool.read_telemetry()
                )
                # print(packet_out)

            elif type_id == "c":
                # print("[DEBUG] Detected c-package")
                Bc = codec.decode_cpacket(packet_in)
                try:
                    self.server.datapool.write_Bc(Bc)
                    print("[DEBUG] Bc written to datapool:", Bc, type(Bc))
                    print("[DEBUG] CHECK datapool.Bc:", self.server.datapool.Bc)
                    packet_out = codec.encode_mpacket("1")
                except:  # noqa
                    packet_out = codec.encode_mpacket("-1")

            elif type_id == "s":
                # print("[DEBUG] Detected b-package")

                segment = codec.decode_spacket(packet_in)
                self.server.datapool.set_schedule_segment(segment)
                # Send segment number back as a verification
                packet_out = codec.encode_mpacket(str(segment[0]))

            elif type_id == "x":
                # print("[DEBUG] Detected x-package")
                fname, args = codec.decode_xpacket(packet_in)
                # print(f"[DEBUG] {fname}({args})")
                packet_out = self.command_handle(fname, args)

            else:
                raise ValueError(f"Encountered uninterpretable type_id '{type_id}' in received packet.")

            # print("[DEBUG] packet_out:", packet_out)

            # t2 = time()  # [TIMING]

            # If a response was warranted, send it:
            if packet_out is not None:
                self.request.sendall(packet_out)
            # t3 = time()  # [TIMING]
            # print(f"Sent {codec.packet_type(packet_out)}-packet. Time: {int((t1-t0)*1E6)}, {int((t2-t1)*1E6)}, {int((t3-t2)*1E6)} \u03bcs")  # [TIMING]


    def command_handle(self, fname, args):
        packet_out = None

        # Requests the server uptime:
        if fname == "get_server_uptime":
            packet_out = codec.encode_mpacket(str(self.server.uptime()))

        # Requests the uptime of the communication socket, from the perspective
        # of the server
        elif fname == "get_socket_uptime":
            packet_out = codec.encode_mpacket(str(time()-self.socket_tstart))

        # # Requests the value of play mode (False indicates `manual mode`)
        # elif fname == "get_play_mode":
        #     packet_out = codec.encode_mpacket(str(self.server.datapool.get_play_mode()))
        #
        # # Requests the value of play status (False indicates `manual mode`)
        # elif fname == "get_play_status":
        #     packet_out = codec.encode_mpacket(self.server.datapool.get_play_status())

        # Requests the schedule name, length, and duration as csv string
        elif fname == "get_schedule_info":
            name, length, duration = self.server.datapool.get_schedule_info()
            packet_out = codec.encode_mpacket(f"{name},{length},{duration}")

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
    # HOST = ("127.0.0.1", 7777)  # TODO remove
    HOST = (config["SERVER_ADDRESS"], config["SERVER_PORT"])

    server = ThreadedTCPServer(HOST, ThreadedTCPRequestHandler, datapool)

    # When set to True, this makes all child threads of the server thread
    # daemonic, forcing them to terminate when main thread terminates.
    # It is recommended to keep this on False, because operation of the
    # write_DAC_thread will be safer if it is non-daemonic.
    server.daemon_threads = False

    # Place server in own thread
    server_thread = Thread(target=server.serve_forever)

    # Make server thread daemonic, so it too will terminate upon main thread
    # termination
    server_thread.daemon = True

    # Start server thread
    server_thread.start()

    # Set up thread for continuously polling the ADC, and writing it to the
    # server datapool.
    thread_read_ADC = Thread(
        name="Read ADC Thread",
        target=threaded_read_ADC,
        args=(datapool,),
        daemon=True)
    thread_read_ADC.start()

    # Set up thread that finds when a change in control parameters occurs, and
    # when it occurs, ensures that it is written to the DAC.
    thread_write_DAC = Thread(
        name="Write DAC Thread",
        target=threaded_write_DAC,
        args=(datapool,),
        daemon=False)  # Not set as daemon to ensure that it finishes properly
    thread_write_DAC.start()

    print(f"Server is up. Time elapsed: {round((time()-t0)*1E3, 3)} ms. Active threads: {active_count()}")


    # ==== Main loop of server ===============================================
    while True:
        try:
            # Do something useful
            sleep(0.001)
            pass

        except:  # noqa
            break


    # ==== Server shutdown ===================================================

    # Gracefully terminate control threads
    print("Shutting down - finishing threads.")
    datapool.kill_threaded_read_ADC = True
    # datapool.kill_write_Bm = True  # TODO STALE
    datapool.kill_threaded_write_DAC = True

    ttest = time()
    # thread_write_Bm.join(timeout=1.0)
    thread_write_tmBmIm.join(timeout=1.0)
    print(f"Shut down measure_tmBmIm_thread in {round((time()-ttest)*1E3, 3)} ms")

    ttest = time()
    thread_apply_Bc.join(timeout=1.0)
    print(f"Shut down apply_Bc_thread in {round((time()-ttest)*1E3, 3)} ms")

    # For safety: set power supplies to zero, separately from apply_Bc_thread
    print(f"Resetting Bc just in case")
    instruct_DACs(datapool, [0., 0., 0.])

    # Server termination
    total_uptime = server.uptime()
    server.shutdown()
    server.server_close()
    print(f"Server is closed. Total uptime: {round(total_uptime, 3)} s")

