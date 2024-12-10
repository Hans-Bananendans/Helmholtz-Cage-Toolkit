"""
Group hierarchy:

parent
├── CyclicsInput
│   ├── group_common
│   ├── group_xyz
│   ├── group_interpolate
│   └── button_generate
│
└── VisualizerCyclics
    ├── SchedulePlayerCyclics (non-UI)
    ├── EnvelopePlot
    ├── PlayControls
    ├── HHCPlot (YZ)
    └── HHCPlot (-XY)

"""

from time import time
import numpy as np # TODO REMOVE

from helmholtz_cage_toolkit import *

from helmholtz_cage_toolkit.schedule_player import SchedulePlayer, PlayerControls
from helmholtz_cage_toolkit.utilities import tB_to_schedule
from helmholtz_cage_toolkit.generator_cyclics import (
    # generator_cyclics_single,
    # generator_cyclics,
    # cyclics_generation_parameters,
    interpolation_parameters,
    interpolate,
)
from helmholtz_cage_toolkit.generator_orbital import (
    generator_orbital2,
    orbital_generation_parameters,
)
from helmholtz_cage_toolkit.orbital_plot import OrbitalPlot, OrbitalPlotButtons
from helmholtz_cage_toolkit.cage3dplot import Cage3DPlot, Cage3DPlotButtons


class OrbitalWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.config = config
        self.datapool = datapool

        layout0 = QGridLayout()


        group_orbital_input = OrbitalInput(self.datapool)
        # group_orbital_plottabs = QTabWidget()
        group_orbital_visualizer = OrbitalVisualizer(self.datapool)
        # group_orbital_cage3d = QLabel("Cage3D")
        #
        # group_orbital_plottabs.addTab(group_orbital_visualizer, "Orbit plot")
        # group_orbital_plottabs.addTab(group_orbital_cage3d, "Cage plot")

        group_orbital_input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        group_orbital_visualizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        group_orbital_input.setMaximumWidth(360)

        layout0.addWidget(group_orbital_input, 0, 0)
        # layout0.addWidget(group_orbital_plottabs, 0, 1) #TODO remove
        layout0.addWidget(group_orbital_visualizer, 0, 1)
        self.setLayout(layout0)


