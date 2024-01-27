import os

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.orbit_visualizer import Orbit, Earth
# from file_handling import load_file, save_file, NewFileDialog

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

        self.bscale = self.config["plotwindow_bscale"]
        self.cyclics_visualizer = None
        self.cyclics_input = None

        # self.cyclics_plot = None
        # self.cyclics_scheduleplayer = None

        # self.window_title_base = self.config["APPNAME"]
        # self.software_version = self.config["VERSION"]
        self.set_window_title()

        # Devices
        self.interface_board = None
        self.supplies = [None, None, None]
        self.magnetometer = None

        # Measurement
        self.adc_pollrate = self.config["adc_pollrate"]
        # TODO: Revert to 0. 0. 0.
        self.B_m = array([0., 1., 0.])   # B measured by magnetometer
        self.tBm = 0.0                      # Unix acquisition time of latest measurement

        # Command
        self.B_c = array([0., 0., 0.])   # Commanded (=desired) magnetic field
        self.I_c = array([0., 0., 0.])   # Voltage for voltage control
        self.V_cc = array([0., 0., 0.])  # Voltage for voltage control
        self.V_vc = array([0., 0., 0.])  # Voltage for voltage control

        # Schedule
        self.init_schedule()

        # Orbital parameters
        # TODO: Fix these presets Replace
        self.orbit = Orbit(Earth(), 100E3, 0.2, 60, 120, 0, 0)
        self.orbit_subs = 256
        self.orbit_spacing = "isochronal"
        self.i_satpos = 0

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


    def refresh(self):
        """Refreshes certain key UI elements when the internal schedule and
        generation parameters are changed.
        """
        print("[DEBUG] refresh()")
        # self.set_window_title()  # Reset window title to clear any old filenames

        # Populate cyclics_input with whatever genparams in datapool:
        self.cyclics_input.populate(self.generation_parameters_cyclics)

        # Refresh the plots and play controls in the Cyclics Visualizer:
        self.cyclics_visualizer.refresh()

        # First clear data previously plotted:
        # XYZ lines in envelope plot
        # for item in self.cyclics_visualizer.widget_cyclicsplot.plot_obj.dataItems:
        #     item.clear()
        # Ghosts in HHC plots:
        # for item in [self.cyclics_visualizer.hhcplot_yz.plot_obj.dataItems[-1],
        #              self.cyclics_visualizer.hhcplot_mxy.plot_obj.dataItems[-1]]:
        #     item.clear()
        #
        # self.cyclics_visualizer.widget_cyclicsplot.generate_envelope_plot()
        # self.cyclics_visualizer.plot_ghosts()
        # self.cyclics_visualizer.scheduleplayer.init_values()
        # self.cyclics_visualizer.group_playcontrols.refresh()

        # TODO: Add UI elements from Orbital Generator


    def set_adc_channels(self, adc_channels):
        self.adc_channels = adc_channels

    def set_dac_channels(self, dac_channels):
        self.dac_channels = dac_channels

    def get_schedule_duration(self):
        return self.schedule[2][-1]

    def get_schedule_steps(self):
        return len(self.schedule[0])

    def dump_datapool(self):
        print("\n ==== DATAPOOL DUMP ==== ")
        members = vars(self)
        for key in members.keys():
            if key not in ("config",):
                print(key, "=", members[key])

    def dump_config(self):
        print("\n ==== CONFIG DUMP ==== ")
        for key, val in self.config.items():
            print(key, "=", val)

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


