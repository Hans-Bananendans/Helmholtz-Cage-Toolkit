"""
One-stop-shop automated test routine to test most server functionalities.
This implementation uses 'socket' sockets rather than QTcpSocket sockets, which
may make the tests a bit less representative.
"""

import sys
import socket
from time import time, sleep
from hashlib import blake2b
from timeit import timeit

from helmholtz_cage_toolkit import *
import helmholtz_cage_toolkit.scc.scc4 as codec
import helmholtz_cage_toolkit.client_functions as cf
from helmholtz_cage_toolkit.server.server_config import server_config


HOST = server_config["SERVER_ADDRESS"]
PORT = server_config["SERVER_PORT"]

cc = "\033[96m" # cyan
cg = "\033[92m" # green
cr = "\033[91m" # red
ce = "\033[0m"  # endc


timing = False  # Set False to hide timing statistics

details = False

if __name__ == "__main__":

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((HOST, PORT))
            t_start = time()
            print(f"Connection to {HOST}:{PORT} established.")
            print(f"Accessing from {s.getsockname()[0]}:{s.getsockname()[1]}.")
        except:  # noqa
            print("Connection failed!")
            sys.exit(0)

        ds = QDataStream()


        print("\n ==== Starting tests ====")
        n = 99
        i = 1


        # ==== Test pings ====
        t0 = time()
        r = cf.ping(s, ds)
        t1 = time()
        if r != -1:
            print(cg + f" {i}/{n} Test ping                 PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Test ping                 FAIL" + ce)
        i += 1


        # ==== Test pings ====
        n_pings = 100
        t_pings = cf.ping_n(s, n_pings, ds)
        if t_pings != -1:
            print(cc + f" {i}/{n} Test pings ({n_pings})          {int(1E6*t_pings)} \u03bcs" + ce)
        else:
            print(cr + f" {i}/{n} Test pings ({n_pings})          FAIL" + ce)
        i += 1


        # ==== Echo message ====
        msg = "Test echo message"
        t0 = time()
        r = cf.echo(s, msg, ds)
        t1 = time()
        if r == msg:
            print(cg + f" {i}/{n} Echo message              PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Echo message              FAIL")
            print(f"msg:       {msg}")
            print(f"response:  {r}" + ce)
        i += 1


        # ==== Message packet ====
        msg = "Test message"
        t0 = time()
        r = cf.message(s, msg, ds)
        t1 = time()
        if r == 1:
            print(cg + f" {i}/{n} Send message              PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Send message              FAIL")
            print(f"msg:       {msg}")
            print(f"response:  {r}" + ce)
        i += 1


        # ==== Get server uptime ====
        t0 = time()
        r = cf.get_server_uptime(s, ds)
        t1 = time()
        if isinstance(r, float) and r > 0:
            print(cg + f" {i}/{n} Get server uptime         PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Get server uptime         FAIL")
            print(f"response: {r}" + ce)
        i += 1


        # ==== Get socket info ====
        t0 = time()
        r = cf.get_socket_info(s, ds)
        t1 = time()
        diff = (t1-t_start)-r[0]
        if isinstance(r[0], float) and abs(diff) <= 0.01 and isinstance(r[1], str) \
                and isinstance(r[2], int) and r[2] >= 0:
            print(cg + f" {i}/{n} Get socket info           PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       -> Uptime: {round(r[0], 6)} (diff: {round(diff*1E6)} \u03bcs)" + ce)
                print(cg + f"       -> Socket: {r[1]}:{r[2]}" + ce)
        else:
            print(cr + f" {i}/{n} Get socket info           FAIL" + ce)
            print(cr + f"Uptime: {round(r[0], 6)} (diff: {round(diff*1E6)} \u03bcs)" + ce)
            print(cr + f"Socket: {r[1]}:{r[2]} ({type(r[1])}:{type(r[2])})" + ce)
        i += 1


        # ==== Get Bm ====
        t0 = time()
        tm, Bm = cf.get_Bm(s, ds)
        t1 = time()
        if tm >= 0 and len(Bm) == 3 \
                and [True for v in Bm if isinstance(v, float)] == [True, ]*3:
            print(cg + f" {i}/{n} Get Bm                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       -> {tm}, {Bm}" + ce)
        else:
            print(cr + f" {i}/{n} Get Bm                    FAIL")
            print(f"tm: {tm}")
            print(f"Bm: {Bm}" + ce)
        i += 1


        # ==== Set Bc ====
        Bc_test = [3.3, 6.6, -9.9]
        t0 = time()
        r = cf.set_Bc(s, Bc_test, ds)
        t1 = time()
        if r == 1:
            print(cg + f" {i}/{n} Set Bc                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f" {i}/{n} Set Bc                    FAIL")
        i += 1

        # ==== Get Bc ====
        t0 = time()
        Bc = cf.get_Bc(s, ds)
        t1 = time()
        if Bc == Bc_test:
            print(cg + f" {i}/{n} Get Bc                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       {Bc} -> {Bc}" + ce)
        else:
            print(cr + f" {i}/{n} Get Bc                    FAIL")
            if details:
                print(f"Bc set:      {Bc_test}")
                print(f"Bc response: {Bc}" + ce)
        i += 1


        # ==== Set Br ====
        Br_test = [2.2, 5.5, -8.8]
        t0 = time()
        r = cf.set_Br(s, Br_test, ds)
        t1 = time()
        if r == 1:
            print(cg + f"{i}/{n} Set Br                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Set Br                    FAIL")
        i += 1

        # ==== Get Br ====
        t0 = time()
        Br = cf.get_Br(s, ds)
        t1 = time()
        if Br == Br_test:
            print(cg + f"{i}/{n} Get Br                    PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       {Br_test} -> {Br}" + ce)
        else:
            print(cr + f"{i}/{n} Get Br                    FAIL")
            print(f"Bc set:      {Br_test}")
            print(f"Bc response: {Br}" + ce)
        i += 1


        # ==== Get telemetry ====
        t0 = time()
        tm, i_step, Im, Bm, Bc = cf.get_telemetry(s, ds)
        t1 = time()
        txt = ["tm", "i_step", "Im", "Bm", "Bc"]
        if isinstance(tm, float) and tm >= 0. \
                and isinstance(i_step, int) and i_step >= 0 \
                and len(Im+Bm+Bc) == 9 \
                and [isinstance(v, float) for v in Im+Bm+Bc] == [True, ]*9:
            print(cg + f"{i}/{n} Get telemetry             PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                for j, val in enumerate((tm, i_step, Im, Bm, Bc)):
                    print(cg + f"       {txt[j]}: {val}" + ce)
        else:
            print(cr + f"{i}/{n} Get telemetry             FAIL" + ce)
            for j, val in enumerate((tm, i_step, Im, Bm, Bc)):
                print(cr + f"       {txt[j]}: {val}" + ce)
        i += 1


        # ==== Set / Get output_enable ====
        ts0 = time()
        rs0 = cf.set_output_enable(s, True, ds)
        ts1 = time()

        tg0 = time()
        rg0 = cf.get_output_enable(s, ds)
        tg1 = time()

        rs1 = cf.set_output_enable(s, False, ds)
        rg1 = cf.get_output_enable(s, ds)

        if rs0 and not rs1:
            print(cg + f"{i}/{n} Set output_enable         PASS ({int(1E6*(ts1-ts0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Set output_enable         FAIL")
            print(f"Enable True:  {rs0}")
            print(f"Enable False: {rs1}" + ce)
        i += 1

        if rg0 and not rg1:
            print(cg + f"{i}/{n} Get output_enable         PASS ({int(1E6*(tg1-tg0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Get output_enable         FAIL")
            print(f"Enable True:  {rg0}")
            print(f"Enable False: {rg1}" + ce)
        i += 1


        # ==== Get V_board ====
        t0 = time()
        V_board = cf.get_V_board(s, ds)
        t1 = time()
        if isinstance(V_board, float):
            print(cg + f"{i}/{n} Get V_board               PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       V_board: {V_board}" + ce)
        else:
            print(cr + f"{i}/{n} Get V_board               FAIL")
            print(f" V_board: {V_board}" + ce)
        i += 1


        # ==== Get aux ADC ====
        t0 = time()
        aux_adc = cf.get_aux_adc(s, ds)
        t1 = time()
        if isinstance(aux_adc, float):
            print(cg + f"{i}/{n} Get aux ADC               PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       aux ADC: {aux_adc}" + ce)
        else:
            print(cr + f"{i}/{n} Get aux ADC               FAIL")
            print(f"V_board: {aux_adc}" + ce)
        i += 1


        # ==== Set / Get aux DAC ====
        dac_test = [1.01, 2.02, 3.03, 4.04, 5.05, -6.06]
        ts0 = time()
        rs = cf.set_aux_dac(s, dac_test, ds)
        ts1 = time()

        tg0 = time()
        rg = cf.get_aux_dac(s, ds)
        tg1 = time()

        if rs == dac_test:
            print(cg + f"{i}/{n} Set aux DAC               PASS ({int(1E6*(ts1-ts0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Input:  {dac_test}" + ce)
                print(cg + f"       Output: {rs}" + ce)
        else:
            print(cr + f"{i}/{n} Set aux DAC               FAIL")
            print(f"Input:  {dac_test}")
            print(f"Output: {rs}" + ce)
        i += 1

        if rg == dac_test:
            print(cg + f"{i}/{n} Get aux DAC               PASS ({int(1E6*(tg1-tg0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Expected: {dac_test}" + ce)
                print(cg + f"       Received: {rg}" + ce)
        else:
            print(cr + f"{i}/{n} Get aux DAC               FAIL")
            print(f"Expected: {dac_test}")
            print(f"Received: {rg}" + ce)
        i += 1


        # ==== Set / Get params_VB ====
        pVB = [[110.0, 1.0], [120.0, False], [3.0, 1337.0]]
        pVB_1D = pVB[0] + pVB[1] + pVB[2]

        ts0 = time()
        rs = cf.set_params_VB(s, *pVB_1D, ds)
        ts1 = time()

        tg0 = time()
        rg = cf.get_params_VB(s, ds)
        tg1 = time()

        if rs == 1:
            print(cg + f"{i}/{n} Set params_VB             PASS ({int(1E6*(ts1-ts0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Input:  {dac_test}" + ce)
                print(cg + f"       Output: {rs}" + ce)
        else:
            print(cr + f"{i}/{n} Set params_VB             FAIL" + ce)
            print(cr + f"Output: {rs}" + ce)
        i += 1

        if rg[1][1] is not None and rg[2] == [3.0, 1337.0]:
            print(cg + f"{i}/{n} Get params_VB             PASS ({int(1E6*(tg1-tg0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Expected: {pVB}" + ce)
                print(cg + f"       Received: {rg}" + ce)
        else:
            print(cr + f"{i}/{n} Get params_VB             FAIL")
            print(cr + f"       Expected: {pVB}" + ce)
            print(cr + f"       Received: {rg}" + ce)
        i += 1


        # ==== Get / set serveropt_spoof_Bm ====
        ts0 = time()
        rs0 = cf.set_serveropt_spoof_Bm(s, True, ds)    # Set to True
        ts1 = time()

        tg0 = time()
        rg0 = cf.get_serveropt_spoof_Bm(s, ds)          # Should get True
        tg1 = time()

        Bm_0 = cf.get_Bm(s, ds)[1]                      # Observe Bm before mutation
        sleep(2*1/server_config["threaded_read_ADC_rate"])  # Wait to mutate
        Bm_1 = cf.get_Bm(s, ds)[1]                      # Observe Bm before mutation
        diff = (Bm_0 != Bm_1)                           # Success if different

        rs1 = cf.set_serveropt_spoof_Bm(s, False, ds)   # Set to False
        rg1 = cf.get_serveropt_spoof_Bm(s, ds)          # Should get False

        Bm_2 = cf.get_Bm(s, ds)[1]                      # Observe Bm before mutation
        sleep(2*1/server_config["threaded_read_ADC_rate"])  # Wait to mutate
        Bm_3 = cf.get_Bm(s, ds)[1]                      # Observe Bm before mutation
        same = (Bm_2 == Bm_3)                           # Success if identical

        if rg0 is True and rg1 is False:
            print(cg + f"{i}/{n} Get serveropt_spoof_Bm    PASS ({int(1E6*(tg1-tg0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Get serveropt_spoof_Bm    FAIL")
            print(f"True:  {rg0}")
            print(f"False: {rg1}" + ce)
        i += 1

        if rs0 == 1 and rs1 == 0 and rg0 is True and rg1 is False and \
                diff is True and same is True:
            print(cg + f"{i}/{n} Set serveropt_spoof_Bm    PASS ({int(1E6*(ts1-ts0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} set serveropt_spoof_Bm    FAIL")
            print(f"True:  {rs0}")
            print(f"False: {rs1}" + ce)
        i += 1

        if diff is True and same is True:
            print(cg + f"{i}/{n} Bm spoofing and mutate()  PASS ({int(1E6*(ts1-ts0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       mutate() ON (before):  {Bm_0}")
                print(cg + f"                    (after):  {Bm_1}")
                print(cg + f"       mutate() OFF (before): {Bm_2}")
                print(cg + f"                     (after): {Bm_3}")
        else:
            print(cr + f"{i}/{n} Bm spoofing and mutate()  FAIL" + ce)
            print(cr + f"mutate() ON (before):  {Bm_0}" + ce)
            print(cr + f"             (after):  {Bm_1}" + ce)
            print(cr + f"mutate() OFF (before): {Bm_2}" + ce)
            print(cr + f"              (after): {Bm_3}" + ce)
        i += 1



        # ==== SCHEDULE HANDLING ====
        test_schedule_name = "test_schedule_name"
        test_schedule_name_alt = "test_schedule_name_alt"
        test_schedule = [
            [0, 8, 1.0,   0.0,  0.1,  -0.2],
            [1, 8, 3.0,  10.0, 10.1, -10.2],
            [2, 8, 5.0,  20.0, 20.1, -20.2],
            [3, 8, 7.0,  30.0, 30.1, -30.2],
            [4, 8, 9.0,  40.0, 40.1, -40.2],
            [5, 8, 10.0, 50.0, 50.1, -50.2],
            [6, 8, 12.0, 60.0, 60.1, -60.2],
            [7, 8, 13.0, 70.0, 70.1, -70.2],
        ]
        n_seg = len(test_schedule)
        duration = test_schedule[2][-1]

        ri0 = cf.initialize_schedule(s, ds)  # Clear schedule

        t0 = time()
        r = cf.allocate_schedule(
            s,
            test_schedule_name,         # Schedule name
            n_seg,                      # Schedule number of segments
            duration,                   # Schedule duration
            ds
        )
        t1 = time()

        t0si = time()
        si_name, si_len, si_dur, si_hash = cf.get_schedule_info(
            s, generate_hash=False, datastream=ds
        )
        t1si = time()


        # ==== Get schedule info ====
        if si_name == test_schedule_name and si_len == n_seg \
                and si_dur == duration and si_hash == "":
            print(cg + f"{i}/{n} Get schedule info (-hash) PASS ({int(1E6*(t1si-t0si))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Schedule name:     {si_name}" + ce)
                print(cg + f"       Schedule length:   {si_len}" + ce)
                print(cg + f"       Schedule duration: {si_dur}" + ce)
                print(cg + f"       Schedule hash:     {si_hash}" + ce)
        else:
            print(cr + f"{i}/{n} Get schedule info (-hash) FAIL" + ce)
            print(cr + f"Schedule name:     {si_name}" + ce)
            print(cr + f"Schedule length:   {si_len}" + ce)
            print(cr + f"Schedule duration: {si_dur}" + ce)
            print(cr + f"Schedule hash:     {si_hash}" + ce)
        i += 1


        # ==== Allocate schedule ====
        if isinstance(r, int) and r == 1:
            print(cg + f"{i}/{n} Allocate schedule         PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Allocate schedule         FAIL" + ce)
            print(cr + f"return: {r}" + ce)
        i += 1


        # ==== Set / Get schedule segment ====
        t0s = time()
        rs = cf.set_schedule_segment(s, test_schedule[-1], ds)
        t1s = time()

        t0g = time()
        rg = cf.get_schedule_segment(s, test_schedule[-1][0], ds)
        t1g = time()

        if isinstance(rs, int) and rs == test_schedule[-1][0] \
                and rg == test_schedule[-1]:
            print(cg + f"{i}/{n} Set schedule segment      PASS ({int(1E6*(t1s-t0s))} \u03bcs)" + ce)
            if details:
                print(cg + f"       return: {rs}" + ce)
                print(cg + f"       Segment sent:     {test_schedule[-1]}" + ce)
                print(cg + f"       Segment received: {rg}" + ce)
        else:
            print(cr + f"{i}/{n} Set schedule segment      FAIL" + ce)
            print(cr + f"return: {rs}" + ce)
            print(cr + f"Segment sent:     {test_schedule[-1]}" + ce)
            print(cr + f"Segment received: {rg}" + ce)
        i += 1

        if rg == test_schedule[-1]:
            print(cg + f"{i}/{n} Get schedule segment      PASS ({int(1E6*(t1g-t0g))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Segment sent:     {test_schedule[-1]}" + ce)
                print(cg + f"       Segment received: {rg}" + ce)
        else:
            print(cr + f"{i}/{n} Get schedule segment      FAIL" + ce)
            print(cr + f"Segment sent:     {test_schedule[-1]}" + ce)
            print(cr + f"Segment received: {rg}" + ce)
        i += 1


        # ==== Transfer schedule ====
        t0 = time()
        r = cf.transfer_schedule(
            s, test_schedule, name=test_schedule_name_alt, datastream=ds
        )
        t1 = time()

        si_name, si_len, si_dur, _ = cf.get_schedule_info(
            s, generate_hash=False, datastream=ds
        )

        if r == 1 and si_name == test_schedule_name_alt \
            and si_len == len(test_schedule) \
            and si_dur == test_schedule[-1][2]:
            print(cg + f"{i}/{n} Transfer schedule         PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Confirm:           {r}" + ce)
                print(cg + f"       Schedule name:     {si_name}" + ce)
                print(cg + f"       Schedule length:   {si_len}" + ce)
                print(cg + f"       Schedule duration: {si_dur}" + ce)
        else:
            print(cr + f"{i}/{n} Transfer schedule         FAIL" + ce)
            print(cr + f"Confirm:           {r}" + ce)
            print(cr + f"Schedule name:     {si_name}" + ce)
            print(cr + f"Schedule length:   {si_len}" + ce)
            print(cr + f"Schedule duration: {si_dur}" + ce)
        i += 1


        # ==== Get schedule hash ====
        t0 = time()
        hash_r = cf.get_schedule_hash(s, ds)
        t1 = time()

        if isinstance(hash_r, str) and len(hash_r) == 16:
            print(cg + f"{i}/{n} Get schedule hash         PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Remote hash: {hash_r}" + ce)
        else:
            print(cr + f"{i}/{n} Get schedule hash         FAIL" + ce)
            print(cr + f"Remote hash: {hash_r}" + ce)
        i += 1


        # ==== Calculate local schedule hash ====
        t0 = time()
        hash_l = cf.calculate_schedule_hash(test_schedule)
        t1 = time()

        if isinstance(hash_l, str) and len(hash_l) == 16:
            print(cg + f"{i}/{n} Calculate local hash      PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Local hash:  {hash_l}" + ce)
        else:
            print(cr + f"{i}/{n} Calculate local hash      FAIL" + ce)
            print(cr + f"Remote hash: {hash_l}" + ce)
        i += 1


        # ==== Verify schedule by hash comparison ====
        t0 = time()
        verify, hash_l, hash_r = cf.verify_schedule(s, test_schedule, ds)
        t1 = time()

        if verify and hash_l == hash_r:
            print(cg + f"{i}/{n} Verify schedule           PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       Local hash:  " + cc + f"{hash_l}" + ce)
                print(cg + f"       Remote hash: " + cc + f"{hash_r}" + ce)
                print(cg + f"       Verified:    {verify}" + ce)
        else:
            print(cr + f"{i}/{n} Verify schedule           FAIL" + ce)
            print(cr + f"Local hash:  " + cc + f"{hash_l}" + ce)
            print(cr + f"Remote hash: " + cc + f"{hash_r}" + ce)
            print(cr + f"Verified:    {verify}" + ce)
        i += 1


        # ==== Print schedule info ====
        t0 = time()
        r = cf.print_schedule_info(s, datastream=ds)
        t1 = time()

        if isinstance(r, int) and r == 1:
            print(cg + f"{i}/{n} Print schedule info       PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
        else:
            print(cr + f"{i}/{n} Print schedule info       FAIL" + ce)
            print(cr + f"confirm: {r}" + ce)
        i += 1

        # ==== Initialize schedule ====
        t0 = time()
        r = cf.initialize_schedule(s, ds)
        t1 = time()
        si_name, si_len, si_dur, si_hash = cf.get_schedule_info(
            s, generate_hash=True, datastream=ds
        )
        hash_l = cf.calculate_schedule_hash([[0, 0, 0., 0., 0., 0.], ])

        if isinstance(r, int) and r == 1 \
                and si_name == "init" and si_len == 1 and si_dur == 0.0 \
                and si_hash == hash_l:
            print(cg + f"{i}/{n} Initialize schedule       PASS ({int(1E6*(t1-t0))} \u03bcs)" + ce)
            if details:
                print(cg + f"       return: {r}" + ce)
                print(cg + f"       Schedule name:     {si_name}" + ce)
                print(cg + f"       Schedule length:   {si_len}" + ce)
                print(cg + f"       Schedule duration: {si_dur}" + ce)
                print(cg + f"       Schedule hash:     {si_hash}" + ce)
                print(cg + f"       Local hash:        " + cc + f"{hash_l}" + ce)
        else:
            print(cr + f"{i}/{n} Initialize schedule       FAIL" + ce)
            print(cr + f"return: {r}" + ce)
            print(cr + f"Schedule name:     {si_name}" + ce)
            print(cr + f"Schedule length:   {si_len}" + ce)
            print(cr + f"Schedule duration: {si_dur}" + ce)
            print(cr + f"Schedule hash:     {si_hash}" + ce)
            print(cr + f"Local hash:        " + cc + f"{hash_l}" + ce)
        i += 1

        cf.initialize_schedule(s, ds)






        print("\n ======================== \n")

        # ==== Uptimes
        print(f"Socket uptime {round(cf.get_socket_info(s)[0], 3)} s")
        print(f"Server uptime {round(cf.get_server_uptime(s), 3)} s")
        print(""); sleep(1)


        # Shutting down connection from client side
        print("Terminating...")
        # s.shutdown(1)
        s.close()
        print("Connection terminated.")

        sys.exit(0)