class OrbitalInput(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Generation Parameters")
        self.datapool = datapool
        self.datapool.orbital_input = self

        self.setStyleSheet(self.datapool.config["stylesheet_groupbox_smallmargins"])

        self.setMinimumWidth(300)

        self.ui_elements = {
            "n_step": {
                "group": "common",
                "pos": (1, 1),
                "label": QLabel("Simulation points [-]:"),
                "n_step": QLineEdit(),
            },
            "n_orbit_subs": {
                "group": "common",
                "pos": (2, 1),
                "label": QLabel("Points per orbit [-]:"),
                "n_orbit_subs": QLineEdit(),
            },
            "time_speed_factor": {
                "group": "common",
                "pos": (3, 1),
                "label": QLabel("Time speed factor [-]:"),
                "time_speed_factor": QLineEdit(),
            },
            "date0": {
                "group": "common",
                "pos": (4, 1),
                "label": QLabel("Date at t0 [base10 date]:"),
                "date0": QLineEdit(),
            },
            "earth_zero_datum": {
                "group": "common",
                "pos": (5, 1),
                "label": QLabel("Earth datum at t0 [\u00b0]:"),
                "earth_zero_datum": QLineEdit(),
            },


            "orbit_eccentricity": {
                "group": "elements",
                "pos": (1, 1),
                "label": QLabel("e [-]:"),
                "orbit_eccentricity": QLineEdit(),
            },
            "orbit_RAAN": {
                "group": "elements",
                "pos": (1, 4),
                "label": QLabel("\u03a9 [\u00b0]:"),
                "orbit_RAAN": QLineEdit(),
            },
            "orbit_pericentre_altitude": {
                "group": "elements",
                "pos": (2, 1),
                "label": QLabel("h_p [km]:"),
                "orbit_pericentre_altitude": QLineEdit(),
            },
            "orbit_argp": {
                "group": "elements",
                "pos": (2, 4),
                "label": QLabel("\u03c9 [\u00b0]:"),
                "orbit_argp": QLineEdit(),
            },
            "orbit_inclination": {
                "group": "elements",
                "pos": (3, 1),
                "label": QLabel("i [\u00b0]:"),
                "orbit_inclination": QLineEdit(),
            },
            "orbit_ma0": {
                "group": "elements",
                "pos": (3, 4),
                "label": QLabel("M0 [\u00b0]:"),
                "orbit_ma0": QLineEdit(),
            },

            "angle_body_x_0": {
                "group": "body",
                "pos": (1, 1),
                "label": QLabel("\u03c6 [\u00b0]:"),
                "angle_body_x_0": QLineEdit(),
            },
            "rate_body_x": {
                "group": "body",
                "pos": (1, 4),
                "label": QLabel("d\u03c6/dt [\u00b0/s]:"),
                "rate_body_x": QLineEdit(),
            },
            "angle_body_y_0": {
                "group": "body",
                "pos": (2, 1),
                "label": QLabel("\u03b8 [\u00b0]:"),
                "angle_body_y_0": QLineEdit(),
            },
            "rate_body_y": {
                "group": "body",
                "pos": (2, 4),
                "label": QLabel("d\u03b8/dt [\u00b0/s]:"),
                "rate_body_y": QLineEdit(),
            },
            "angle_body_z_0": {
                "group": "body",
                "pos": (3, 1),
                "label": QLabel("\u03c8 [\u00b0]:"),
                "angle_body_z_0": QLineEdit(),
            },
            "rate_body_z": {
                "group": "body",
                "pos": (3, 4),
                "label": QLabel("d\u03c8/dt [\u00b0/s]:"),
                "rate_body_z": QLineEdit(),
            },
        }

        self.interpolation_ui_elements = {
            "cb_items": ["none", "linear", "spline"],
            "label_function": QLabel("Function:"),
            "function": QComboBox(),
            "label_factor": QLabel("Factor:"),
            "factor": QLineEdit(),
        }

        # Make layouts for the generation parameters
        self.layout_common_grid = QGridLayout()
        self.layout_elements_grid = QGridLayout()
        self.layout_body_grid = QGridLayout()

        # Make a layout for the interpolation parameters
        self.layout_interpolation = QHBoxLayout()

        # Call functions to populate these layouts
        self.populate_orbital()
        self.populate_interpolation_parameters()

        # Get the default values for both sets
        defaults_orbital = self.datapool.config["orbital_default_generation_parameters"]
        defaults_interpolation = self.datapool.config["default_interpolation_parameters"]

        # Deposit the default values onto the fields
        self.deposit_orbital(defaults_orbital)  # TODO
        self.deposit_interpolation_parameters(defaults_interpolation)

        # Create a button to trigger self.generate()
        button_generate = QPushButton("Generate!")
        button_generate.clicked.connect(self.generate) # TODO

        # Groupbox for common generation parameters
        group_common = QGroupBox()
        group_common.setLayout(self.layout_common_grid)
        group_common.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        # Groupbox for orbital elements
        group_elements = QGroupBox("Orbital elements")
        group_elements.setLayout(self.layout_elements_grid)
        group_elements.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        # Groupbox for body motion parameters
        group_body = QGroupBox("Body motion")
        group_body.setLayout(self.layout_body_grid)
        group_body.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        # Groupbox for interpolation parameters
        group_interpolation = QGroupBox("Interpolation")
        group_interpolation.setLayout(self.layout_interpolation)
        group_interpolation.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins"]
        )


        # Create and configure main layout
        layout0 = QVBoxLayout()

        layout0.addWidget(group_common)
        layout0.addWidget(group_elements)
        layout0.addWidget(group_body)
        layout0.addWidget(group_interpolation)
        layout0.addWidget(button_generate)

        self.setLayout(layout0)

    def populate_orbital(self):
        """Populates the UI with input widgets for orbital generation
        parameters.
        """
        print("[DEBUG] deposit_orbital()")
        for prop, elements in self.ui_elements.items():
            for key, val in elements.items():
                i, j = elements["pos"]

                # print("key:", key, type(key))
                # print("prop:", prop, type(prop))

                if elements["group"] == "common":
                    if key == "label":
                        self.layout_common_grid.addWidget(val, i, j)
                    if key == prop:
                        self.layout_common_grid.addWidget(val, i, j+1)

                if elements["group"] == "elements":
                    if key == "label":
                        self.layout_elements_grid.addWidget(val, i, j)
                    if key == prop:
                        self.layout_elements_grid.addWidget(val, i, j+1)

                if elements["group"] == "body":
                    if key == "label":
                        self.layout_body_grid.addWidget(val, i, j)
                    if key == prop:
                        self.layout_body_grid.addWidget(val, i, j+1)

                # elif elements["group"] == "xyz":
                #     if key == "label":
                #         self.layout_xyz_grid.addWidget(val, i, 1)
                #
                #     if "X" in key:
                #         self.layout_xyz_grid.addWidget(val, i, 2)
                #     elif "Y" in key:
                #         self.layout_xyz_grid.addWidget(val, i, 3)
                #     elif "Z" in key:
                #         self.layout_xyz_grid.addWidget(val, i, 4)

                if type(val) == QLineEdit:
                    val.setAlignment(Qt.AlignCenter)
                elif type(val) == QComboBox:
                    if val.count() == 0:
                        val.addItems(elements["cb_items"])
                        val.setMinimumWidth(128)  # TODO: Dirty fix, improve in future
                elif type(val) == QLabel:
                    if "alignment" in elements:
                        val.setAlignment(elements["alignment"])

    def populate_interpolation_parameters(self):
        """Populates the UI with input widgets for interpolation parameters.
        """
        # print("[DEBUG] populate_interpolation_parameters()")

        for key, val in self.interpolation_ui_elements.items():
            if type(val) == QLabel:
                self.layout_interpolation.addWidget(val)
            elif type(val) == QLineEdit:
                self.layout_interpolation.addWidget(val)
            elif type(val) == QComboBox:
                if val.count() == 0:
                    val.addItems(self.interpolation_ui_elements["cb_items"])
                    val.setMinimumWidth(128)  # TODO: Dirty fix, improve in future
                self.layout_interpolation.addWidget(val)


    def slurp_orbital(self):
        """Automatically visits the user-editable widgets in the user
        interface and slurps their values into a dict.
        """
        print("[DEBUG] slurp_orbital()")

        # Load defaults as template (to overwrite next)
        inputs = self.datapool.config["orbital_default_generation_parameters"]

        # First fill inputs with generation parameters already in datapool:
        for key, val in self.datapool.generation_parameters_orbital.items():
            inputs[key] = val

        # Now overwrite everything with the values in the input widgets:
        for prop, elements in self.ui_elements.items():
            for key, val in elements.items():
                if type(val) == QLineEdit:
                    if key in inputs.keys() and val.text() != "":
                        if key in ("n_step", "n_orbit_subs"):
                            inputs[key] = int(float(val.text()))
                        elif key in ("orbit_pericentre_altitude",):
                            inputs[key] = int(float(val.text()) * 1000)
                        else:
                            inputs[key] = float(val.text())
                elif type(val) == QComboBox:
                    if key in inputs.keys():
                        inputs[key] = val.currentText()
                    # print(prop, key, val.currentText())

        # for key, val in inputs.items():
        #     print(f"{key}: {val} ({type(val)})")  # [DEBUG]

        return inputs

    def slurp_interpolation_parameters(self):
        """Automatically visits the user-editable widgets in the user
        interface and slurps their values into a dict.
        """

        print("[DEBUG] slurp_interpolation_parameters()")
        # Load defaults as template
        inputs = interpolation_parameters

        # First fill inputs with generation parameters already in datapool:
        for key, val in self.datapool.interpolation_parameters.items():
            inputs[key] = val

        # Now overwrite everything with the values in the input widgets:
        for key, val in self.interpolation_ui_elements.items():
            if type(val) == QLineEdit:
                if key in inputs.keys() and val.text() != "":
                    if key in ("factor",):
                        inputs[key] = int(float(val.text()))
                    else:
                        inputs[key] = float(val.text())
            elif type(val) == QComboBox:
                if key in inputs.keys():
                    inputs[key] = val.currentText()

        # for key, val in inputs.items():
        #     print(f"{key}: {val} ({type(val)})")  # [DEBUG]

        return inputs


    def deposit_orbital(self, contents):
        """Does the opposite of slurp_orbital(); deposits values from
        datapool.generation_parameters_orbital onto the user-editable widgets.
        """
        print("[DEBUG] deposit_orbital()")
        if contents == {}:
            contents = self.datapool.config["orbital_default_generation_parameters"]

        for prop, elements in self.ui_elements.items():
            for key, val in elements.items():
                if type(val) == QLineEdit:
                    if key in ("orbit_pericentre_altitude",):
                        val.setPlaceholderText(str(contents[key]/1000)) # Convert [m] to [km]
                    else:
                        val.setPlaceholderText(str(contents[key]))
                elif type(val) == QComboBox:
                    val.setCurrentIndex(elements["cb_items"].index(contents[key]))


    def deposit_interpolation_parameters(self, contents):
        """Deposits values from datapool.interpolation_parameters onto the
        user-editable widgets.
        """
        print("[DEBUG] deposit_interpolation_parameters()")
        if contents == {}:
            contents = self.datapool.config["default_interpolation_parameters"]


        for key, val in self.interpolation_ui_elements.items():
            if type(val) == QLineEdit:
                val.setPlaceholderText(str(contents[key]))
            elif type(val) == QComboBox:
                val.setCurrentIndex(
                    self.interpolation_ui_elements["cb_items"].index(contents[key])
                )


    # @Slot()
    def generate(self):
        """Invokes the Orbital Generator
        1. slurp values
        2. Assemble generation_parameters
        3. Shove into generator_orbital(), get (t, B)
        4. Slurp interpolation_parameters
        4. Do interpolation()
        6. Flood to datapool.schedule, datapool.generation_parameters
        7. Schedule changed -> self.datapool.refresh()
        """
        print("[DEBUG] orbital.generate()")
        t_start = time()

        self.datapool.status_bar.showMessage("Generating orbit...")

        generation_parameters = self.slurp_orbital()
        t, B = generator_orbital2(generation_parameters, self.datapool)

        interpolation_parameters = self.slurp_interpolation_parameters()

        t, B = interpolate(t,
                           B,
                           interpolation_parameters["factor"],
                           interpolation_parameters["function"])

        self.datapool.schedule = tB_to_schedule(t, B)
        self.datapool.generation_parameters_orbital = generation_parameters
        self.datapool.interpolation_parameters = interpolation_parameters

        # print("[DEBUG] orbital.generate() HERE!")
        self.datapool.refresh(source="orbital")

        self.datapool.status_bar.showMessage(
            f"Generated orbit successfully in {round(time()-t_start, 3)} s"
        )


