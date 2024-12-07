"""
This is the main script for the server side of the Helmholtz Cage Toolkit,
intended to be run from the Raspberry Pi controlling all the hardware.
Its design is relatively simple, but since the implementation fully supports
multi-threading, things tend to look a bit more complicated than they ought
to.

This script is intended to be run directly, preferably invoked via the
terminal. The code to set up the server can be found after the line:
    if __name__ == "__main__":

The basic layout of the server setup is as follows:
1. Create Datapool(), a general-purpose data container that the server will use
    as a thread-safe data hub. The definition of the server Datapool is also in
    this file, and is altogether distinct to the Datapool used by the clients.
2. Fetch own address and port information from the server_config, via the
    Datapool.
3. Create a ThreadedTCPServer instance, which is the main and only server
    instance. Its creation also defines a ThreadedTCPRequestHandler. Each
    connected client will interact with their own instance of this handler,
    running in a separate thread to keep things compartmentalized.
4. The server object is placed in its own thread, which is then started.
5. Two separate threads are created and started:
    - A thread running the function threaded_write_DAC(), used for DAC hardware
    interactions.
    - A thread running the function threaded_read_ADC(), used for ADC hardware
    interactions.

After this, the server will be fully operational and run in perpetuity unless
terminated or an exception occurs. When this occurs, the threads are one by one
stopped, some work is done to finish gracefully, and finally the server Thread
will be terminated.

The server implementation relies on the server config and the SCC codec.
"""


from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from threading import Thread, Lock, main_thread, active_count

from numpy import array, zeros
from numpy.random import rand
from time import time, sleep

import helmholtz_cage_toolkit.scc.scc4 as codec
from helmholtz_cage_toolkit.server.server_config import server_config as config




def hardware_shutdown(datapool):
    """
    In case of a software error or upon termination of the server, it is of
    critical importance that the hardware is properly terminated. Without this,
    the hardware can still output power without user control, store energy,
    cause voltage surges, etc.

    This routine should be called in such cases, and will properly terminate
    the hardware to a safe idling state. Given that the Helmholtz Cage Toolkit
    is in many places relatively hardware agnostic, the proper termination
    procedure is hardware specific nonetheless, depending for example on the
    slewing properties of power supplies. If you are using particular hardware,
    note that you may have to rewrite/overload this function with your own
    implementation.

    The basic overview of the termination procedure is as follows:
    1. Command all power supplies to output zero amp.
    2. Sleep for a specific period to allow the power supplies to slew to zero.
    3. Reset the H-bridges to their default off state.
    4. Inhibit the output of either the PSUs or the H-bridges with the
        dedicated software toggle implementation.
    """
    print("hardware_shutdown() called")



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
            # print("threaded_write_DAC() loop")
            t0 = time()
            Bc_read = [0., 0., 0.]
            if Bc_read == Bc_prev:
                sleep(max(0., datapool.threaded_write_DAC_period - (time() - t0)))
            else:
                pass
        else:
            sleep(datapool.threaded_write_DAC_period)

    # When loop is broken, set power supply values to zero.
    # TODO implement safe shutdown
    print(f"Closing write_DAC thread")
    hardware_shutdown(datapool)

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
            # print("threaded_read_ADC() loop")

            if datapool.serveropt_spoof_Bm:
                Bm_prev = datapool.read_Bm()
                Bm = []
                for i in (0, 1, 2):
                    Bm.append(datapool.mutate(
                        Bm_prev[i],
                        datapool.params_mutate[0][i],
                        datapool.params_mutate[1][i],
                        datapool.params_mutate[2][i]
                    ))
                datapool.write_Bm(Bm)

            else:
                pass # DO ADC READING STUFF

            print(f"[DEBUG] Bm = {datapool.read_Bm()}")
            sleep(max(0., datapool.threaded_read_ADC_period - (time() - t0)))

        else:
            sleep(datapool.threaded_read_ADC_period)

    print(f"Closing read ADC thread")


