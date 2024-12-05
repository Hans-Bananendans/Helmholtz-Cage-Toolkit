import sys
import socket
from time import time, sleep


from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.scc.scc3 as scc
import helmholtz_cage_toolkit.client_functions as cf

"""
In-the-loop test of difference in overhead of b-packets vs. t-packets.

Result:
1E5 b-packets exchanged + processed: 57.6 us/p
1E5 t-packets exchanged + processed: 81.1 us/p
    
Conclusion: 
The additional encoding, decoding, and server-side processing of t-packets 
result in an absolute average overhead of 23.5 us per package compared to 
b-packets.
"""


# HOST = "169.254.241.64"  # whatever outside connection
HOST = "127.0.0.1"  # localhost
PORT = 7777

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

        ds = QDataStream()
        print(""); sleep(0.1)


        # ==== Set up server with dummy Bm to check it's reading correctly
        cf.set_serveropt_Bm_sim(s, "constant", ds)
        cf.set_Bm_sim(s, [50_000., 25_000., 75_000.], ds)
        sleep(0.1)  # Wait for Bm on server to hook Bm_sim dummy value


        # ==== Verify
        telem1 = cf.get_telemetry(s, ds)
        telem2 = cf.get_Bm(s, ds)

        for thing in (telem1, telem2):
            print(thing)


        # ==== Test
        n_packets = 10000

        t_f1 = [0.] * n_packets
        t_f2 = [0.] * n_packets

        # Exchange t-packets
        for i in range(n_packets):
            t0 = time()
            telem = cf.get_telemetry(s, ds)
            t1 = time()
            t_f1[i] = t1-t0

        sleep(1) # Let settle just in case

        # Exchange b-packets
        for i in range(n_packets):
            t0 = time()
            telem = cf.get_Bm(s, ds)
            t1 = time()
            t_f2[i] = t1-t0

        sleep(1)

        print("t_avg get_telemetry(): ", round(sum(t_f1)/len(t_f1)*1E6, 3), "\u03bcs")
        print("t_avg get_Bm()       : ", round(sum(t_f2)/len(t_f2)*1E6, 3), "\u03bcs")


        # ==== Cleanup: disabling Bm_sim functionality on server again
        cf.set_serveropt_Bm_sim(s, "disabled", ds)


        # ============================
        # ==== Uptimes
        print(f"Socket uptime {round(cf.get_socket_uptime(s), 3)} s")
        print(f"Server uptime {round(cf.get_server_uptime(s), 3)} s")
        print(""); sleep(0.1)

        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)