class OrbitalVisualizer(QGroupBox):
    def __init__(self, datapool) -> None:
        # super().__init__("Visualizations")
        super().__init__()

        # Import datapool reference
        self.datapool = datapool
        # Place reference to self into datapool for reference
        self.datapool.orbital_visualizer = self

        # self.show_plot_visibility_tabs = \
        #     self.datapool.config["show_plot_visibility_tabs"]

        # Apply stylesheet for smaller margins
        self.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        # Apply stylesheet for smaller margin
        windowsize = (self.datapool.config["visualizer_windowsize"][0],
                      self.datapool.config["visualizer_windowsize"][1])
        self.setMinimumSize(QSize(windowsize[0], windowsize[1]))

        # Fetch preconfigured bscale, which plotting functions will use
        self.bscale = self.datapool.config["visualizer_bscale"]


        self.layout_orbitalplot = QHBoxLayout()

        # Define orbital plot
        self.widget_orbitalplot = OrbitalPlot(self.datapool)
        self.widget_orbitalplot.draw_statics()

        # TODO REMOVE DEBUG
        genparams = self.datapool.config["orbital_default_generation_parameters"]
        generator_orbital2(genparams, datapool)
        # self.datapool.simdata = generator_orbital2(genparams, datapool)

        # # Writes B_B to a file in np.array format
        # f = open("b_dump.txt", "w")
        # f.write("")
        # f.close()
        # f = open("b_dump.txt", "a")
        # f.write("B = np.array([")
        # for line in range(self.datapool.simdata["n_step"]):
        #     f.write("[")
        #     f.write(str(round(self.datapool.simdata["B_B"][line, 0])))
        #     f.write(",")
        #     f.write(str(round(self.datapool.simdata["B_B"][line, 1])))
        #     f.write(",")
        #     f.write(str(round(self.datapool.simdata["B_B"][line, 2])))
        #     f.write("],")
        #     f.write("\n")
        # f.write("])")
        # f.close()
        # print("Done!")

        self.widget_orbitalplot.draw_simdata()

        self.widget_orbitalplot_buttons = OrbitalPlotButtons(self.widget_orbitalplot, datapool)

        self.layout_orbitalplot.addWidget(self.widget_orbitalplot)
        self.layout_orbitalplot.addWidget(self.widget_orbitalplot_buttons)

        # Cage3D Plot
        self.layout_cage3d = QHBoxLayout()

        self.widget_cage3d = Cage3DPlot(datapool)
        self.widget_cage3d.draw_statics()
        self.widget_cage3d.draw_simdata()

        self.widget_cage3d_buttons = Cage3DPlotButtons(self.widget_cage3d, datapool)


        self.layout_cage3d.addWidget(self.widget_cage3d)
        self.layout_cage3d.addWidget(self.widget_cage3d_buttons)
        # Set visibility once, then let datapool.toggle_plot_visibility_tabs()
        # handle it henceforth
        if self.datapool.config["show_plot_visibility_tabs"] is False:
            self.widget_orbitalplot_buttons.setVisible(False)
            self.widget_cage3d_buttons.setVisible(False)

        # self.widget_cage3d_buttons.set

        self.group_orbitalplot = QGroupBox()
        self.group_orbitalplot.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_hidden"]
        )
        self.group_orbitalplot.setLayout(self.layout_orbitalplot)

        self.group_cage3d = QGroupBox()
        self.group_cage3d.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_hidden"]
        )
        self.group_cage3d.setLayout(self.layout_cage3d)



        # Define subclassed SchedulePlayer object (does not have a UI)
        self.scheduleplayer = SchedulePlayerOrbital(
            self.widget_orbitalplot, self.widget_cage3d, self.datapool)
        # Pass reference to datapool for reference
        self.datapool.orbital_scheduleplayer = self.scheduleplayer
        # Set playback multiplier
        self.mult = 1

        # Create PlayerControl widget
        self.group_playcontrols = PlayerControls(
            self.datapool, self.scheduleplayer
        )


        # self.group_playcontrols = QLabel("SCHEDULE PLAYER CONTROLS HERE")
        self.group_playcontrols.setMaximumHeight(48)


        self.plottabs = QTabWidget()
        self.plottabs.addTab(self.group_orbitalplot, "Orbit plot")
        self.plottabs.addTab(self.group_cage3d, "Cage plot")


        # Make main layout
        layout0 = QVBoxLayout()

        layout0.addWidget(self.plottabs)
        layout0.addWidget(self.group_playcontrols)
        # layout0.addLayout(layout_hhcplot)

        self.setLayout(layout0)

        # Timer
        self.i_step = 0
        self.autorotate_timer = QTimer()
        self.autorotate_timer.timeout.connect(self.autorotate)
        self.autorotate_timer.start(50)

    # def update_plots(self):
    #     self.update_orbital_plot()
    #     self.update_cage3d_plot()
    #     self.i_step = (self.i_step + 1) % len(self.datapool.simdata["i_step"])

    # def update_orbital_plot(self, timing=False):
    #     # print(f"[NEW] [{self.i_step}] B={self.datapool.simdata['B_ECI'][self.i_step].round()} |B|={round(np.linalg.norm(self.datapool.simdata['B_ECI'][self.i_step]))}")
    #     if timing:
    #         t0 = time()
    #     self.widget_orbitalplot.draw_step(self.i_step)
    #     if timing:
    #         t = round((time()-t0)*1000, 3)
    #         print(f"update_orbital_plot(): i_step {self.i_step} - time: {t} ms")
    #
    # def update_cage3d_plot(self, timing=False):
    #     # print(f"[NEW] [{self.i_step}] B={self.datapool.simdata['B_ECI'][self.i_step].round()} |B|={round(np.linalg.norm(self.datapool.simdata['B_ECI'][self.i_step]))}")
    #     if timing:
    #         t0 = time()
    #     self.widget_cage3d.draw_step(self.i_step)
    #     # self.i_step = (self.i_step + 1) % len(self.datapool.simdata["i_step"])
    #     if timing:
    #         t = round((time()-t0)*1000, 3)
    #         print(f"update_cage3d_plot(): i_step {self.i_step} - time: {t} ms")

    def refresh(self):
        """When the schedule, or other parameters relevant to the
        VisualizerCyclics item are changed, it is important to call an update
        to every aspect that has to be updated, such as timers, plots, etc.

        This refresh() function is a one-stop shop for all required updates
        relevant to OrbitalVisualizer.

        """
        # First clear data previously plotted:
        # XYZ lines in envelope plot
        self.widget_orbitalplot.clear()
        self.widget_orbitalplot.draw_statics()
        self.widget_orbitalplot.draw_simdata()

        self.widget_cage3d.clear()
        self.widget_cage3d.draw_statics()
        self.widget_cage3d.draw_simdata()

        # Refresh play controls
        self.scheduleplayer.init_values()
        self.group_playcontrols.refresh()

    def autorotate(self):

        if self.datapool.config["ov_draw"]["autorotate"]:
            angle = self.datapool.config["ov_autorotate_angle"]
            self.widget_orbitalplot.setCameraPosition(
                azimuth=(self.widget_orbitalplot.opts["azimuth"] + angle) % 360
            )
        if self.datapool.config["c3d_draw"]["autorotate"]:
            angle = self.datapool.config["c3d_autorotate_angle"]
            self.widget_cage3d.setCameraPosition(
                azimuth=(self.widget_cage3d.opts["azimuth"] + angle) % 360
            )


    # def plot_ghosts(self):
    #     """Plots hazy, dotted paths indicating the magnetic field vector
    #     movement during the schedule.
    #     """
    #     ghost_pen = pg.mkPen((0, 255, 255, 64), width=1, style=Qt.DotLine)
    #
    #     self.hhcplot_mxy.plot_obj.plot(
    #         self.datapool.schedule[4]/self.bscale,      # Y
    #         -self.datapool.schedule[3]/self.bscale,     # -X
    #         pen=ghost_pen
    #     )
    #     self.hhcplot_yz.plot_obj.plot(
    #         self.datapool.schedule[4]/self.bscale,          # Y
    #         self.datapool.schedule[5]/self.bscale,          # Z
    #         pen=ghost_pen
    #     )


