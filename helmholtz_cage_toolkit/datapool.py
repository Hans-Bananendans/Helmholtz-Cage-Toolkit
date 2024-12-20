import os
from time import time
# from numpy import zeros

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.orbit_visualizer import Orbit, Earth
import helmholtz_cage_toolkit.client_functions as cf
# from file_handling import load_file, save_file, NewFileDialog
import scc.scc4 as codec
from helmholtz_cage_toolkit.server.server_config import server_config

class DataPool:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config


        # Handles for specific UI elements
        self.main_window = None
        self.menu_bar = None
        self.status_bar = None
        self.tab_bar = None
        self.tabcontainer = None
        self.command_window = None

        self.bscale = self.config["visualizer_bscale"]
        self.cyclics_input = None
        self.cyclics_visualizer = None
        self.orbital_input = None
        self.orbital_visualizer = None
        self.cage3d_plot = None

        # self.cyclics_plot = None
        # self.cyclics_scheduleplayer = None
        self.orbital_scheduleplayer = None

        # self.window_title_base = self.config["APPNAME"]
        # self.software_version = self.config["VERSION"]
        self.set_window_title()


        self.socket_tstart = None
        self.socket = None
        self.ds = None

        self.socket_connected = False


        self.t_playstart = 0.


        # Command
        self.play_mode = "manual"

        # Data buffers
        aqs = Aqs(self.config["buffer_size"])

        self.tm = 0.                    # UNIX time of most recent Bm, Im measurement
        self.Bm = [0., 0., 0.]          # B vector measured by hardware
        self.Bc = [0., 0., 0.]          # B vector as commanded by user
        self.Br = [0., 0., 0.]          # Rejected B vector
        self.Bt = [0., 0., 0.]          # Total actuated B vector
        self.Ec = [0., 0., 0.]          # Command error (Br + Bc - Bm)

        self.Be = [0., 0., 0.]          # Local EMF vector

        #
        # self.Ic = [0., 0., 0.]          # Coil current commanded by user (calculated by server)
        self.Im = [0., 0., 0.]          # Coil current as measured by hardware

        self.V_board = 0.               #
        self.V_adc_aux = 0.             #


        self.i_step = 0                 #
        #
        # self.Vc = [0., 0., 0.]          # Power supply voltage as commanded by user
        #
        # self.Vcc = [0., 0., 0.]         # Supply Current Control Voltage [0, 2] VDC
        # self.Vvc = [0., 0., 0.]         # Supply Voltage Control Voltage [0, 2] VDC


        # # Devices TODO DEPRECATED
        # self.interface_board = None
        # self.supplies = [None, None, None]
        # self.magnetometer = None
        #
        # # Measurement TODO DEPRECATED
        # # self.adc_pollrate = self.config["adc_pollrate"]
        # # TODO: Revert to 0. 0. 0.
        # self.B_m = array([0., 1., 0.])   # B measured by magnetometer
        # self.tBm = 0.0                   # Unix acquisition time of latest measurement
        #
        # # Command TODO DEPRECATED
        # self.B_c = array([0., 0., 0.])   # Commanded (=desired) magnetic field
        # self.I_c = array([0., 0., 0.])   # Voltage for voltage control
        # self.V_cc = array([0., 0., 0.])  # Voltage for voltage control
        # self.V_vc = array([0., 0., 0.])  # Voltage for voltage control

        # Schedule
        self.init_schedule()
        self.init_simdata()

        # Orbital parameters
        # TODO: Fix these presets Replace

        self.init_orbit()
        # self.orbit = Orbit(Earth(), 400E3, 0.0, 0, 0, 0, 0)
        self.orbit_subs = self.config["orbital_default_generation_parameters"]["n_orbit_subs"]
        self.orbit_spacing = self.config["orbit_spacing"]
        self.i_satpos = 0 # TODO DEPRECATED

        self.checks = {
            "connection_up":
                {"text": ["Connected to device",
                          "<unimplemented>",
                          "Unconnected to device"],
                 "value": 2,
                 },
            "schedule_ready":
                {"text": ["Schedule ready on device",
                          "<unimplemented>",
                          "No schedule ready on device"],
                 "value": 2,
                 },
            "recording":
                {"text": ["Ready to record data",
                          "Recording not on/armed",
                          "No recording output selected!"],
                 "value": 1,
                 },
            "dummy_check1":
                {"text": ["dummy1 tick",
                          "dummy1 ~",
                          "dummy1 x"],
                 "value": 0,
                 },
            "dummy_check2":
                {"text": ["dummy2 tick",
                          "dummy2 ~",
                          "dummy2 x"],
                 "value": 0,
                 },
            "dummy_check3":
                {"text": ["dummy3 tick",
                          "dummy3 ~",
                          "dummy3 x"],
                 "value": 0,
                 },
        }


        # ==== TIMERS
        self.timer_get_Bm = QTimer()  # TODO STALE
        # self.timer_get_Bm.timeout.connect(self.do_get_Bm)  # TODO STALE
        self.timer_get_telemetry = QTimer()
        self.timer_get_telemetry.timeout.connect(self.do_get_telemetry)



    # def do_get_Bm(self):
    #     t0 = time()
    #     if self.socket.state() != QAbstractSocket.ConnectedState:
    #         t1 = time()
    #         self.tm, *self.Bm = [0.]*4
    #     else:
    #         t1 = time()
    #         self.tm, *self.Bm = cf.get_Bm(self.socket, self.ds)
    #     t2 = time()
    #     print("[TIMING] do_get_Bm():", int(1E6*(t1-t0)), int(1E6*(t2-t1)), "\u03bcs")
    #
    #     self.command_window.do_update_bm_display()

    def do_set_Bc(self, Bc):
        if self.socket_connected:
            cf.set_Bc(self.socket, Bc, self.ds)

        self.Bc = Bc


    def do_set_Br(self, Br):
        print(f"[DEBUG] datapool.do_set_Br({Br})")
        if self.socket_connected:
            cf.set_Br(self.socket, Br, self.ds)

        self.Br = Br


    def do_get_Bm(self):  # TODO STALE
        """Requests the value of Bm from the server, and stores it to self.tm
        and self.Bm

        Upon disconnecting from the server, the socket.disconnected signal
        should disable the timer periodically running this function. However,
        there exists an edge case where the socket connection is already down,
        but this function still fires once, as the timer has not been shut off
        yet.

        For this reason, this function used to first check for the socket state
        by testing
            self.socket.state() == QAbstractSocket.ConnectedState

        This however introduced a ~15 us overhead. It is now implemented using
        a try and blank except, which is not generally good practice, but it
        prevents do_get_Bm from shitting the bed when the aforementioned edge
        case occurs.
        """
        # t0 = time()
        # try:
        #     self.tm, *self.Bm = cf.get_Bm(self.socket, self.ds)
        # except: # noqa
        #     self.tm, *self.Bm = [0.]*4
        # t1 = time()
        # print("[TIMING] do_get_Bm():", int(1E6*(t1-t0)), "\u03bcs")


        t0 = time()  # [TIMING]
        if self.socket_connected:
            t1 = time()
            self.tm, self.Bm = cf.get_Bm(self.socket, self.ds)

        else:
            t1 = time()
            self.tm, self.Bm = 0., [0.]*3

        t2 = time()  # [TIMING]


        # def randomwalkB():
        #     Btest = []
        #     m = 0.2
        #     f = 10_000
        #     Bm_mutated = self.Bm
        #     for i in range(3):
        #         b = self.Bm[i]
        #         # print(b, b/f, 1/2-b/f, -1/2-b/f)
        #         Bm_mutated[i] += (m*(random()-0.5) - 1/(1/2-b/f+0.1) - 1/(-1/2-b/f-0.1))*f
        #     Btest.append(Bm_mutated)
        #     for i in range(3):
        #         Btest.append([0.]*3)
        #     return Btest
        #
        # def randomBtest():
        #     Btest = []
        #     for i in range(2):
        #         Btest.append(list((random(3) * 100_000 - 50_000).round(1)))
        #     for i in range(2):
        #         Btest.append([0.]*3)
        #     return Btest
        #
        # # Btest = [
        # #     [ 40_000,  50_000,       0],
        # #     [ 80_000,  20_000,  10_000],
        # #     [-40_000, -50_000,       0],
        # #     [-80_000, -20_000, -10_000],
        # # ]
        # Btest = randomwalkB()
        #
        # t3 = time()  # [TIMING]
        # self.command_window.do_update_bm_display()
        #
        # self.command_window.hhcplot_xy.update_arrows(Btest)
        # self.command_window.hhcplot_yz.update_arrows(Btest)
        #
        # t4 = time()  # [TIMING]
        # # print("[TIMING] do_get_Bm():",
        # #       int(1E6*(t1-t0)), int(1E6*(t2-t1)), int(1E6*(t3-t2)), int(1E6*(t4-t3)), "\u03bcs")


    def do_get_telemetry(self):
        """Requests telemetry data from the server, and stores the contents of
         the received t-packet to the corresponding values in the datapool.

        Upon disconnecting from the server, the socket.disconnected signal
        should disable the timer periodically running this function. However,
        there exists an edge case where the socket connection is already down,
        but this function still fires once, as the timer has not been shut off
        yet.

        For this reason, this also checks self.socket_connected as a
        low-overhead (<1 us) method to handle this edge case.
        """
        # print("[DEBUG] do_get_telemetry()")
        # t0 = time()
        # try:
        #     self.tm, *self.Bm = cf.get_Bm(self.socket, self.ds)
        # except: # noqa
        #     self.tm, *self.Bm = [0.]*4
        # t1 = time()
        # print("[TIMING] do_get_Bm():", int(1E6*(t1-t0)), "\u03bcs")


        # t0 = time()  # [TIMING]
        if self.socket_connected:
            # t1 = time()  # [TIMING]
            self.tm, self.i_step, self.Im, self.Bm, self.Bc = cf.get_telemetry(
                self.socket, self.ds)
        else:
            # t1 = time()  # [TIMING]
            self.tm = -1.
            [self.Im, self.Bm, self.Bc] = [[-1.]*3]*3

        # t2 = time()  # [TIMING]


        # print("[TIMING] do_get_Bm():",
        #       int(1E6*(t1-t0)), int(1E6*(t2-t1)), "\u03bcs")


    def enable_timer_get_telemetry(self):
        self.timer_get_telemetry.start(
            int(1000 / self.config["telemetry_polling_rate"])
        )

        # self.timer_get_Bm.start(int(1000/self.config["Bm_polling_rate"]))

    def disable_timer_get_telemetry(self):
        self.timer_get_telemetry.stop()
        # self.timer_get_Bm.stop()

    def get_config(self):
        return self.config

    def set_config(self, config):
        self.config = config

    def init_schedule(self):
        self.schedule = zeros((6, 2))
        self.schedule_name = ""
        self.generator = "none"
        self.generation_parameters_cyclics = {}
        self.generation_parameters_orbital = {}
        self.interpolation_parameters = {}

    def init_simdata(self): #TODO UPDATE
        self.simdata = None

    def init_orbit(self):
        odgp = self.config["orbital_default_generation_parameters"]
        self.orbit = Orbit(
            Earth(),
            odgp["orbit_pericentre_altitude"],
            odgp["orbit_eccentricity"],
            odgp["orbit_inclination"],
            odgp["orbit_RAAN"],
            odgp["orbit_argp"],
            odgp["orbit_ma0"],)

    def do_start_playback(self):
        t_before = time()
        cf.set_play(self.socket, True, self.ds)
        t_after = time()
        self.t_playstart = t_before-(t_after-t_before)

    def do_stop_playback(self):
        cf.set_play(self.socket, False, self.ds)

    def refresh(self, source):
        """Refreshes certain key UI elements when the internal schedule and
        generation parameters are changed.
        """
        print("[DEBUG] refresh()")

        if source == "cyclics":
            # Deposit cyclics_input with whatever interpolation_parameters in datapool:
            self.cyclics_input.deposit_interpolation_parameters(self.interpolation_parameters)

            # Deposit cyclics_input with whatever genparams in datapool:
            self.cyclics_input.deposit_cyclics(self.generation_parameters_cyclics)

            # Refresh the plots and play controls in the Cyclics Visualizer:
            self.cyclics_visualizer.refresh()

        if source == "orbital":
            # Deposit cyclics_input with whatever interpolation_parameters in datapool:
            self.orbital_input.deposit_interpolation_parameters(self.interpolation_parameters)

            # Deposit cyclics_input with whatever genparams in datapool:
            self.orbital_input.deposit_orbital(self.generation_parameters_orbital)

            # Refresh the plots and play controls in the Cyclics Visualizer:
            self.orbital_visualizer.refresh()

        self.command_window.on_schedule_refresh()

        # TODO: Add UI elements from Orbital Generator

    def set_serveropts_Bm_manipulation(self, mode: str):
        if self.socket_connected:
            if mode == "none":
                cf.set_serveropt_mutate_Bm(self.socket, False, self.ds)
                cf.set_serveropt_inject_Bm(self.socket, False, self.ds)
            elif mode == "mutate":
                cf.set_serveropt_mutate_Bm(self.socket, True, self.ds)
                cf.set_serveropt_inject_Bm(self.socket, False, self.ds)
            elif mode == "inject":
                cf.set_serveropt_mutate_Bm(self.socket, False, self.ds)
                cf.set_serveropt_inject_Bm(self.socket, True, self.ds)
            else:
                raise ValueError(f"set_serveropts_Bm_manipulation(): Invalid mode '{mode}'!")

            self.status_bar.showMessage(
                f"Setting serveropt 'Bm manip.' to '{mode}'")

        else:
            self.status_bar.showMessage(
                "Could not set serveropts: Not connected to server!"
            )

    def set_adc_channels(self, adc_channels):
        self.adc_channels = adc_channels

    def set_dac_channels(self, dac_channels):
        self.dac_channels = dac_channels

    def get_schedule_duration(self):
        return self.schedule[2][-1]

    def get_schedule_steps(self):
        return len(self.schedule[0])

    def dump(self, data: str):
        if data == "datapool":
            print("\n ==== DATAPOOL DUMP ==== ")
            members = vars(self)
            for key in members.keys():
                if key not in ("config",):
                    print(key, "=", members[key])
        elif data == "config":
            print("\n ==== CONFIG DUMP ==== ")
            for key, val in self.config.items():
                print(key, "=", val)
        elif data == "telemetry":
            print("\n ==== TELEMETRY DUMP ==== ")
            items = (self.tm, self.i_step, self.Im, self.Bm, self.Bc)
            items_str = ("tm", "i_step", "Im", "Bm", "Bc")
            for i, item in enumerate(items):
                print(items_str[i], "=", item)
        elif data == "cyclics_genparams":
            print("\n ==== CYCLICS GENPARAMS DUMP ==== ")
            for key, val in self.generation_parameters_cyclics.items():
                print(key, "=", val)
        elif data == "orbital_genparams":
            print("\n ==== ORBITAL GENPARAMS DUMP ==== ")
            for key, val in self.generation_parameters_orbital.items():
                print(key, "=", val)
        else:
            raise ValueError(f"dump(): Invalid dumping data '{data}'!")

    # # @Slot()
    # def dump_datapool(self):
    #     print("\n ==== DATAPOOL DUMP ==== ")
    #     members = vars(self)
    #     for key in members.keys():
    #         if key not in ("config",):
    #             print(key, "=", members[key])

    # # @Slot()
    # def dump_config(self):
    #     print("\n ==== CONFIG DUMP ==== ")
    #     for key, val in self.config.items():
    #         print(key, "=", val)
    #
    # def dump_generation_parameters_orbital(self):
    #     print("\n ==== ORBITAL GENPARAMS DUMP ==== ")
    #     for key, val in self.generation_parameters_orbital.items():
    #         print(key, "=", val)
    #
    # def dump_generation_parameters_cyclics(self):
    #     print("\n ==== CYCLICS GENPARAMS DUMP ==== ")
    #     for key, val in self.generation_parameters_cyclics.items():
    #         print(key, "=", val)

    def toggle_plot_visibility_tabs(self):
        if self.orbital_visualizer is None:
            pass
        else:
            if self.config["show_plot_visibility_tabs"] is True:
                self.orbital_visualizer.widget_orbitalplot_buttons.setVisible(False)
                self.orbital_visualizer.widget_cage3d_buttons.setVisible(False)
                self.config["show_plot_visibility_tabs"] = False
            else:
                self.orbital_visualizer.widget_orbitalplot_buttons.setVisible(True)
                self.orbital_visualizer.widget_cage3d_buttons.setVisible(True)
                self.config["show_plot_visibility_tabs"] = True

    def set_window_title(self, suffix: str = ""):
        if suffix != "":
            suffix = " - " + suffix.split(os.sep)[-1]
        self.parent.setWindowTitle(
            self.config["APPNAME"] + " " + self.config["VERSION"] + suffix
        )

    # Function not meant for DataPool per se but more for acces by other functions
    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)



