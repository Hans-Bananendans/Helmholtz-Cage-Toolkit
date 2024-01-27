from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from threading import Thread, Lock, main_thread, active_count
from functools import partial

from numpy.random import random
from time import time, sleep
from scc2 import SCC


# Dummy functions
def instruct_DACs(Bc):
    """Dummy for writing values to DAC"""
    print(f"[DEBUG] Called instruct_DACs({Bc})!")

    return 1


def threaded_write_Bm(datapool, period):
    print(f"[DEBUG] Started write_Bm thread with period {period}")
    datapool.write_Bm_continuously = True

    while datapool.write_Bm_continuously:
        t0 = time()
        datapool.write_Bm()
        # t1 = time()
        # print(f"[DEBUG] set datapool values in {round((t1-t0)*1E6, 3)} us")
        # i += 1
        sleep(period - (time() - t0))

def threaded_apply_Bc(datapool, period):
    # TODO: Replace with actual hardware function. Basic idea is this:
    # 1. Read datapool.Bc
    # 2. Compare value to previously stored value
    # 3. If no change was made, sleep for `period` and start again
    # 4. If a change was detected, apply this change by instructing the DACs
    # TODO: Also build in a graceful way to break this function. It is actively
    # controlling hardware, it is important for it not to get stuck.
    # Can do an external software watchdog, or a non-daemon implementation of
    # thread that always gracefully settles, or place it further up the chain
    # in the main thread.

    print(f"[DEBUG] Started apply_Bc thread with period {period}")
    datapool.apply_Bc_continuously = True

    Bc_prev = [0., 0., 0.]
    while datapool.apply_Bc_continuously:

        t0 = time()
        Bc_read = datapool.read_Bc()
        if Bc_read == Bc_prev:
            sleep(period - (time() - t0))
        else:
            instruct_DACs(Bc_read)
            Bc_prev = Bc_read

    # When loop is broken, set power supply values to zero:
    instruct_DACs([0., 0., 0.])
    sleep(0.001)  # TODO: Evaluate if this is necessary


    print(f"[DEBUG] Closing write_Bm thread")

# def threaded_read_Bm(datapool, period):
#     print(f"[DEBUG] Started read_Bm thread with period {period}")
#     datapool.read_continuously = True
#
#     # while datapool.read_Bm_continuously:
#     i = 0
#     while i < 2:  # TODO: REPLACE
#         t0 = time()
#         Bm = datapool.read_Bm()
#         # t1 = time()
#         # print(f"[DEBUG] set datapool values in {round((t1-t0)*1E6, 3)} us")
#         print(f"[DEBUG] threaded_read_Bm(): Read Bm: {Bm}")
#         i += 1
#         sleep(period-(time()-t0))

    print(f"[DEBUG] Closing write_Bm thread")