# class HHCPlot(pg.GraphicsLayoutWidget):
#     def __init__(self, direction="YZ"):
#         super().__init__()
#
#         self.direction = direction
#
#         self.plot_obj = self.addPlot(row=0, col=0, antialias=True)
#         self.resize(360, 360)
#         self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
#         self.plot_obj.showGrid(x=True, y=True)
#         # self.plot_obj.setData(antialias=True)
#         self.plot_obj.showAxis("bottom", True)
#         self.plot_obj.showAxis("left", True)
#         self.plot_obj.getAxis("bottom").setStyle(showValues=False)
#         self.plot_obj.getAxis("left").setStyle(showValues=False)
#
#         if direction == "YZ":
#             self.plot_hhc_elements_yz()
#         elif direction == "XY":
#             self.plot_hhc_elements_xy()
#         elif direction == "mXY":
#             self.plot_hhc_elements_mxy()
#         else:
#             raise ValueError("Parameter 'direction' must be 'XY' or 'YZ'!")
#
#         self.arrow_pen = pg.mkPen("c", width=3)
#         self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
#         self.arrow_tail.setPen(self.arrow_pen)
#
#         self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)
#
#         self.plot_obj.addItem(self.arrow_tail)
#         self.plot_obj.addItem(self.arrow_tip)
#
#
#     def plot_hhc_elements_mxy(self):
#
#         ts = 0.15
#         tripod = (
#             QGraphicsLineItem(QLineF(-1, -1, -1, -1-ts)),
#             QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
#             QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
#         )
#         for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
#             tripod[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(tripod[i])
#
#         coils = (
#             QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
#             QGraphicsRectItem(QRectF(-0.95, 0.75, 2 * 0.95, 0.05)),
#             QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
#             QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
#         )
#         for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
#             coils[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(coils[i])
#
#
#         walls = (
#             QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
#             QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
#         )
#         for wall in walls:
#             wall.setPen(pg.mkPen("#FFF6"))
#             wall.setBrush(pg.mkBrush("#FFF1"))
#             self.plot_obj.addItem(wall)
#
#
#         table = (
#             QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
#         )
#         for item in table:
#             item.setPen(pg.mkPen("#FFF6"))
#             self.plot_obj.addItem(item)
#
#     def plot_hhc_elements_xy(self):
#
#         ts = 0.15
#         tripod = (
#             QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
#             QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
#             QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
#         )
#         for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
#             tripod[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(tripod[i])
#
#         coils = (
#             QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
#             QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
#             QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
#             QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
#         )
#         for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
#             coils[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(coils[i])
#
#         # walls = (
#         #     QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
#         #     QGraphicsRectItem(QRectF(-1.0, -1.0, 0.05, 2 * 1.0)),
#         # )
#         # for wall in walls:
#         #     wall.setPen(pg.mkPen("#FFF6"))
#         #     wall.setBrush(pg.mkBrush("#FFF1"))
#         #     self.plot_obj.addItem(wall)
#
#         table = (
#             QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
#         )
#         for item in table:
#             item.setPen(pg.mkPen("#FFF6"))
#             self.plot_obj.addItem(item)
#
#     def plot_hhc_elements_yz(self):
#         ts = 0.15
#         tripod = (
#             QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
#             QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
#             QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
#         )
#         for i, c in enumerate(("#0F0F", "#22FF", "#F00F")):
#             tripod[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(tripod[i])
#
#         coils = (
#             QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
#             QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
#             QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
#             QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
#             QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
#         )
#         for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
#             coils[i].setPen(pg.mkPen(c))
#             self.plot_obj.addItem(coils[i])
#
#         walls = (
#             QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
#         )
#         for wall in walls:
#             wall.setPen(pg.mkPen("#FFF6"))
#             wall.setBrush(pg.mkBrush("#FFF1"))
#             self.plot_obj.addItem(wall)
#
#         table = (
#             QGraphicsRectItem(QRectF(-0.25, -0.05, 2 * 0.25, 1 * 0.05)),
#             QGraphicsRectItem(QRectF(-0.15, -1, 0.05, 0.95)),
#             QGraphicsRectItem(QRectF(0.1, -1, 0.05, 0.95)),
#         )
#
#         for item in table:
#             item.setPen(pg.mkPen("#FFF6"))
#             self.plot_obj.addItem(item)
#