# DataPool object
class DataPool:
    def __init__(self):
        # Thread controls
        self._lock_ADC = Lock()                 # Thread lock for ADC value buffers
        self._lock_DAC = Lock()                 # Thread lock for DAC value buffers
        self._lock_schedule = Lock()            # Thread lock for schedule

        self.pause_threaded_read_ADC = False    # Not thread-safe
        self.pause_threaded_write_DAC = False   # Not thread-safe

        self.kill_threaded_read_ADC = False     # Not thread-safe
        self.kill_threaded_write_DAC = False    # Not thread-safe

        self.threaded_read_ADC_period = 1/config["threaded_read_ADC_rate"]  # Not thread-safe
        self.threaded_write_DAC_period = 1/config["threaded_write_DAC_rate"]  # Not thread-safe


        # ==== Data buffers ==================================================
        """ Here all data buffers are defined. They are all defined as lists,
        such that previous data can be stored for potential analysis.
        
        Entry 0 will always be the most recent value, and should therefore be
        useful in most cases. To write to the buffer, use self.write_buffer().
        """

        ibs = config["internal_buffer_size"]

        self.tm = self.init_buffer(ibs, 1)      # Time at which Bm, Im were taken
        self.Im = self.init_buffer(ibs, 3)      # Measured current Im in [A]
        self.Bm = self.init_buffer(ibs, 3)      # Measured field Bm in [nT]

        self.Bc = self.init_buffer(ibs, 3)      # Control vector Bc to be applied [nT]
        self.Vvc = self.init_buffer(ibs, 3)  # Currently unused
        self.Vcc = self.init_buffer(ibs, 3)  # Currently unused

        self.Br = self.init_buffer(ibs, 3)      # Magnetic field vector to be rejected

        self.V_board = self.init_buffer(ibs, 1) # Measured value of +12V bus - +5V bus

        self.i_step = self.init_buffer(ibs, 1)

        self.adc_aux = self.init_buffer(ibs, 1)
        self.dac_aux = self.init_buffer(ibs, 6)

        # ==== Other parameters ==============================================

        self.params_tf_vb = {
            "x": config["params_tf_vb_x"],
            "y": config["params_tf_vb_y"],
            "z": config["params_tf_vb_z"],
        }

        self.params_mutate = config["params_mutate"]

        self.output_enable = False              # Enable/disable H-bridge output using PSUE pin

        # ==== Serveropts ==============================================
        self.serveropt_spoof_Bm = config["spoof_Bm"]

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


    # ==== INTERNAL FUNCTIONS ================================================

    def write_buffer(self, buffer, value):
        """First-in, last-out buffer update function.
        - Increases length of buffer by 1 by inserting new value at position 0
        - Deletes the last value of the buffer using pop()
        Beware: There is NO input validation or type/size checking, you must
        ensure that the value that is written is appropriate!
        """
        buffer.insert(0, value)
        buffer.pop()

    def init_buffer(self, buffer_size, entry_size):
        """Automatically creates a buffer object, which is a list with a number
        of entries. The number of entries is equal to <buffer_size>.
        The entries themselves are lists if <entry_size> is larger than 1,
        making the buffer 2D. For <entry_size> equal to 1, the buffer will be
        1D instead.
        """
        if buffer_size <= 0:
            raise ValueError(f"init_buffer(): buffer_size cannot be {buffer_size}!")

        if entry_size == 1:
            return zeros(buffer_size).tolist()
        elif entry_size > 1:
            return zeros((buffer_size, entry_size)).tolist()
        else:
            raise ValueError(f"init_buffer(): Negative entry_size given!")

    def mutate(self, v_prev, v_central, mutation_scale, fence_strength):
        """Mutate a value from a starting value, but push back if it gets too
        far from some defined central value.
        """
        m = mutation_scale * v_central * (2 * rand() - 1)
        d = v_prev - v_central

        # d=0 causes a singularity later, so side-step it
        if d == 0:
            d = 0.1

        if d / abs(d) == m / abs(m):
            mutagen = m * (1 - abs(d / v_central) * fence_strength)
        else:
            mutagen = m * (1 + abs(d / v_central) * fence_strength)

        return v_prev + mutagen

    def auto_calibrate(self):
        pass # TODO


    # ==== IO FUNCTIONS ======================================================

    def read_Bm(self):
        """Thread-safely reads the current Bm field from the datapool.

        The lock prevents other threads from updating self.Bm whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        try:
            tm = self.tm[0]
            Bm = self.Bm[0]
        except:  # noqa
            print("[WARNING] DataPool.read_Bm(): Unable to read self.Bm!")
        self._lock_ADC.release()
        return tm, Bm

    def write_Bm(self, Bm: list):
        """Thread-safely write Bm to the datapool.

        The lock prevents other threads from accessing self.Bm whilst it is
        being updated. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        try:
            self.write_buffer(self.Bm, Bm) # noqa
        except:  # noqa
            print("[WARNING] DataPool.write_Bm(): Unable to write to self.Bm!")
        self._lock_ADC.release()


    def read_Bc(self):
        """Thread-safely reads the current Bc field from the datapool.

        The lock prevents other threads from updating self.Bc whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            Bc = self.Bc[0]
        except:  # noqa
            print("[WARNING] DataPool.read_Bc(): Unable to read self.Bc!")
        self._lock_DAC.release()
        return Bc

    def write_Bc(self, Bc: list):
        """Thread-safely write Bc to the datapool.

        The lock prevents other threads from accessing self.Bc whilst it is
        being updated. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            self.write_buffer(self.Bc, Bc) # noqa
        except:  # noqa
            print("[WARNING] DataPool.write_Bc(): Unable to write to self.Bc!")
        self._lock_DAC.release()


    def read_Br(self):
        """Thread-safely reads the current Br field from the datapool.

        The lock prevents other threads from updating self.Bc whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            Br = self.Br[0]
        except:  # noqa
            print("[WARNING] DataPool.read_Br(): Unable to read self.Br!")
        self._lock_DAC.release()
        return Br

    def write_Br(self, Br: list):
        """Thread-safely write Br to the datapool.

        The lock prevents other threads from accessing self.Bc whilst it is
        being updated. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            self.write_buffer(self.Br, Br) # noqa
        except:  # noqa
            print("[WARNING] DataPool.write_Br(): Unable to write to self.Br!")
        self._lock_DAC.release()


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
        self.schedule = [[0, 0, 0., 0., 0., 0.], ]*n_seg # TODO NEVER USE THIS

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

    Its behaviour is as follows: It will run setup() once, after which it will
    loop handle() forever. Within handle(), the more specialized function
    command_handle() may be invoked. When the handle() loop is broken, finish()
    will run once, after which the class instance will terminate.
    """

    def setup(self):
        """Overloaded from base class. Runs once before handle() loops."""
        self.socket_tstart = time()
        print(f"Client {self.client_address[0]}:{self.client_address[1]} connected.")

        self.v = config["verbosity"]

    def handle(self):
        """
        This is the default handling routine for any data packets sent to the
        server from any client. Its behaviour is to while-loop forever until
        interrupted.

        Every server-client interaction is blocking for that client. This
        means that every incoming packet warrants a response packet from the
        server before a new packet can be sent from the client. A packet from
        one client will not block a packet coming from another client, as it
        will be interacting with a different instance of the handler running
        in its own thread.

        The first thing that is done when a packet arrives is its type is
        identified. This involves the reading of the first byte character
        through the packet_type() function in the SCC codec, which can be done
        very quickly. Based on the type, a different subroutine is chosen to
        handle the packet. For x-packets, whose contents may vary a lot, the
        handling routines are bundled in the command_handle() function.

        Every subroutine for handling a particular package type will result in
        the creation "package_out", which holds the package that will be sent
        in response. Empty packets will not be sent.
        """
        print("handle()")
        while True:
            packet_out = None
            packet_in = self.request.recv(256)
            # t0 = time()  # [TIMING]
            if packet_in == b"":
                break
            type_id = codec.packet_type(packet_in)
            # t1 = time()  # [TIMING]

            if self.v >= 4:
                print("[DEBUG] packet_in:", packet_in)

            if type_id == "b":
                """b-packets received from a client are considered a request 
                for Bm, and always have their contents discarded. The server
                sends back a b-packet with a timestamp and the current value
                of Bm."""
                if self.v >= 2:
                    print("[DEBUG] Detected b-packet")
                packet_out = codec.encode_bpacket(
                    *self.server.datapool.read_Bm()
                )


            elif type_id == "c":
                """c-packets contain power supply instructions in the form of
                Bc: a desired flux density value for all three axes. Return
                an m-packet with 1 if successfully passed on to the Datapool,
                or -1 if it was unsuccessful."""
                if self.v >= 2:
                    print("[DEBUG] Detected c-packet")
                Bc = codec.decode_cpacket(packet_in)
                try:
                    self.server.datapool.write_Bc(Bc)
                    if self.v >= 4:
                        print("[DEBUG] Bc written to datapool:", Bc, type(Bc))
                        print("[DEBUG] CHECK datapool.Bc:", self.server.datapool.Bc)
                    packet_out = codec.encode_mpacket("1")
                except:  # noqa
                    packet_out = codec.encode_mpacket("-1")


            elif type_id == "e":
                """The purpose of e-packets is to require as little processing 
                as possible, and they will be comstantly coming in from the 
                client, so they are instantly decoded, re-encoded, and echoed 
                back without any additional action."""
                if self.v >= 2:
                    print("[DEBUG] Detected e-packet")
                packet_out = codec.encode_epacket(
                    codec.decode_epacket(packet_in)
                )


            elif type_id == "m":
                """m-packets comprise simple string messages. They are always 
                displayed in the server terminal, and a simple acknowledgement 
                m-packet is sent in response."""
                if self.v >= 2:
                    print("[DEBUG] Detected m-packet")

                msg = codec.decode_mpacket(packet_in)
                print(f"[{self.client_address[0]}:{self.client_address[1]}] {msg}")
                packet_out = codec.encode_mpacket("1")  # Send 1 as confirmation


            elif type_id == "s":
                """s-packets are schedule segments and usually sent in large
                batches. The corresponding entry in the schedule located in
                the Datapool is updated with the information in the s-packet.
                The segment number is sent back as a acknowledgement and 
                verification."""
                if self.v >= 2:
                    print("[DEBUG] Detected s-packet")

                segment = codec.decode_spacket(packet_in)
                self.server.datapool.set_schedule_segment(segment)
                # Send segment number back as a verification
                packet_out = codec.encode_mpacket(str(segment[0]))


            elif type_id == "t":
                """t-packets received from a client are considered a request 
                for telemetry, and always have their contents discarded. The 
                server responds with a t-packet with a timestamp and the 
                latest telemetry values as specified by the SCC codec."""
                if self.v >= 2:
                    print("[DEBUG] Detected t-packet")
                packet_out = codec.encode_tpacket(
                    *self.server.datapool.read_telemetry()
                )


            elif type_id == "x":
                """x-packets always contain a command, the number of additional
                arguments, as well as these additional arguments. This routine
                simply identifies the function name and its arguments, and 
                delegates these to command_handle() for further processing.
                When done, command_handle() returns the contents of packet_out.
                """
                if self.v >= 2:
                    print("[DEBUG] Detected x-packet")
                fname, args = codec.decode_xpacket(packet_in)
                if self.v >= 2:
                    print(f"[DEBUG] {fname}({args})")
                packet_out = self.command_handle(fname, args)


            else:
                """Raise exception when encountering an unrecognised packet 
                type."""
                raise ValueError(f"Encountered uninterpretable type_id '{type_id}' in received packet.")

            if self.v >= 4:
                print("[DEBUG] packet_out:", packet_out)

            # t2 = time()  # [TIMING]

            # Send packet_out:
            if packet_out is not None:
                self.request.sendall(packet_out)

            # t3 = time()  # [TIMING]
            # print(f"Sent {codec.packet_type(packet_out)}-packet. Time: {int((t1-t0)*1E6)}, {int((t2-t1)*1E6)}, {int((t3-t2)*1E6)} \u03bcs")  # [TIMING]


    def command_handle(self, fname, args):
        """
        This function handles the interpretation of all x-packets sent to the
        server, executes the corresponding actions, and composes the
        appropriate properties of the response packet.

        Here is a list of all functions the server currently supports:
        get_Bc
        get_schedule_info
        get_server_uptime
        get_socket_uptime


        """
        packet_out = None

        # Requests the Bc value:
        if fname == "get_Bc":
            packet_out = codec.encode_cpacket(self.server.datapool.read_Bc())

        # Requests the Br value:
        elif fname == "get_Br":
            packet_out = codec.encode_mpacket("{},{},{}".format(
                *self.server.datapool.read_Br()))
        # Sets the Br value:
        elif fname == "set_Br":
            Br = [args[0], args[1], args[2]]
            self.server.datapool.write_Br(Br)
            if self.v >= 4:
                print("[DEBUG] Br written to datapool:", Br, type(Br))
                print("[DEBUG] CHECK datapool.Br:", self.server.datapool.Br)
            packet_out = codec.encode_mpacket("1")


        # Requests the schedule name, length, and duration as csv string
        elif fname == "get_schedule_info":
            name, length, duration = self.server.datapool.get_schedule_info()
            packet_out = codec.encode_mpacket(f"{name},{length},{duration}")


        # Requests the server uptime:
        elif fname == "get_server_uptime":
            packet_out = codec.encode_mpacket(str(self.server.uptime()))


        # Requests the uptime of the communication socket, from the perspective
        # of the server # TODO DEPRECATED IN FAVOUR OF get_socket_info
        elif fname == "get_socket_uptime":
            """Return an m-packet with the time the corresponding client has 
            been connected for."""
            packet_out = codec.encode_mpacket(str(time()-self.socket_tstart))


        elif fname == "get_socket_info":
            """Return an m-packet with some information about the client from
            the perspective of the server:
            1. The time for which the client socket has been active
            2. The client address
            3. The client port
            This information is packaged as a csv string.
            """
            uptime = time()-self.socket_tstart
            packet_out = codec.encode_mpacket(
                f"{uptime},{self.client_address[0]},{self.client_address[1]}"
            )


        # # Requests the value of play mode (False indicates `manual mode`)
        # elif fname == "get_play_mode":
        #     packet_out = codec.encode_mpacket(str(self.server.datapool.get_play_mode()))
        #
        # # Requests the value of play status (False indicates `manual mode`)
        # elif fname == "get_play_status":
        #     packet_out = codec.encode_mpacket(self.server.datapool.get_play_status())


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
    datapool.kill_threaded_write_DAC = True

    ttest = time()
    thread_read_ADC.join(timeout=1.0)
    print(f"Shut down read_ADC thread in {round((time()-ttest)*1E3, 3)} ms")

    ttest = time()
    thread_write_DAC.join(timeout=5.0)
    print(f"Shut down write_DAC thread in {round((time()-ttest)*1E3, 3)} ms")

    # For safety: set power supplies to zero, separately from apply_Bc_thread
    print(f"Resetting Bc just in case")
    hardware_shutdown(datapool)

    # Server termination
    total_uptime = server.uptime()
    server.shutdown()
    server.server_close()
    print(f"Server is closed. Total uptime: {round(total_uptime, 3)} s")


