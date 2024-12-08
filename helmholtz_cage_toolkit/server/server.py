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

from hashlib import blake2b
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
                Bm_prev = datapool.read_Bm()[1]
                # print("[DEBUG] Bm_prev", Bm_prev)
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

            # print(f"[DEBUG] Bm = {datapool.read_Bm()}")
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

        self.i_step = self.init_buffer(ibs, 1, dtype=int)

        self.aux_adc = self.init_buffer(ibs, 1)
        self.aux_dac = self.init_buffer(ibs, 6)

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

    def init_buffer(self, buffer_size, entry_size, dtype=float):
        """Automatically creates a buffer object, which is a list with a number
        of entries. The number of entries is equal to <buffer_size>.
        The entries themselves are lists if <entry_size> is larger than 1,
        making the buffer 2D. For <entry_size> equal to 1, the buffer will be
        1D instead.
        """
        if buffer_size <= 0:
            raise ValueError(f"init_buffer(): buffer_size cannot be {buffer_size}!")

        if entry_size == 1:
            return zeros(buffer_size, dtype=dtype).tolist()
        elif entry_size > 1:
            return zeros((buffer_size, entry_size), dtype=dtype).tolist()
        else:
            raise ValueError(f"init_buffer(): Negative entry_size given!")

    def mutate(self, v_prev, v_central, mutation_scale, fence_strength):
        """Mutate a value from a starting value, but push back if it gets too
        far from some defined central value.
         - v_prev is the value to mutate
         - v_central is the value around which the mutation will move
         - mutation_scale is the size of the mutation steps
         - fence_strength increases how tightly the mutation is kept near
            v_central
        Convergence is not guaranteed for all values. If mutation_scale is too
        large in comparison to fence_strength and v_central, the results may
        become unbound.
        """
        # strs = ["v_prev", "v_central", "mutation_scale", "fence_strength"]
        # for i, var in enumerate((v_prev, v_central, mutation_scale, fence_strength)):
        #     print("[DEBUG]", strs[i], var)

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

    def measure_performance(self):
        pass # TODO

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

    def read_telemetry(self):
        """Thread-safely reads the telemetry data from the datapool.

        The lock prevents other threads from updating this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        self._lock_DAC.acquire(timeout=0.001)
        try:
            tm = self.tm[0]
            i_step = self.i_step[0]
            Im = self.Im[0]
            Bm = self.Bm[0]
            Bc = self.Bc[0]
        except:  # noqa
            print("[WARNING] DataPool.read_telemetry(): Unable to read telemetry!")
        self._lock_ADC.release()
        self._lock_DAC.release()
        return tm, i_step, Im, Bm, Bc


    def write_ADC_data(self, Bm, Im, V_board, aux_adc):
        """Thread-safely writes all ADC data to their corresponding fields
         in the datapool.

        The lock prevents other threads from accessing this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        try:
            self.write_buffer(self.Bm, Bm)  # noqa
            self.write_buffer(self.Im, Im)  # noqa
            self.write_buffer(self.V_board, V_board)  # noqa
            self.write_buffer(self.aux_adc, aux_adc)  # noqa
        except:  # noqa
            print("[WARNING] DataPool.read_Bm(): Unable to read self.Bm!")
        self._lock_ADC.release()


    def read_aux_adc(self):
        """Thread-safely reads the ADC aux1 channel data from the datapool.

        The lock prevents other threads from updating this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        try:
            aux_adc = self.aux_adc[0]
        except:  # noqa
            print("[WARNING] DataPool.read_aux_adc: Exception!")
        self._lock_ADC.release()
        return aux_adc

    def read_V_board(self):
        """Thread-safely reads the board voltage data from the datapool.

        The lock prevents other threads from updating this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_ADC.acquire(timeout=0.001)
        try:
            V_board = self.V_board[0]
        except:  # noqa
            print("[WARNING] DataPool.read_V_board(): Exception!")
        self._lock_ADC.release()
        return V_board

    def read_output_enable(self):
        """Thread-safely reads the output_enable toggle from the datapool.

        The lock prevents other threads from updating this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            output_enable = self.output_enable
        except:  # noqa
            print("[WARNING] DataPool.read_output_enable(): Exception!")
        self._lock_DAC.release()
        return output_enable

    def write_output_enable(self, output_enable: bool):
        """Thread-safely writes the output_enable toggle to the datapool.

        The lock prevents other threads from updating this data whilst it is
        being read. Useful to prevent hard-to-debug race condition bugs.
        """
        self._lock_DAC.acquire(timeout=0.001)
        try:
            self.output_enable = output_enable
        except:  # noqa
            print("[WARNING] DataPool.write_output_enable(): Exception!")
        self._lock_DAC.release()


    # ==== SCHEDULE HANDLING =================================================

    def read_schedule_segment(self, segment_id: int):
        """Thread-safely reads a schedule segment from the schedule in the
        datapool, if it exists, and returns it. If it does not exist, it
        returns 0.

        The lock prevents other threads from accessing the schedule whilst it
        is being edited. Useful to prevent hard-to-debug race condition bugs.
        """
        # print("[DEBUG] read_schedule_segment()")

        self._lock_schedule.acquire(timeout=0.001)

        if segment_id > len(self.schedule) - 1:
            print(f"[WARNING] get_schedule_segment(): Tried to set " +
                  f"segment {segment_id}, but this is out of bounds for a " +
                  f"schedule of length {len(self.schedule)}!")
            return 0

        segment = self.schedule[segment_id]
        self._lock_schedule.release()
        return segment

    def write_schedule_segment(self, segment: list):
        """Thread-safely writes a schedule segment into the schedule, by
        consulting the ID of the segment (first entry, segment[0]) and writing
        it to the schedule object.

        The lock prevents other threads from accessing the schedule whilst it
        is being edited. Useful to prevent hard-to-debug race condition bugs.
        """
        # print("[DEBUG] write_schedule_segment()")

        self._lock_schedule.acquire(timeout=0.001)
        self.schedule[segment[0]] = segment
        self.schedule_hash = ""     # Modifying the schedule voids the hash.
        self._lock_schedule.release()


    def initialize_schedule(self):
        """Thread-safely writes the default init schedule to the datapool.
        Returns a 1 for remote confirmation purposes.

        The lock prevents other threads from accessing the schedule whilst it
        is being edited. Useful to prevent hard-to-debug race condition bugs.
        """
        # print("[DEBUG] initialize_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule_hash = ""     # Modifying the schedule voids the hash.

        self.schedule = [[0, 0, 0., 0., 0., 0.], ]
        self.schedule_name = "init"
        self.schedule_duration = 0.0

        self._lock_schedule.release()

        # print(f"[DEBUG] HASH INIT {self.schedule_hash}")
        return 1


    def allocate_schedule(self, name: str, n_seg: int, duration: float):
        """Thread-safely allocates an empty schedule of a defined size. This
        schedule then has to be filled with segments by using
        write_schedule_segment(). The schedule name and duration are also
        written to the datapool. Returns a 1 for remote confirmation purposes.

        Note that the dtypes of the empty schedule values will all be float,
        where some have to be int, but write_schedule_segment() addresses this.

        The lock prevents other threads from accessing the schedule whilst it
        is being edited. Useful to prevent hard-to-debug race condition bugs.
        """
        # print("[DEBUG] allocate_schedule()")

        self._lock_schedule.acquire(timeout=0.001)

        self.schedule_hash = ""     # Modifying the schedule voids the hash.

        self.schedule_name = name
        self.schedule_duration = duration
        # self.schedule = [[0, 0, 0., 0., 0., 0.], ]*n_seg  # Risky implementation
        self.schedule = self.init_buffer(n_seg, 6)

        self._lock_schedule.release()

        # print(f"[DEBUG] HASH ALLOC {self.schedule_hash}")

        return 1

    def read_schedule_hash(self, generate_hash=True):
        """Thread-safely reads the value of self.schedule_hash and returns it.
        If the hash is empty, generate it, but only when allowed.

        The reason for potentially disallowing it is that hashing takes
        significant time and computational resources, and since accessing it
        here thread-locks the object, it means that it cannot be accessed for
        schedule playback, which would result in execution lag.

        The lock prevents other threads from accessing the schedule whilst it
        is being edited. Useful to prevent hard-to-debug race condition bugs.

        [DEV NOTE] As an extra safety/performance measure, the schedule could
        be deep-copied so that the thread lock can be lifted while the hashing
        function works on the schedule copy. However, this will take twice the
        memory resources, and for large schedules, where you expect the hashing
        to take a long time, available memory will already be limited. So this
        idea has been shelved for now, but may be revisited in the future.
        """
        # print("[DEBUG] read_schedule_hash()")

        self._lock_schedule.acquire(timeout=30.000)

        schedule_hash = self.schedule_hash

        if schedule_hash == "" and generate_hash is True:
            t0 = time()
            schedule_hash = blake2b(
                array(self.schedule).tobytes(), digest_size=8
            ).hexdigest()
            print(f"[BLAKE2B] Hash generated in {int((time()-t0)*1E6)} \u03bcs")
            self.schedule_hash = schedule_hash

        self._lock_schedule.release()
        return schedule_hash

    def read_schedule_info(self, generate_hash=True):
        # print("[DEBUG] read_schedule_info()")

        self._lock_schedule.acquire(timeout=0.001)

        name = self.schedule_name
        length = len(self.schedule)
        duration = self.schedule_duration

        self._lock_schedule.release()

        # print(f"[DEBUG] HASH SI 1 {self.schedule_hash}")

        schedule_hash = self.read_schedule_hash(generate_hash=generate_hash)

        # print(f"[DEBUG] HASH SI 2 {self.schedule_hash}")

        return name, length, duration, schedule_hash

    def print_schedule_info(self, max_entries=16):
        self._lock_schedule.acquire(timeout=0.001)

        print(" ==== SCHEDULE INFO ==== ")
        print("Name:    ", self.schedule_name)
        print("n_seg:   ", len(self.schedule))
        print("Duration:", self.schedule_duration)
        print("Hash", self.schedule_hash)

        if len(self.schedule) == 0:
            pass
        elif len(self.schedule) == 1:
            print(" [Preview]")
            print(self.schedule[0])
        elif len(self.schedule) == 2:
            print(" [Preview]")
            print(self.schedule[0])
            print(self.schedule[1])
        else:
            print(" [Preview]")
            n_prints = min(len(self.schedule), max_entries)
            for i_seg in range(0, int(n_prints/2)):
                print(self.schedule[i_seg])
            if len(self.schedule) > max_entries:
                print("...         ...")
            for i_seg in range(-int(n_prints/2), 0):
                print(self.schedule[i_seg])

        self._lock_schedule.release()
        return 1


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
                self.server.datapool.write_schedule_segment(segment)
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

        get_aux_adc
        get_aux_dac / set_aux_dac
        get_Bc
        get_Br / set_Br
        get output_enable / set output_enable
        get_schedule_info
        get_server_uptime
        get_socket_info
        get_serveropt_spoof_Bm / set_serveropt_spoof_Bm
        get_V_board

        """
        packet_out = None

        if fname == "get_aux_adc":
            packet_out = codec.encode_mpacket(
                str(self.server.datapool.read_aux_adc()))


        elif fname == "get_aux_dac":
            dac = self.server.datapool.aux_dac[0]               # Not thread-safe
            packet_out = codec.encode_mpacket(
                f"{dac[0]},{dac[1]},{dac[2]},{dac[3]},{dac[4]},{dac[5]}"
            )

        elif fname == "set_aux_dac":
            dac_str = [args[0], args[1], args[2], args[3], args[4], args[5]]
            dac_vals = [float(item) for item in dac_str]
            self.server.datapool.write_buffer(
                self.server.datapool.aux_dac, dac_vals
            )                                               # Not thread-safe
            dac = self.server.datapool.aux_dac[0]           # Not thread-safe
            packet_out = codec.encode_mpacket(
                f"{dac[0]},{dac[1]},{dac[2]},{dac[3]},{dac[4]},{dac[5]}"
            )


        # Requests the Bc value:
        elif fname == "get_Bc":
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


        elif fname == "get_output_enable":
            packet_out = codec.encode_mpacket(
                str(int(self.server.datapool.read_output_enable()))
            )

        elif fname == "set_output_enable":
            bool_val = bool(int(args[0]))
            self.server.datapool.write_output_enable(bool_val)
            packet_out = codec.encode_mpacket(str(int(bool_val)))

        # Requests the server uptime:
        elif fname == "get_server_uptime":
            packet_out = codec.encode_mpacket(str(self.server.uptime()))

        elif fname == "set_serveropt_spoof_Bm":
            self.server.datapool.serveropt_spoof_Bm = bool(int(args[0]))    # Not thread-safe
            packet_out = codec.encode_mpacket(
                str(int(self.server.datapool.serveropt_spoof_Bm)))          # Not thread-safe
            if self.v >= 4:
                print(f"[DEBUG] serveropt_spoof_Bm() set {bool(int(args[0]))}")

        elif fname == "get_serveropt_spoof_Bm":
            packet_out = codec.encode_mpacket(
                str(int(self.server.datapool.serveropt_spoof_Bm)))          # Not thread-safe



        # ==== Schedule and playback functions ===============================

        # Prints info about the schedule into the terminal
        elif fname == "print_schedule_info":
            confirm = self.server.datapool.print_schedule_info(max_entries=args[0])
            packet_out = codec.encode_mpacket(str(confirm))

        # Requests the schedule name, length, and duration as csv string
        elif fname == "get_schedule_info":
            # print("[DEBUG] Generate_hash:", bool(int(args[0])))
            # print(self.server.datapool.schedule_hash)
            name, length, duration, schedule_hash = \
                self.server.datapool.read_schedule_info(
                    generate_hash=bool(int(args[0]))
                )
            # print(self.server.datapool.schedule_hash)
            # print(schedule_hash)
            packet_out = codec.encode_mpacket(
                f"{name},{length},{duration},{schedule_hash}"
            )

        elif fname == "get_schedule_segment":
            seg = self.server.datapool.read_schedule_segment(args[0])
            packet_out = codec.encode_spacket(
                seg[0], seg[1], seg[2], seg[3], seg[4], seg[5]
            )

        # Initialize the schedule (reset)
        elif fname == "initialize_schedule":
            confirm = self.server.datapool.initialize_schedule()
            packet_out = codec.encode_mpacket(str(confirm))

        # Allocate an empty schedule (args: name: str, n_seg: int, duration: float)
        elif fname == "allocate_schedule":
            confirm = self.server.datapool.allocate_schedule(args[0], args[1], args[2])
            packet_out = codec.encode_mpacket(str(confirm))


        # # Requests the uptime of the communication socket, from the perspective
        # # of the server # TODO DEPRECATED IN FAVOUR OF get_socket_info
        # elif fname == "get_socket_uptime":
        #     """Return an m-packet with the time the corresponding client has
        #     been connected for."""
        #     packet_out = codec.encode_mpacket(str(time()-self.socket_tstart))


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


        elif fname == "get_V_board":
            packet_out = codec.encode_mpacket(
                str(self.server.datapool.read_V_board()))

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