# class EnvelopePlot(pg.GraphicsLayoutWidget):
#     def __init__(self, datapool):
#         super().__init__()
#
#         self.datapool = datapool
#         self.datapool.cyclics_plot = self
#
#         self.plot_obj = self.addPlot(row=0, col=0)
#         self.resize(720, 360)
#         self.plot_obj.showGrid(x=True, y=True)
#         self.plot_obj.showAxis('bottom', True)
#         self.plot_obj.showAxis('left', True)
#         self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
#         self.plot_obj.getAxis("left").setLabel(text="B", units="T")
#         self.plot_obj.getAxis("left").setScale(scale=1E-9)
#
#         self.vline = pg.InfiniteLine(angle=90, movable=False,
#                                      pen=pg.mkPen("c", width=2),)
#         self.vline.setZValue(10)
#         self.plot_obj.addItem(self.vline, ignoreBounds=True)
#
#         self.generate_envelope_plot()
#
#     # @staticmethod
#     # def detect_predelay(x):
#     #     if 0.99 * (x[1] - x[0]) > x[3] - x[2] and abs(x[2] - x[1]) < 1E-6:
#     #         return x[1] - x[0]
#     #     else:
#     #         return 0.0
#     #
#     # @staticmethod
#     # def detect_postdelay(x):
#     #     if 0.99 * (x[-1] - x[-2]) > x[-4] - x[-3] and abs(x[-2] - x[-3]) < 1E-6:
#     #         return x[-1] - x[-2]
#     #     else:
#     #         return 0.0
#
#
#     def generate_envelope_plot(self, show_actual=True, show_points=False):
#
#         t = self.datapool.schedule[2]
#         B = array([self.datapool.schedule[3],
#                    self.datapool.schedule[4],
#                    self.datapool.schedule[5]])
#
#         colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]
#
#         # TODO: Predelay and postdelay were unexposed in GUI as of 27-01-2024
#         #  as its limited value was not worth the substantial complication of
#         #  the code implementation. Delete the following commented code after
#         #  QA testing.
#         # # Detect predelay and postdelay, for more accurate staggered plots
#         # # Detection algorithms are not guaranteed to catch predelays
#         # predelay = False
#         # postdelay = False
#         # push = [0, -1]
#         #
#         # try:
#         #     if self.detect_predelay(t) > 0.0:
#         #         predelay = True
#         #         push[0] = 2
#         # except:  # noqa  # TODO Replace this system with lookup of gen parameters
#         #     pass
#         # try:
#         #     if self.detect_postdelay(t) > 0.0:
#         #         postdelay = True
#         #         push[1] = -2
#         # except:  # noqa  # TODO Replace this system with lookup of gen parameters
#         #     pass
#
#         # # Correct staggered plots in case of predelay and postdelay
#         # predelay = False
#         # postdelay = False
#         # push = [0, -1]
#         #
#         # if self.datapool.generation_parameters_cyclics["predelay"] > 0.0:
#         #     predelay = True
#         #     push[0] = 2
#         # if self.datapool.generation_parameters_cyclics["postdelay"] > 0.0:
#         #     postdelay = True
#         #     push[1] = -2
#
#         # Generate staggered dataset by copying using repeat and then shifting
#         push = [0, -1]
#         t_stag = repeat(t[push[0]:push[1]], 2)[1:]
#         B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
#                         repeat(B[1, push[0]:push[1]], 2)[:-1],
#                         repeat(B[2, push[0]:push[1]], 2)[:-1])
#                        )
#
#         for i in range(3):
#             if show_actual:
#                 # Staggered line
#                 self.plot_obj.plot(t_stag, B_stag[i], pen=colours[i])
#                 # # Line patches for predelay
#                 # if predelay:
#                 #     self.plot_obj.plot([t[0], t[1], t_stag[0]],
#                 #                        [B[i, 0], B[i, 1], B_stag[i, 0]],
#                 #                        pen=colours[i])
#                 # # Line patches for postdelay
#                 # if postdelay:
#                 #     self.plot_obj.plot([t_stag[-1], t[-2], t[-1]],
#                 #                        [B_stag[i, -1], B[i, -2], B[i, -1]],
#                 #                        pen=colours[i])
#             else:
#                 self.plot_obj.plot(t, B[i], pen=colours[i])
#
#             if show_points:
#                 self.plot_obj.plot(t, B[i],
#                                    pen=(0, 0, 0, 0),
#                                    symbolBrush=(0, 0, 0, 0),
#                                    symbolPen=colours[i],
#                                    symbol="o",
#                                    symbolSize=6)
#
#         # plot_main.plot(t_interp, y_interp,
#         #                pen=(255, 0, 0, 0),
#         #                symbolBrush=(0, 0, 0, 0),
#         #                symbolPen=(255, 120, 120, 200),
#         #                symbol="o",
#         #                symbolSize=6)