# DataPool
class DataPool:
    def __init__(self):
        self._lock_Bm = Lock()
        self._lock_Bc = Lock()
        # self.starttime = 0

        self.read_Bm_continuously = True
        self.write_Bm_continuously = True
        self.apply_Bc_continuously = True

        self.Bm = [0., 0., 0., 0.]
        self.Bc = [0., 0., 0.]
        self.cbx = 0.
        self.cby = 0.
        self.cbz = 0.

    def write_Bm(self):  # TODO: DUMMY - Implement actual functionality
        t = time()
        # Generate 3 dummy values of [-50,000 , +50,000] nT
        b1, b2, b3 = (random(3) * 100_000 - 50_000).round(1)

        t_la = time()
        # The lock prevents other threads from accessing self.Bm whilst it is
        # being updated. Useful to prevent hard-to-debug race condition bugs.
        self._lock_Bm.acquire(timeout=0.001)
        try:
            self.Bm = [t, b1, b2, b3]
        except:  # noqa
            print("[DEBUG] DataPool.write_Bm(): Unable to write to self.Bm!")
        self._lock_Bm.release()
        t_lr = time()

        # print(f"[DEBUG] DataPool.write_Bm(): Lock active for {round((t_lr-t_la)*1E6, 3)} us")
        # print(f"[DEBUG] DataPool.write_Bm(): Completed in {round((time()-t)*1E6, 3)} us")

    def read_Bm(self):
        """Thread-safely reads the current Bm field from the datapool"""

        t_la = time()
        # The lock prevents other threads from updating self.Bm whilst it is
        # being read. Useful to prevent hard-to-debug race condition bugs.
        self._lock_Bm.acquire(timeout=0.001)
        try:
            Bm = self.Bm
        except:  # noqa
            print("[DEBUG] DataPool.read_Bm(): Unable to read self.Bm!")
        self._lock_Bm.release()
        t_lr = time()

        # print(f"[DEBUG] DataPool.read_Bm(): Lock active for {round((t_lr-t_la)*1E6, 3)} us")
        # print(f"[DEBUG] DataPool.read_Bm(): Completed in {round((time()-t_la)*1E6, 3)} us")

        return Bm

    def write_Bc(self, Bc):  # TODO: DUMMY - Implement actual functionality
        """Thread-safely write Bc to the datapool"""

        t_la = time()
        # The lock prevents other threads from accessing self.Bc whilst it is
        # being updated. Useful to prevent hard-to-debug race condition bugs.
        self._lock_Bc.acquire(timeout=0.001)
        try:
            self.Bc = Bc
        except:  # noqa
            print("[DEBUG] DataPool.write_Bc(): Unable to write to self.Bc!")
        self._lock_Bc.release()
        t_lr = time()

        # print(f"[DEBUG] DataPool.write_Bc(): Lock active for {round((t_lr-t_la)*1E6, 3)} us")
        # print(f"[DEBUG] DataPool.write_Bc(): Completed in {round((time()-t)*1E6, 3)} us")


    def read_Bc(self):
        """Thread-safely reads the current Bc field from the datapool"""

        t_la = time()
        # The lock prevents other threads from updating self.Bc whilst it is
        # being read. Useful to prevent hard-to-debug race condition bugs.
        self._lock_Bc.acquire(timeout=0.001)
        try:
            Bc = self.Bc
        except:  # noqa
            print("[DEBUG] DataPool.read_Bc(): Unable to read self.Bc!")
        self._lock_Bc.release()
        t_lr = time()

        # print(f"[DEBUG] DataPool.read_Bc(): Lock active for {round((t_lr-t_la)*1E6, 3)} us")
        # print(f"[DEBUG] DataPool.read_Bc(): Completed in {round((time()-t_la)*1E6, 3)} us")

        return Bc

# # Make threaded loop
# class ThreadedADCRead(Thread):
#     def __init__(self, datapool):
#         self._datapool = datapool
#
#     def run(self):
#         pass
#
#
# class ThreadedDACWrite(Thread):
#     def __init__(self, datapool):
#         self._datapool = datapool
#
#     def run(self):
#         pass




# Make inherited TCP Server class with threading enabled
class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    # def __init__(self, *args, **kwargs):  # TODO: Remove
    #     print("SERVER- DOES THIS EVEN RUN?")
    #     self._datapool = datapool
    #     print("datapool =", self._datapool)
    #
    #     super().__init__(*args, **kwargs)
    def __init__(self, host, handler, datapool):
        # print("SERVER- DOES THIS EVEN RUN?")  # TODO: Remove
        self.datapool = datapool
        self.server_tstart = time()
        # print("datapool =", self.datapool)  # TODO: Remove

        super().__init__(host, handler)

    def uptime(self):
        return time() - self.server_tstart


# Thread-handler
class ThreadedTCPRequestHandler(BaseRequestHandler):
    # Override __init__() to have entry point for data pool  # TODO: Remove
    # def __init__(self, datapool, *args, **kwargs):
    #
    #     print("HANDLER - DOES THIS EVEN RUN?")
    #     self._datapool = datapool
    #     print("datapool =", self._datapool)
    #
    #     super().__init__(*args, **kwargs)


    def setup(self):
        self.socket_tstart = time()
        print(f"Client {self.client_address[0]}:{self.client_address[1]} connected.")

    def handle(self):
        # print("DATAPOOL TEST: self.server._datapool =", self.server._datapool)  # TODO: Remove
        while True:
            packet_out = None
            packet_in = self.request.recv(256)
            if packet_in == b"":
                break
            type_id = SCC.packet_type(packet_in)

            if type_id == "m":
                print("[DEBUG] Detected m-package")
                msg = SCC.decode_mpacket(packet_in)
                print("[MSG]", msg)

            elif type_id == "e":
                print("[DEBUG] Detected e-package")
                packet_out = SCC.encode_epacket(SCC.decode_epacket(packet_in))

            elif type_id == "b":
                print("[DEBUG] Detected b-package")
                packet_out = SCC.encode_bpacket(self.server.datapool.read_Bm())

            elif type_id == "c":
                print("[DEBUG] Detected c-package")
                Bc = SCC.decode_cpacket(packet_in)
                try:
                    self.server.datapool.write_Bc(Bc)
                    print("[DEBUG] Bc written to datapool:", Bc, type(Bc))
                    packet_out = SCC.encode_mpacket(1)
                except:  # noqa
                    packet_out = SCC.encode_mpacket(-1)

            elif type_id == "x":
                print("[DEBUG] Detected x-package")
                fname, args = SCC.decode_xpacket(packet_in)
                print(f"[DEBUG] {fname}({args})")
                packet_out = self.command_handle(fname, args)

            else:
                raise ValueError(f"Encountered uninterpretable type_id '{type_id}' in received packet.")

            # If a response was warranted, send it:
            if packet_out is not None:
                self.request.sendall(packet_out)

    def command_handle(self, fname, args):
        packet_out = None

        # Requests the server uptime:
        if fname == "server_uptime":
            packet_out = SCC.encode_mpacket(self.server.uptime())

        # Requests the uptime of the communication socket, from the perspective
        # of the server
        elif fname == "socket_uptime":
            packet_out = SCC.encode_mpacket(time()-self.socket_tstart)

        # Alternative echo, mainly for testing purposes. Echoes the first
        # argument given to it, or an empty string if no arguments were given.
        elif fname == "echo":
            if len(args) == 0:
                packet_out = SCC.encode_epacket("")
            else:
                packet_out = SCC.encode_epacket(args[0])

        else:
            raise ValueError(f"Function name '{fname}' not recognised!")
        return packet_out


    def finish(self):
        print(f"Client {self.client_address[0]}:{self.client_address[1]} disconnected.")


