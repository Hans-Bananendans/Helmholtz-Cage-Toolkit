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

from helmholtz_cage_toolkit import *

from helmholtz_cage_toolkit.schedule_player import SchedulePlayer, PlayerControls
from helmholtz_cage_toolkit.utilities import tB_to_schedule
# from helmholtz_cage_toolkit.hhcplot import HHCPlot, HHCPlotArrow
from helmholtz_cage_toolkit.generator_cyclics import (
    generator_cyclics_single,
    generator_cyclics,
    cyclics_generation_parameters,
    interpolation_parameters,
    interpolate,
)


class CyclicsWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.config = config
        self.datapool = datapool

        layout0 = QGridLayout()


        group_cyclics_input = CyclicsInput(self.datapool)
        group_cyclics_visualizer = VisualizerCyclics(self.datapool)
        group_cyclics_input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        group_cyclics_visualizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout0.addWidget(group_cyclics_input, 0, 0)
        layout0.addWidget(group_cyclics_visualizer, 0, 1)
        self.setLayout(layout0)


class CyclicsInput(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Generation Parameters")
        self.datapool = datapool
        self.datapool.cyclics_input = self

        self.setStyleSheet(self.datapool.config["stylesheet_groupbox_smallmargins"])

        self.setMinimumWidth(560)

        self.ui_elements = {
            "duration": {
                "group": "common",
                "pos": (1, 1),
                "label": QLabel("Duration [s]:"),
                "duration": QLineEdit(),
            },
            "resolution": {
                "group": "common",
                "pos": (1, 4),
                "label": QLabel("Resolution [S/s]:"),
                "resolution": QLineEdit(),
            },
            # "predelay": {
            #     "group": "common",
            #     "pos": (2, 1),
            #     "label": QLabel("Predelay [s]:"),
            #     "predelay": QLineEdit(),
            # },
            # "postdelay": {
            #     "group": "common",
            #     "pos": (2, 4),
            #     "label": QLabel("Postdelay [s]:"),
            #     "postdelay": QLineEdit(),
            # },
            "labels": {
                "group": "xyz",
                "pos": (1, 0),
                "alignment": Qt.AlignCenter,
                "label": QLabel(),
                "labelX": QLabel("X"),
                "labelY": QLabel("Y"),
                "labelZ": QLabel("Z"),
            },
            "fbase": {
                "group": "xyz",
                "pos": (2, 0),
                "cb_items": ["constant", "linear", "sine", "sawtooth", "triangle", "square"],
                "label": QLabel("Base function:"),
                "fbaseX": QComboBox(),
                "fbaseY": QComboBox(),
                "fbaseZ": QComboBox(),
            },
            "amplitude": {
                "group": "xyz",
                "pos": (3, 0),
                "label": QLabel("Amp. [\u03bcT]:"),
                "amplitudeX": QLineEdit(),
                "amplitudeY": QLineEdit(),
                "amplitudeZ": QLineEdit(),
            },
            "frequency": {
                "group": "xyz",
                "pos": (4, 0),
                "label": QLabel("Frequency [Hz]:"),
                "frequencyX": QLineEdit(),
                "frequencyY": QLineEdit(),
                "frequencyZ": QLineEdit(),
            },
            "phase": {
                "group": "xyz",
                "pos": (5, 0),
                "label": QLabel("Phase [-\u03c0 rad]:"),
                "phaseX": QLineEdit(),
                "phaseY": QLineEdit(),
                "phaseZ": QLineEdit(),
            },
            "offset": {
                "group": "xyz",
                "pos": (6, 0),
                "label": QLabel("Offset [\u03bcT]:"),
                "offsetX": QLineEdit(),
                "offsetY": QLineEdit(),
                "offsetZ": QLineEdit(),
            },
            "fbase_noise": {
                "group": "xyz",
                "pos": (7, 0),
                "cb_items": ["gaussian", "uniform"],
                "label": QLabel("Noise function:"),
                "fbase_noiseX": QComboBox(),
                "fbase_noiseY": QComboBox(),
                "fbase_noiseZ": QComboBox(),
            },
            "noise_factor": {
                "group": "xyz",
                "pos": (8, 0),
                "label": QLabel("Factor:"),
                "noise_factorX": QLineEdit(),
                "noise_factorY": QLineEdit(),
                "noise_factorZ": QLineEdit(),
            },
        }

        self.interpolation_ui_elements = {
            "cb_items": ["none", "linear"],  # TODO: Expand with cubic, spline, etc.
            "label_function": QLabel("Function:"),
            "function": QComboBox(),
            "label_factor": QLabel("Factor:"),
            "factor": QLineEdit(),
        }

        # Make two layouts for the generation parameters
        self.layout_common_grid = QGridLayout()
        self.layout_xyz_grid = QGridLayout()

        # Make a layout for the interpolation parameters
        self.layout_interpolation = QHBoxLayout()

        # Call functions to populate these layouts
        self.populate_cyclics()
        self.populate_interpolation_parameters()

        # Get the default values for both sets
        defaults_cyclics = self.datapool.config["cyclics_default_generation_parameters"]
        defaults_interpolation = self.datapool.config["default_interpolation_parameters"]

        # Deposit the default values onto the fields
        self.deposit_cyclics(defaults_cyclics)
        self.deposit_interpolation_parameters(defaults_interpolation)

        # Create a button to trigger self.generate()
        button_generate = QPushButton("Generate!")
        button_generate.clicked.connect(self.generate)

        # Groupbox for common generation parameters
        group_common = QGroupBox()
        group_common.setLayout(self.layout_common_grid)
        group_common.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        # Groupbox for XYZ specific generation parameters
        group_xyz = QGroupBox()
        group_xyz.setLayout(self.layout_xyz_grid)
        group_xyz.setStyleSheet(
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
        layout0.addWidget(group_xyz)
        layout0.addWidget(group_interpolation)
        layout0.addWidget(button_generate)

        self.setLayout(layout0)

    def populate_cyclics(self):
        """Populates the UI with input widgets for cyclics generation
        parameters.
        """
        # print("[DEBUG] populate_cyclics()")
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

                elif elements["group"] == "xyz":
                    if key == "label":
                        self.layout_xyz_grid.addWidget(val, i, 1)

                    if "X" in key:
                        self.layout_xyz_grid.addWidget(val, i, 2)
                    elif "Y" in key:
                        self.layout_xyz_grid.addWidget(val, i, 3)
                    elif "Z" in key:
                        self.layout_xyz_grid.addWidget(val, i, 4)

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


    def slurp_cyclics(self):
        """Automatically visits the user-editable widgets in the user
        interface and slurps their values into a dict.
        """
        print("[DEBUG] slurp_cyclics()")

        # Load defaults as template (to overwrite next)
        inputs = cyclics_generation_parameters

        # First fill inputs with generation parameters already in datapool:
        for key, val in self.datapool.generation_parameters_cyclics.items():
            inputs[key] = val

        # Now overwrite everything with the values in the input widgets:
        for prop, elements in self.ui_elements.items():
            for key, val in elements.items():
                if type(val) == QLineEdit:
                    if key in inputs.keys() and val.text() != "":
                        if key in ("duration", "resolution"):
                            inputs[key] = int(float(val.text()))
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


    def deposit_cyclics(self, contents):
        """Does the opposite of slurp_cyclics(); deposits values from
        datapool.generation_parameters_cyclics onto the user-editable widgets.
        """
        # print("[DEBUG] populate_cyclics()")
        if contents == {}:
            contents = self.datapool.config["cyclics_default_generation_parameters"]

        for prop, elements in self.ui_elements.items():
            for key, val in elements.items():
                if type(val) == QLineEdit:
                    val.setPlaceholderText(str(contents[key]))
                elif type(val) == QComboBox:
                    val.setCurrentIndex(elements["cb_items"].index(contents[key]))


    def deposit_interpolation_parameters(self, contents):
        """Deposits values from datapool.interpolation_parameters onto the
        user-editable widgets.
        """
        # print("[DEBUG] deposit_interpolation_parameters()")
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
        """Invokes the Cyclics Generator
        1. Slurp values
        2. Assemble generation_parameters
        3. Shove into generator_cyclics(), get (t, B)
        4. Slurp interpolation_parameters
        4. Do interpolation()
        6. Flood to datapool.schedule, datapool.generation_parameters
        7. Schedule changed -> self.datapool.refresh()
        """
        # print("[DEBUG] generate()")
        generation_parameters = self.slurp_cyclics()
        t, B = generator_cyclics(generation_parameters)

        interpolation_parameters = self.slurp_interpolation_parameters()

        t, B = interpolate(t,
                           B,
                           interpolation_parameters["factor"],
                           interpolation_parameters["function"])

        self.datapool.schedule = tB_to_schedule(t, B)
        self.datapool.generation_parameters_cyclics = generation_parameters
        self.datapool.interpolation_parameters = interpolation_parameters

        self.datapool.refresh(source="cyclics")


class VisualizerCyclics(QGroupBox):
    def __init__(self, datapool) -> None:
        # super().__init__("Visualizations")
        super().__init__()

        # Import datapool reference
        self.datapool = datapool
        # Place reference to self into datapool for reference
        self.datapool.cyclics_visualizer = self

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


        # Define envelope plot
        self.widget_envelopeplot = EnvelopePlot(self.datapool)

        # Define HHC plots
        self.hhcplot_yz = HHCPlot(direction="YZ")
        self.hhcplot_mxy = HHCPlot(direction="mXY")

        # Plot path ghosts on HHC plots
        self.plot_ghosts()


        # Put HHC Plots and relevant labels in their own layout
        layout_hhcplot = QGridLayout()
        layout_hhcplot.addWidget(QLabel("Front view (YZ)"), 0, 0)
        layout_hhcplot.addWidget(self.hhcplot_yz, 1, 0)

        layout_hhcplot.addWidget(QLabel("Top view (-XY)"), 0, 1)
        layout_hhcplot.addWidget(self.hhcplot_mxy, 1, 1)


        # Define subclassed SchedulePlayer object (does not have a UI)
        self.scheduleplayer = SchedulePlayerCyclics(
            self.hhcplot_mxy, self.hhcplot_yz, self.widget_envelopeplot,
            self.bscale, self.datapool)
        # Pass reference to datapool for reference
        self.datapool.cyclics_scheduleplayer = self.scheduleplayer
        # Set playback multiplier
        self.mult = 1

        # Create PlayerControl widget
        self.group_playcontrols = PlayerControls(
            self.datapool, self.scheduleplayer
        )


        # Make main layout
        layout0 = QVBoxLayout()

        layout0.addWidget(self.widget_envelopeplot)
        layout0.addWidget(self.group_playcontrols)
        layout0.addLayout(layout_hhcplot)

        self.setLayout(layout0)


    def refresh(self):
        """When the schedule, or other parameters relevant to the
        VisualizerCyclics item are changed, it is important to call an update
        to every aspect that has to be updated, such as timers, plots, etc.

        This refresh() function is a one-stop shop for all required updates
        relevant to VisualizerCyclics.

        """
        # First clear data previously plotted:
        # XYZ lines in envelope plot
        for item in self.widget_envelopeplot.plot_obj.dataItems:
            item.clear()
        # Ghosts in HHC plots:
        for item in [self.hhcplot_yz.plot_obj.dataItems[-1],
                     self.hhcplot_mxy.plot_obj.dataItems[-1]]:
            item.clear()

        # Refresh envelope plot
        self.widget_envelopeplot.generate_envelope_plot()

        # Refresh path ghosts on HHC plots
        self.plot_ghosts()

        # Refresh play controls
        self.scheduleplayer.init_values()
        self.group_playcontrols.refresh()

    def plot_ghosts(self):
        """Plots hazy, dotted paths indicating the magnetic field vector
        movement during the schedule.
        """
        ghost_pen = pg.mkPen((0, 255, 255, 64), width=1, style=Qt.DotLine)

        self.hhcplot_mxy.plot_obj.plot(
            self.datapool.schedule[4]/self.bscale,      # Y
            -self.datapool.schedule[3]/self.bscale,     # -X
            pen=ghost_pen
        )
        self.hhcplot_yz.plot_obj.plot(
            self.datapool.schedule[4]/self.bscale,          # Y
            self.datapool.schedule[5]/self.bscale,          # Z
            pen=ghost_pen
        )


class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self, direction="YZ"):
        super().__init__()

        self.direction = direction

        self.plot_obj = self.addPlot(row=0, col=0, antialias=True)
        self.resize(360, 360)
        self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot_obj.showGrid(x=True, y=True)
        # self.plot_obj.setData(antialias=True)
        self.plot_obj.showAxis("bottom", True)
        self.plot_obj.showAxis("left", True)
        self.plot_obj.getAxis("bottom").setStyle(showValues=False)
        self.plot_obj.getAxis("left").setStyle(showValues=False)

        if direction == "YZ":
            self.plot_hhc_elements_yz()
        elif direction == "XY":
            self.plot_hhc_elements_xy()
        elif direction == "mXY":
            self.plot_hhc_elements_mxy()
        else:
            raise ValueError("Parameter 'direction' must be 'XY' or 'YZ'!")

        self.arrow_pen = pg.mkPen("c", width=3)
        self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.arrow_tail.setPen(self.arrow_pen)

        self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)

        self.plot_obj.addItem(self.arrow_tail)
        self.plot_obj.addItem(self.arrow_tip)


    def plot_hhc_elements_mxy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1, -1-ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95, 0.75, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(coils[i])


        walls = (
            QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
            QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
        )
        for wall in walls:
            wall.setPen(pg.mkPen("#FFF6"))
            wall.setBrush(pg.mkBrush("#FFF1"))
            self.plot_obj.addItem(wall)


        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )
        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)

    def plot_hhc_elements_xy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(coils[i])

        # walls = (
        #     QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
        #     QGraphicsRectItem(QRectF(-1.0, -1.0, 0.05, 2 * 1.0)),
        # )
        # for wall in walls:
        #     wall.setPen(pg.mkPen("#FFF6"))
        #     wall.setBrush(pg.mkBrush("#FFF1"))
        #     self.plot_obj.addItem(wall)

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )
        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)

    def plot_hhc_elements_yz(self):
        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#0F0F", "#22FF", "#F00F")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(coils[i])

        walls = (
            QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
        )
        for wall in walls:
            wall.setPen(pg.mkPen("#FFF6"))
            wall.setBrush(pg.mkBrush("#FFF1"))
            self.plot_obj.addItem(wall)

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.05, 2 * 0.25, 1 * 0.05)),
            QGraphicsRectItem(QRectF(-0.15, -1, 0.05, 0.95)),
            QGraphicsRectItem(QRectF(0.1, -1, 0.05, 0.95)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)