# class SchedulePlayerCyclics(SchedulePlayer):
#     def __init__(self, hhcplot_xy, hhcplot_yz, widget_envelopeplot, bscale,
#                  *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # External variables: self.datapool.get_schedule_steps()
#         self.hhcplot_xy = hhcplot_xy
#         self.hhcplot_yz = hhcplot_yz
#         self.widget_envelopeplot = widget_envelopeplot
#         self.bscale = bscale
#
#     def update(self):
#         # t0 = time()  # [TIMING] ~4 us
#         bx = self.datapool.schedule[3][self.step]
#         by = self.datapool.schedule[4][self.step]
#         bz = self.datapool.schedule[5][self.step]
#
#         tail_clip = 0.9
#
#         # t1 = time()  # [TIMING] 32 us
#         self.hhcplot_xy.arrow_tail.setLine(
#             0., 0., tail_clip * by / self.bscale, -tail_clip * bx / self.bscale
#         )
#         # t2 = time()  # [TIMING] 11 us
#         self.hhcplot_xy.arrow_tip.setPos(by / self.bscale, -bx / self.bscale)
#         # t3 = time()  # [TIMING] ~300 us
#         self.hhcplot_xy.arrow_tip.setStyle(
#             angle=self.hhcplot_xy.arrow_tail.line().angle() - 180
#         )
#
#         # t4 = time()  # [TIMING]
#         self.hhcplot_yz.arrow_tail.setLine(
#             0., 0., tail_clip * by / self.bscale, tail_clip * bz / self.bscale)
#         self.hhcplot_yz.arrow_tip.setPos(by / self.bscale, bz / self.bscale)
#         self.hhcplot_yz.arrow_tip.setStyle(
#             angle=self.hhcplot_yz.arrow_tail.line().angle() - 180
#         )
#
#         # t5 = time()  # [TIMING] ~210 us
#
#         self.widget_envelopeplot.vline.setPos(self.t)
#
#         # t6 = time()  # [TIMING] total ~700 us
#
#         # print(f"[TIMING]", end=" ")
#         # print(f"{round((t1-t0)*1E6)} us", end=" ")
#         # print(f"{round((t2-t1)*1E6)} us", end=" ")
#         # print(f"{round((t3-t2)*1E6)} us", end=" ")
#         # print(f"{round((t4-t3)*1E6)} us", end=" ")
#         # print(f"{round((t5-t4)*1E6)} us", end=" ")
#         # print(f"{round((t6-t5)*1E6)} us", end=" ")
#         # print(f"T: {round((t6-t0)*1E6)} us")

