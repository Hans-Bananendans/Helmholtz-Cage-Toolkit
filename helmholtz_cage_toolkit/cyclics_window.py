import os
from time import time, sleep

from helmholtz_cage_toolkit import *

from helmholtz_cage_toolkit.schedule_player import SchedulePlayer
from helmholtz_cage_toolkit.utilities import tB_to_schedule
from helmholtz_cage_toolkit.generator_cyclics import (
    generator_cyclics_single,
    generator_cyclics,
    cyclics_generation_parameters
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

        self.setMinimumWidth(560)

        # Todo: implement "autoslurping" of input field data based on single
        #  dict with routing information.

        defaults = self.datapool.config["cyclics_default_generation_parameters"]

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
            "predelay": {
                "group": "common",
                "pos": (2, 1),
                "label": QLabel("Predelay [s]:"),
                "predelay": QLineEdit(),
            },
            "postdelay": {
                "group": "common",
                "pos": (2, 4),
                "label": QLabel("Postdelay [s]:"),
                "postdelay": QLineEdit(),
            },
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

        self.layout_xyz_grid = QGridLayout()
        self.layout_common_grid = QGridLayout()

        self.populate(defaults)

        # for prop, elements in self.ui_elements.items():
        #     for key, val in elements.items():
        #         i, j = elements["pos"]
        #
        #         # print("key:", key, type(key))
        #         # print("prop:", prop, type(prop))
        #
        #         if elements["group"] == "common":
        #             if key == "label":
        #                 layout_common_grid.addWidget(val, i, j)
        #             if key == prop:
        #                 layout_common_grid.addWidget(val, i, j+1)
        #
        #         elif elements["group"] == "xyz":
        #             if key == "label":
        #                 layout_xyz_grid.addWidget(val, i, 1)
        #
        #             if "X" in key:
        #                 layout_xyz_grid.addWidget(val, i, 2)
        #             elif "Y" in key:
        #                 layout_xyz_grid.addWidget(val, i, 3)
        #             elif "Z" in key:
        #                 layout_xyz_grid.addWidget(val, i, 4)
        #
        #         if type(val) == QLineEdit:
        #             val.setPlaceholderText(str(defaults[key]))
        #             val.setAlignment(Qt.AlignCenter)
        #         elif type(val) == QComboBox:
        #             val.addItems(elements["cb_items"])
        #             val.setCurrentIndex(elements["cb_items"].index(defaults[key]))
        #         elif type(val) == QLabel:
        #             if "alignment" in elements:
        #                 val.setAlignment(elements["alignment"])



        self.layout_interpolation = QHBoxLayout()

        interpolation_ui_elements = {
            "cb_items": ["NOT YET IMPLEMENTED", "linear", "cubic"],  # TODO: Expand
            "label_function": QLabel("Function:"),
            "fbaseX": QComboBox(),
            "label_factor": QLabel("Factor:"),
            "duration": QLineEdit(),
        }

        for key, val in interpolation_ui_elements.items():
            if type(val) == QLabel:
                self.layout_interpolation.addWidget(val)
            elif type(val) == QLineEdit:
                # val.setPlaceholderText(str(1))
                val.setPlaceholderText("NOT YET IMPLEMENTED")
                self.layout_interpolation.addWidget(val)
            elif type(val) == QComboBox:
                val.addItems(interpolation_ui_elements["cb_items"])
                self.layout_interpolation.addWidget(val)


        button_generate = QPushButton("Generate!")
        button_generate.clicked.connect(self.generate)


        layout0 = QVBoxLayout()

        group_common = QGroupBox()
        group_common.setLayout(self.layout_common_grid)

        group_xyz = QGroupBox()
        group_xyz.setLayout(self.layout_xyz_grid)

        group_interpolation = QGroupBox("Interpolation")
        group_interpolation.setLayout(self.layout_interpolation)

        layout0.addWidget(group_common)
        layout0.addWidget(group_xyz)
        layout0.addWidget(group_interpolation)
        layout0.addWidget(button_generate)

        self.setLayout(layout0)

    def autoslurp(self):
        """Automatically visits the user-editable widgets in the user
        interface and slurps their values into a dict.
        """
        print("[DEBUG] autoslurp()")

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


    def populate(self, contents):
        """Does the opposite of autoslurp(); populates values from
        datapool.generation_parameters_cyclics onto the user-editable widgets.
        """
        print("[DEBUG] populate()")
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
                    val.setPlaceholderText(str(contents[key]))
                    val.setAlignment(Qt.AlignCenter)
                elif type(val) == QComboBox:
                    if val.count() == 0:
                        val.addItems(elements["cb_items"])
                    val.setCurrentIndex(elements["cb_items"].index(contents[key]))
                elif type(val) == QLabel:
                    if "alignment" in elements:
                        val.setAlignment(elements["alignment"])



    def generate(self):
        # 1. Autoslurp values
        # 2. Assemble generation_parameters
        # 3. Shove into generator_cyclics(), get (t, B)
        # 4. Do interpolation (placeholder)
        # 5. Flood to datapool.schedule, datapool.generation_parameters
        # 6. Schedule changed -> self.datapool.refresh()
        print("[DEBUG] generate()")
        generation_parameters = self.autoslurp()
        t, B = generator_cyclics(generation_parameters)

        # TODO: Interpolate()

        self.datapool.schedule = tB_to_schedule(t, B)
        self.datapool.generation_parameters_cyclics = generation_parameters

        self.datapool.refresh()


class VisualizerCyclics(QGroupBox):
    def __init__(self, datapool) -> None:
        # super().__init__("Visualizations")
        super().__init__()
        self.datapool = datapool
        self.datapool.cyclics_visualizer = self

        # windowsize = (self.data.config["plotwindow_windowsize"][0],
        #               self.data.config["plotwindow_windowsize"][1])
        # self.setMinimumSize(QSize(windowsize[0], windowsize[1]))
        # self.setMaximumSize(QSize(windowsize[0], windowsize[1]))
        windowsize = (560, 820)
        self.setMinimumSize(QSize(windowsize[0], windowsize[1]))
        # self.setMaximumSize(QSize(windowsize[0], windowsize[1]))

        layout0 = QVBoxLayout()

        self.widget_cyclicsplot = CyclicsPlot(self.datapool)


        layout_hhcplot = QGridLayout()

        self.bscale = self.datapool.config["plotwindow_bscale"]  # TODO
        # self.bscale = 100_000
        self.hhcplot_yz = HHCPlot(direction="YZ")
        self.hhcplot_mxy = HHCPlot(direction="mXY")


        print(self.hhcplot_yz.plot_obj.dataItems)
        self.plot_ghosts()
        print(self.hhcplot_yz.plot_obj.dataItems)
        # print("THIS", vars(self.hhcplot_yz.plot_obj))

        layout_hhcplot.addWidget(QLabel("Front view (YZ)"), 0, 0)
        layout_hhcplot.addWidget(self.hhcplot_yz, 1, 0)

        layout_hhcplot.addWidget(QLabel("Top view (-XY)"), 0, 1)
        layout_hhcplot.addWidget(self.hhcplot_mxy, 1, 1)
        # layout0.addWidget(QLabel("Layout2dPlots"))


        self.scheduleplayer = SchedulePlayerCyclics(
            self.hhcplot_mxy, self.hhcplot_yz, self.widget_cyclicsplot,
            self.bscale, self.datapool)
        self.datapool.cyclics_scheduleplayer = self.scheduleplayer
        self.mult = 1

        self.group_playcontrols = PlayerControls(
            self.datapool, self.scheduleplayer
        )

        layout0.addWidget(self.widget_cyclicsplot)
        layout0.addWidget(self.group_playcontrols)
        layout0.addLayout(layout_hhcplot)

        self.setLayout(layout0)


    def refresh(self):
        # First clear data previously plotted:
        # XYZ lines in envelope plot
        for item in self.widget_cyclicsplot.plot_obj.dataItems:
            item.clear()
        # Ghosts in HHC plots:
        for item in [self.hhcplot_yz.plot_obj.dataItems[-1],
                     self.hhcplot_mxy.plot_obj.dataItems[-1]]:
            item.clear()

        # Refresh envelope plot
        self.widget_cyclicsplot.generate_envelope_plot()

        # Refresh ghosts on HHC plots
        self.plot_ghosts()

        # Refresh play controls
        self.scheduleplayer.init_values()
        self.group_playcontrols.refresh()

    def plot_ghosts(self):
        ghost_pen = pg.mkPen((0, 255, 255, 64), width=1, style=Qt.DotLine)
        # self.hhcplot_xy.plot_obj.plot(self.data.schedule[3]/self.bscale,  # X
        #                               self.data.schedule[4]/self.bscale,  # Y
        #                               pen=ghost_pen)

        self.hhcplot_mxy.plot_obj.plot(
            self.datapool.schedule[4]/self.bscale,      # X
            -self.datapool.schedule[3]/self.bscale,     # Y
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
        # self.bscale = bscale
        # self.bscale = 10_000_000  # TODO

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

        # self.arrow_length = 100 * 1.28  # Correcting for plot abnormalities

        self.arrow_pen = pg.mkPen("c", width=3)
        self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.arrow_tail.setPen(self.arrow_pen)

        self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)

        self.plot_obj.addItem(self.arrow_tail)
        self.plot_obj.addItem(self.arrow_tip)


        # self.arrow = pg.ArrowItem(angle=0, headLen=20, tailLen=self.arrow_length(), pen=None, brush='y', pxMode=False)
        # self.plot_obj.addItem(self.arrow)
        # self.arrow.setPos(-1, 0)

    # def arrow_length(self, l=1.0):
    #     return 100*1.28*l/self.bscale - 20

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

    # @staticmethod
    # def draw_wall_element(plot_obj, aspect_ratio=0.05, stripes=20, direction="vertical", side="pos"):
    #
    #     pen = pg.mkPen("w", width=2)
    #     length = 2
    #     midpos = [1, 0]
    #
    #     if direction == "vertical":
    #         mainwall = QGraphicsLineItem(QLineF(midpos[0], -length/2, midpos[0], length/2))

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


class CyclicsPlot(pg.GraphicsLayoutWidget):
    def __init__(self, datapool):
        super().__init__()

        self.datapool = datapool
        self.datapool.cyclics_plot = self

        # self.bscale = 10_000_000  # TODO

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        # self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
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


    @staticmethod
    def detect_predelay(x):
        if 0.99 * (x[1] - x[0]) > x[3] - x[2] and abs(x[2] - x[1]) < 1E-6:
            return x[1] - x[0]
        else:
            return 0.0

    @staticmethod
    def detect_postdelay(x):
        if 0.99 * (x[-1] - x[-2]) > x[-4] - x[-3] and abs(x[-2] - x[-3]) < 1E-6:
            return x[-1] - x[-2]
        else:
            return 0.0

    def generate_envelope_plot(self, show_actual=True, show_points=False):

        t = self.datapool.schedule[2]
        B = array([self.datapool.schedule[3],
                   self.datapool.schedule[4],
                   self.datapool.schedule[5]])

        colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]

        # Detect predelay and postdelay, for more accurate staggered plots
        # Detection algorithms are not guaranteed to catch predelays
        predelay = False
        postdelay = False
        push = [0, -1]
        try:
            if self.detect_predelay(t) > 0.0:
                predelay = True
                push[0] = 2
        except:  # noqa  # TODO Replace this system with lookup of gen parameters
            pass
        try:
            if self.detect_postdelay(t) > 0.0:
                postdelay = True
                push[1] = -2
        except:  # noqa  # TODO Replace this system with lookup of gen parameters
            pass

        # Generate dataset by
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
                        repeat(B[1, push[0]:push[1]], 2)[:-1],
                        repeat(B[2, push[0]:push[1]], 2)[:-1])
                       )

        for i in range(3):
            if show_actual:
                # Staggered line
                self.plot_obj.plot(t_stag, B_stag[i], pen=colours[i])
                # Line patches for predelay
                if predelay:
                    self.plot_obj.plot([t[0], t[1], t_stag[0]],
                                       [B[i, 0], B[i, 1], B_stag[i, 0]],
                                       pen=colours[i])
                # Line patches for postdelay
                if postdelay:
                    self.plot_obj.plot([t_stag[-1], t[-2], t[-1]],
                                       [B_stag[i, -1], B[i, -2], B[i, -1]],
                                       pen=colours[i])
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
    def __init__(self, hhcplot_xy, hhcplot_yz, widget_cyclicsplot, bscale,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External variables: self.datapool.get_schedule_steps()
        self.hhcplot_xy = hhcplot_xy
        self.hhcplot_yz = hhcplot_yz
        self.widget_cyclicsplot = widget_cyclicsplot
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

        self.widget_cyclicsplot.vline.setPos(self.t)

        # t6 = time()  # [TIMING] total ~700 us

        # print(f"[TIMING]", end=" ")
        # print(f"{round((t1-t0)*1E6)} us", end=" ")
        # print(f"{round((t2-t1)*1E6)} us", end=" ")
        # print(f"{round((t3-t2)*1E6)} us", end=" ")
        # print(f"{round((t4-t3)*1E6)} us", end=" ")
        # print(f"{round((t5-t4)*1E6)} us", end=" ")
        # print(f"{round((t6-t5)*1E6)} us", end=" ")
        # print(f"T: {round((t6-t0)*1E6)} us")


class PlayerControls(QGroupBox):
    def __init__(self, datapool, scheduleplayer, label_update_interval=25) -> None:
        super().__init__()

        self.datapool = datapool
        self.scheduleplayer = scheduleplayer

        self.label_update_interval = label_update_interval
        self.label_update_timer = QTimer()
        self.label_update_timer.timeout.connect(self.update_labels)

        self.str_step_prev = 0
        self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
        self.str_steps = "/{}".format(self.datapool.get_schedule_steps())

        stylesheet_groupbox_smallmargins = """  
        QGroupBox {
            padding: 0px;
            padding-top: 0px;
        }
        QGroupBox::title {
            padding: 0px;
            height: 0px;
        }
        """
        self.setStyleSheet(stylesheet_groupbox_smallmargins)

        layout0 = QHBoxLayout()

        self.button_play = QPushButton()
        self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))
        self.button_play.toggled.connect(self.toggle_play)
        self.button_play.setCheckable(True)

        self.button_reset = QPushButton()
        self.button_reset.setIcon(QIcon("./assets/icons/feather/rotate-ccw.svg"))
        self.button_reset.clicked.connect(self.toggle_reset)

        self.button_mult10 = QPushButton()
        self.button_mult10.setIcon(QIcon("./assets/icons/x10.svg"))
        self.button_mult10.toggled.connect(self.toggle_mult10)
        self.button_mult10.setCheckable(True)

        self.button_mult100 = QPushButton()
        self.button_mult100.setIcon(QIcon("./assets/icons/x100.svg"))
        self.button_mult100.toggled.connect(self.toggle_mult100)
        self.button_mult100.setCheckable(True)

        self.button_mult1000 = QPushButton()
        self.button_mult1000.setIcon(QIcon("./assets/icons/x1000.svg"))
        self.button_mult1000.toggled.connect(self.toggle_mult1000)
        self.button_mult1000.setCheckable(True)

        self.buttons_playback = (
            self.button_play,
            self.button_reset,
        )
        self.buttons_mult = (
            self.button_mult10,
            self.button_mult100,
            self.button_mult1000,
        )

        button_size = QSize(32, 32)
        button_size_icon = QSize(24, 24)

        for button in self.buttons_playback+self.buttons_mult:
            button.setFixedSize(button_size)
            button.setIconSize(button_size_icon)
            layout0.addWidget(button)

        # self.setAutoFillBackground()
        # self.setContentsMargins(0, 0, 0, 0)



        stylesheet_time_step_label = """
            QLabel {
                background-color: #0a0a0a;
                font-family: mono;
                font-size: 20px;
            }
        """

        # Labels
        self.label_t = QLabel("0.000/0.000")
        self.label_t.setMinimumWidth(256)
        self.label_step = QLabel("0/0")

        self.update_labels()

        for label in (self.label_t, self.label_step):
            label.setStyleSheet(stylesheet_time_step_label)
            label.setAlignment(Qt.AlignRight)
            layout0.addWidget(label)

        # layout_labels = QGridLayout()
        # layout_labels.addWidget(self.label_t, 1, 1)
        # layout_labels.addWidget(self.label_step, 1, 2)
        # layout0.addLayout(layout_labels)

        self.setLayout(layout0)


    def refresh(self):
        # Stops playback when called
        self.toggle_reset()
        self.button_play.setChecked(False)

        self.str_step_prev = 0
        self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
        self.str_steps = "/{}".format(self.datapool.get_schedule_steps())
        self.update_labels(force_refresh=True)

    def uncheck_buttons(self, buttons_group):
        for button in buttons_group:
            button.setChecked(False)

    def toggle_play(self):
        button = self.button_play
        # print(f"toggle_play() -> checked: {button.isChecked()}")
        if button.isChecked():
            button.setIcon(QIcon("./assets/icons/feather/pause.svg"))
            # print("DO PLAY")
            self.scheduleplayer.start()
            self.label_update_timer.start(self.label_update_interval)

            # self.timer1.start(self.march_interval)
        else:
            button.setIcon(QIcon("./assets/icons/feather/play.svg"))
            # print("DO PAUSE")
            self.scheduleplayer.stop()
            self.label_update_timer.stop()

    def toggle_reset(self):
        # print("DO RESET")
        self.scheduleplayer.reset()


    def set_mult(self, mult):
        # print(f"set_mult({mult})")
        self.scheduleplayer.set_march_mult(mult)

    def toggle_mult10(self):
        # print(f"toggle_mult10() -> checked: {self.button_mult10.isChecked()}")
        if self.button_mult10.isChecked():
            self.button_mult100.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(mult=10)
        else:
            self.set_mult(mult=1)


    def toggle_mult100(self):
        # print(f"toggle_mult100() -> checked: {self.button_mult100.isChecked()}")
        if self.button_mult100.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(mult=100)
        else:
            self.set_mult(mult=1)


    def toggle_mult1000(self):
        # print(f"toggle_mult1000() -> checked: {self.button_mult1000.isChecked()}")
        if self.button_mult1000.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult100.setChecked(False)
            self.set_mult(mult=1000)
        else:
            self.set_mult(mult=1)

    def update_labels(self, force_refresh=False):
        """ Updates the time and step label.

        Optimizations:
         - Pre-generate the string with total steps and duration, so they do
            not have to be calculated in the loop.
         - Replace the only instance of round with a custom 3-digit round that
            has ~30 us less overhead.
         - Save ~10 us of overhead per cycle by not updating steps label when
            step was not updated internally.
        Total improvement from ~150 us to ~50 us
        """
        # t0 = time()  # [TIMING]
        # label_t_str = str((self.scheduleplayer.t * 2001) // 2 / 1000) + self.str_duration
        # label_t_str = str((self.scheduleplayer.t * 2001) // 2 / 1000)
        label_t_str = "{:.3f}{}".format((self.scheduleplayer.t * 2001) // 2 / 1000, self.str_duration)
        # t1 = time())  # [TIMING]
        self.label_t.setText(label_t_str)


        if self.scheduleplayer.step != self.str_step_prev or force_refresh:
            self.label_step.setText(
                # str(self.scheduleplayer.step) + self.str_steps
                "{:}{}".format(self.scheduleplayer.step, self.str_steps)
            )
            self.str_step_prev = self.scheduleplayer.step



    # def update_labels(self, force_refresh=False):
    #     """ Updates the time and step label.
    #
    #     Optimizations:
    #      - Pre-generate the string with total steps and duration, so they do
    #         not have to be calculated in the loop.
    #      - Replace the only instance of round with a custom 3-digit round that
    #         has ~30 us less overhead.
    #      - Save ~10 us of overhead per cycle by not updating steps label when
    #         step was not updated internally.
    #     Total improvement from ~150 us to ~50 us
    #     """
    #     # t0 = time()  # [TIMING]
    #     label_t_str = str((self.scheduleplayer.t * 2001) // 2 / 1000) + self.str_duration
    #     # t1 = time())  # [TIMING]
    #     self.label_t.setText(label_t_str)
    #
    #     # self.label_t.setText(
    #     #     str(round(self.scheduleplayer.t, 3))
    #     #     + "/"
    #     #     + str(round(self.datapool.get_schedule_duration(), 3))
    #     # )
    #
    #     # t2 = time())  # [TIMING]
    #
    #     # if force_refresh:
    #     #     self.label_step.setText(
    #     #         str(self.scheduleplayer.step) + self.str_steps
    #     #     )
    #     #     self.str_step_prev = self.scheduleplayer.step
    #
    #     if self.scheduleplayer.step != self.str_step_prev or force_refresh:
    #         self.label_step.setText(
    #             str(self.scheduleplayer.step) + self.str_steps
    #         )
    #         self.str_step_prev = self.scheduleplayer.step
    #
    #     # self.label_step.setText(
    #     #     str(self.scheduleplayer.step)
    #     #     + "/"
    #     #     + str(self.datapool.get_schedule_steps())
    #     # )
    #
    #     # print(f"[TIMING] update_labels(): {round((t1-t0)*1E6)} us  {round((t2-t1)*1E6)} us  {round((time()-t2)*1E6)} us")  # [TIMING]