class EnvelopePlot(pg.GraphicsLayoutWidget):
    def __init__(self, datapool):
        super().__init__()

        self.datapool = datapool
        self.datapool.cyclics_plot = self

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-9)

        self.vline = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen("c", width=2),)
        self.vline.setZValue(10)
        self.plot_obj.addItem(self.vline, ignoreBounds=True)

        self.generate_envelope_plot()

    # @staticmethod
    # def detect_predelay(x):
    #     if 0.99 * (x[1] - x[0]) > x[3] - x[2] and abs(x[2] - x[1]) < 1E-6:
    #         return x[1] - x[0]
    #     else:
    #         return 0.0
    #
    # @staticmethod
    # def detect_postdelay(x):
    #     if 0.99 * (x[-1] - x[-2]) > x[-4] - x[-3] and abs(x[-2] - x[-3]) < 1E-6:
    #         return x[-1] - x[-2]
    #     else:
    #         return 0.0


    def generate_envelope_plot(self, show_actual=True, show_points=False):

        t = self.datapool.schedule[2]
        B = array([self.datapool.schedule[3],
                   self.datapool.schedule[4],
                   self.datapool.schedule[5]])

        colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]

        # TODO: Predelay and postdelay were unexposed in GUI as of 27-01-2024
        #  as its limited value was not worth the substantial complication of
        #  the code implementation. Delete the following commented code after
        #  QA testing.
        # # Detect predelay and postdelay, for more accurate staggered plots
        # # Detection algorithms are not guaranteed to catch predelays
        # predelay = False
        # postdelay = False
        # push = [0, -1]
        #
        # try:
        #     if self.detect_predelay(t) > 0.0:
        #         predelay = True
        #         push[0] = 2
        # except:  # noqa  # TODO Replace this system with lookup of gen parameters
        #     pass
        # try:
        #     if self.detect_postdelay(t) > 0.0:
        #         postdelay = True
        #         push[1] = -2
        # except:  # noqa  # TODO Replace this system with lookup of gen parameters
        #     pass

        # # Correct staggered plots in case of predelay and postdelay
        # predelay = False
        # postdelay = False
        # push = [0, -1]
        #
        # if self.datapool.generation_parameters_cyclics["predelay"] > 0.0:
        #     predelay = True
        #     push[0] = 2
        # if self.datapool.generation_parameters_cyclics["postdelay"] > 0.0:
        #     postdelay = True
        #     push[1] = -2

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
                        repeat(B[1, push[0]:push[1]], 2)[:-1],
                        repeat(B[2, push[0]:push[1]], 2)[:-1])
                       )

        for i in range(3):
            if show_actual:
                # Staggered line
                self.plot_obj.plot(t_stag, B_stag[i], pen=colours[i])
                # # Line patches for predelay
                # if predelay:
                #     self.plot_obj.plot([t[0], t[1], t_stag[0]],
                #                        [B[i, 0], B[i, 1], B_stag[i, 0]],
                #                        pen=colours[i])
                # # Line patches for postdelay
                # if postdelay:
                #     self.plot_obj.plot([t_stag[-1], t[-2], t[-1]],
                #                        [B_stag[i, -1], B[i, -2], B[i, -1]],
                #                        pen=colours[i])
            else:
                self.plot_obj.plot(t, B[i], pen=colours[i])

            if show_points:
                self.plot_obj.plot(t, B[i],
                                   pen=(0, 0, 0, 0),
                                   symbolBrush=(0, 0, 0, 0),
                                   symbolPen=colours[i],
                                   symbol="o",
                                   symbolSize=6)

        # plot_main.plot(t_interp, y_interp,
        #                pen=(255, 0, 0, 0),
        #                symbolBrush=(0, 0, 0, 0),
        #                symbolPen=(255, 120, 120, 200),
        #                symbol="o",
        #                symbolSize=6)