#
# class PlayerControls(QGroupBox):
#     """Defines a set of UI elements for playback control. It is linked to an
#     instance to the SchedulePlayer class, which handles the actual playback."""
#     def __init__(self, datapool, scheduleplayer, label_update_interval=30) -> None:
#         super().__init__()
#
#         self.datapool = datapool
#         self.setStyleSheet(
#             self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         )
#
#         self.scheduleplayer = scheduleplayer
#
#         # Speed at which labels will update themselves. Slave the act of
#         # performing the update to a QTimer.
#         self.label_update_interval = label_update_interval
#         self.label_update_timer = QTimer()
#         self.label_update_timer.timeout.connect(self.update_labels)
#
#         # To keep overhead on the update_label() function minimal, already
#         # generate the strings of the total schedule duration and steps
#         self.str_step_prev = 0
#         self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
#         self.str_steps = "/{}".format(self.datapool.get_schedule_steps())
#
#         # Main layout
#         layout0 = QHBoxLayout()
#
#         # Generate and configure playback buttons
#         self.button_play = QPushButton()
#         self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))
#         self.button_play.toggled.connect(self.toggle_play)
#         self.button_play.setCheckable(True)
#
#         self.button_reset = QPushButton()
#         self.button_reset.setIcon(QIcon("./assets/icons/feather/rotate-ccw.svg"))
#         self.button_reset.clicked.connect(self.toggle_reset)
#
#         self.button_mult10 = QPushButton()
#         self.button_mult10.setIcon(QIcon("./assets/icons/x10.svg"))
#         self.button_mult10.toggled.connect(self.toggle_mult10)
#         self.button_mult10.setCheckable(True)
#
#         self.button_mult100 = QPushButton()
#         self.button_mult100.setIcon(QIcon("./assets/icons/x100.svg"))
#         self.button_mult100.toggled.connect(self.toggle_mult100)
#         self.button_mult100.setCheckable(True)
#
#         self.button_mult1000 = QPushButton()
#         self.button_mult1000.setIcon(QIcon("./assets/icons/x1000.svg"))
#         self.button_mult1000.toggled.connect(self.toggle_mult1000)
#         self.button_mult1000.setCheckable(True)
#
#         self.buttons_playback = (
#             self.button_play,
#             self.button_reset,
#         )
#         self.buttons_mult = (
#             self.button_mult10,
#             self.button_mult100,
#             self.button_mult1000,
#         )
#
#         button_size = QSize(32, 32)
#         button_size_icon = QSize(24, 24)
#
#         for button in self.buttons_playback+self.buttons_mult:
#             button.setFixedSize(button_size)
#             button.setIconSize(button_size_icon)
#             layout0.addWidget(button)
#
#
#
#         # Generate and configure playback labels
#         self.label_t = QLabel("0.000/0.000")
#         self.label_t.setMinimumWidth(256)
#         self.label_step = QLabel("0/0")
#
#         self.update_labels()
#
#         for label in (self.label_t, self.label_step):
#             label.setStyleSheet(self.datapool.config["stylesheet_label_timestep"])
#             label.setAlignment(Qt.AlignRight)
#             layout0.addWidget(label)
#
#         self.setLayout(layout0)
#
#
#     def refresh(self):
#         # Stops playback when called
#         self.toggle_reset()
#         self.button_play.setChecked(False)
#
#         self.str_step_prev = 0
#         self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
#         self.str_steps = "/{}".format(self.datapool.get_schedule_steps())
#         self.update_labels(force_refresh=True)
#
#     # def uncheck_buttons(self, buttons_group): # TODO DELETE UNUSED
#     #     for button in buttons_group:
#     #         button.setChecked(False)
#
#     # @Slot()
#     def toggle_play(self):
#         # If user clicked button and playback has to "turn on", start playback
#         # immediately, start the label update timer, and change the icon to
#         # indicate it now functions as pause button.
#         if self.button_play.isChecked():
#             self.scheduleplayer.start()
#             self.label_update_timer.start(self.label_update_interval)
#             self.button_play.setIcon(QIcon("./assets/icons/feather/pause.svg"))
#
#         # If user clicked button and playback has to "pause", stop playback
#         # immediately, stop the label update timer, and change the icon to
#         # indicate it now functions as play button.
#         else:
#             self.scheduleplayer.stop()
#             self.label_update_timer.stop()
#             self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))
#
#     # @Slot()
#     def toggle_reset(self):
#         self.scheduleplayer.reset()
#
#     def set_mult(self, mult):
#         # Sets the march multiplier on the SchedulePlayer
#         self.scheduleplayer.set_march_mult(mult)
#
#     def toggle_mult10(self):
#         # If toggled, uncheck other mult buttons, and set playback to x10
#         if self.button_mult10.isChecked():
#             self.button_mult100.setChecked(False)
#             self.button_mult1000.setChecked(False)
#             self.set_mult(10)
#         else:
#             self.set_mult(1)
#
#     # @Slot()
#     def toggle_mult100(self):
#         # If toggled, uncheck other mult buttons, and set playback to x100
#         if self.button_mult100.isChecked():
#             self.button_mult10.setChecked(False)
#             self.button_mult1000.setChecked(False)
#             self.set_mult(100)
#         else:
#             self.set_mult(1)
#
#     # @Slot()
#     def toggle_mult1000(self):
#         # If toggled, uncheck other mult buttons, and set playback to x1000
#         if self.button_mult1000.isChecked():
#             self.button_mult10.setChecked(False)
#             self.button_mult100.setChecked(False)
#             self.set_mult(1000)
#         else:
#             self.set_mult(1)
#
#     # @Slot()
#     def update_labels(self, force_refresh=False):
#         """ Updates the time and step label.
#
#         Optimizations:
#          - Pre-generate the string with total steps and duration, so they do
#             not have to be calculated in the loop.
#          - Replace the only instance of round with a custom 3-digit round that
#             has ~30 us less overhead.
#          - Save ~10 us of overhead per cycle by not updating steps label when
#             step was not updated internally.
#         Total improvement from ~150 us to ~50 us
#         """
#         # t0 = time()  # [TIMING]
#         self.label_t.setText("{:.3f}".format(
#                 (self.scheduleplayer.t * 2001) // 2 / 1000) + self.str_duration)
#         # t1 = time()  # [TIMING]
#
#         if self.scheduleplayer.step != self.str_step_prev or force_refresh:
#             self.label_step.setText(
#                 str(self.scheduleplayer.step) + self.str_steps
#             )
#             self.str_step_prev = self.scheduleplayer.step
#
#         # t2 = time()  # [TIMING]
#         # print(f"[TIMING] update_labels(): {round((t1-t0)*1E6)} us  {round((t2-t1)*1E6)} us")  # [TIMING]



class SchedulePlayerOrbital(SchedulePlayer):
    def __init__(self, orbitalplot, cage3dplot, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External variables: self.datapool.get_schedule_steps()
        self.orbitalplot = orbitalplot
        self.cage3dplot = cage3dplot


    def update(self):
        # t0 = time()  # [TIMING] ~4 us
        self.orbitalplot.draw_step(self.step)
        self.cage3dplot.draw_step(self.step)