if __name__ == "__main__":

    print(f"[DEBUG] Main thread: {main_thread()}")
    print(f"[DEBUG] n_threads: {active_count()}")

    datapool = DataPool()

    # Server object
    HOST = ("127.0.0.1", 7777)  # TODO replace with config

    # Evaluating the constructor of ThreadedTCPRequestHandler as a partial
    # function in order to inject the DataPool instance.
    # test = ThreadedTCPRequestHandler
    # handler = partial(ThreadedTCPRequestHandler, datapool=datapool)
    # print(handler, type(handler))

    # Evaluating the constructor of ThreadedTCPServer as a partial
    # function in order to inject the DataPool instance, so that it can be
    # used both inside the server object and every ThreadedTCPRequestHandler
    # instanced slaved to it.
    # server_partial = partial(ThreadedTCPServer, datapool=datapool)
    # server = server_partial(HOST, ThreadedTCPRequestHandler, datapool)
    # server = ThreadedTCPServer(HOST, handler)
    server = ThreadedTCPServer(HOST, ThreadedTCPRequestHandler, datapool)


    # Makes all child threads of the server thread daemonic, forcing them to
    # terminate when main thread terminates.
    server.daemon_threads = True

    # Place server in own thread
    server_thread = Thread(target=server.serve_forever)

    # Make server thread daemonic, so it too will terminate upon main thread
    # termination
    server_thread.daemon = True

    # Start server thread
    server_thread.start()

    print(f"[DEBUG] n_threads: {active_count()}")

    print("Server is up.")

    # Set up thread for continuously polling magnetic field data from ADC, and
    # writing it to datapool.Bm
    measure_Bm_thread = Thread(
        name="Measure Bm Thread",
        target=threaded_write_Bm,
        args=(datapool, 0.1),
        daemon=True)
    measure_Bm_thread.start()

    # Set up thread that finds when a change in datapool.Bc occurs, and when
    # it occurs, that it gets applied to the power supplies.
    apply_Bc_thread = Thread(
        name="Apply Bc Thread",
        target=threaded_apply_Bc,
        args=(datapool, 0.1),
        daemon=False)  # Not set as daemon to ensure that it finishes at the end
    apply_Bc_thread.start()

    print(f"[DEBUG] n_threads: {active_count()}")


    while True:
        try:
            # Do something useful
            sleep(0.1)
            pass

        except:  # noqa
            break

    # Gracefully terminate control threads
    print("Shutting down - finishing threads.")
    datapool.read_Bm_continuously = False
    datapool.write_Bm_continuously = False
    datapool.apply_Bc_continuously = False

    ttest = time()
    measure_Bm_thread.join(timeout=1)
    print(f"Shut down measure_Bm_thread in {round((time()-ttest)*1E3, 3)} ms")
    ttest = time()
    apply_Bc_thread.join(timeout=1)
    print(f"Shut down apply_Bc_thread in {round((time()-ttest)*1E3, 3)} ms")

    # For safety: set power supplies to zero, separately from apply_Bc_thread
    instruct_DACs([0., 0., 0.])

    total_uptime = server.uptime()
    # Server termination
    server.shutdown()
    server.server_close()
    print(f"Server is closed. Total uptime: {round(total_uptime, 3)} s")