class SchedulePlayerCyclics(SchedulePlayer):
    def __init__(self, hhcplot_xy, hhcplot_yz, widget_envelopeplot, bscale,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External variables: self.datapool.get_schedule_steps()
        self.hhcplot_xy = hhcplot_xy
        self.hhcplot_yz = hhcplot_yz
        self.widget_envelopeplot = widget_envelopeplot
        self.bscale = bscale

    def update(self):
        # t0 = time()  # [TIMING] ~4 us
        bx = self.datapool.schedule[3][self.step]
        by = self.datapool.schedule[4][self.step]
        bz = self.datapool.schedule[5][self.step]

        tail_clip = 0.9

        # t1 = time()  # [TIMING] 32 us
        self.hhcplot_xy.arrow_tail.setLine(
            0., 0., tail_clip * by / self.bscale, -tail_clip * bx / self.bscale
        )
        # t2 = time()  # [TIMING] 11 us
        self.hhcplot_xy.arrow_tip.setPos(by / self.bscale, -bx / self.bscale)
        # t3 = time()  # [TIMING] ~300 us
        self.hhcplot_xy.arrow_tip.setStyle(
            angle=self.hhcplot_xy.arrow_tail.line().angle() - 180
        )

        # t4 = time()  # [TIMING]
        self.hhcplot_yz.arrow_tail.setLine(
            0., 0., tail_clip * by / self.bscale, tail_clip * bz / self.bscale)
        self.hhcplot_yz.arrow_tip.setPos(by / self.bscale, bz / self.bscale)
        self.hhcplot_yz.arrow_tip.setStyle(
            angle=self.hhcplot_yz.arrow_tail.line().angle() - 180
        )

        # t5 = time()  # [TIMING] ~210 us

        self.widget_envelopeplot.vline.setPos(self.t)

        # t6 = time()  # [TIMING] total ~700 us

        # print(f"[TIMING]", end=" ")
        # print(f"{round((t1-t0)*1E6)} us", end=" ")
        # print(f"{round((t2-t1)*1E6)} us", end=" ")
        # print(f"{round((t3-t2)*1E6)} us", end=" ")
        # print(f"{round((t4-t3)*1E6)} us", end=" ")
        # print(f"{round((t5-t4)*1E6)} us", end=" ")
        # print(f"{round((t6-t5)*1E6)} us", end=" ")
        # print(f"T: {round((t6-t0)*1E6)} us")