class Aqs:
    """
    Buffer class for the data coming from the server device in the form of a
    t-packet.
    """
    def __init__(self, buffer_size):
        # UNIX time of most recent Bm, Im measurement
        self.tm = zeros(buffer_size).tolist()

        # B vector measured by hardware (size: <buffer_size> by 3)
        self.Bm = zeros((buffer_size, 3)).tolist()

        # B vector as commanded by user
        self.Bc = zeros((buffer_size, 3)).tolist()

        # Coil current as measured by hardware
        self.Im = zeros((buffer_size, 3)).tolist()

        # Error between Bc and Bm
        self.E = zeros((buffer_size, 3)).tolist()

        # Index of the schedule step that was commanded
        self.i_step = zeros(buffer_size, int).tolist()

    def input(self, tm, i_step, Im: list, Bm: list, Bc: list):
        self.write_buffer(self.tm, tm) # noqa
        self.write_buffer(self.i_step, i_step) # noqa
        self.write_buffer(self.Im, Im) # noqa
        self.write_buffer(self.Bm, Bm) # noqa
        self.write_buffer(self.Bc, Bc) # noqa

        E_new = [0.0, 0.0, 0.0]
        for i in range(3):
            E_new[i] = Bc[i] - Bm[i]
        self.write_buffer(self.E, E_new) # noqa


    def input_tpacket(self, tpacket):
        tm, i_step, Im, Bm, Bc = codec.decode_tpacket(tpacket)
        self.input(tm, i_step, Im, Bm, Bc)


    def write_buffer(self, buffer, value):
        # Light first-in-last-out pop-and-append function
        buffer.insert(0, value)
        buffer.pop()
        return buffer
