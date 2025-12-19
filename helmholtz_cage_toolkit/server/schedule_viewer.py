""" schedule_viewer

A small GUI tool that visualizes the details of a BSCH schedule file.
"""

# Imports
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from copy import deepcopy
from numpy.lib.recfunctions import append_fields, merge_arrays
from scipy.signal import savgol_filter
from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
from helmholtz_cage_toolkit.file_handling import read_bsch_file
from qt_material import apply_stylesheet
from ast import literal_eval


from helmholtz_cage_toolkit.pg3d import (
    PGFrame3D,
    plotframe2,
)

from pyqtgraph.opengl import (
    GLGridItem,
    GLLinePlotItem,
    GLMeshItem,
    GLScatterPlotItem,
    GLViewWidget,
    MeshData,
)

# def read_bsch_file(filename):
#     # TODO: Should headerless files be supported? Seems like a lot of hassle
#     # for little gain.
#     #
#     header_length = 10
#     with open(filename, 'r') as bsch_file:
#         flag = (bsch_file.readline()).strip("\n")
#         schedule_name = (bsch_file.readline()).strip("\n")
#         generator = bsch_file.readline().strip("\n").split("=")[-1]
#         generation_parameters = literal_eval(bsch_file.readline())
#         interpolation_parameters = literal_eval(bsch_file.readline())
#         for i in range(4):
#             bsch_file.readline()
#         end_of_header = (bsch_file.readline()).strip("\n")
#
#         # for i, item in enumerate((flag, schedule_name, generator, generation_parameters, end_of_header)):
#         #     print(i, ":", item, type(item))
#
#         # Checks
#         if flag != "!BSCH":
#             raise AssertionError(f"While loading '{filename}', header flag !BSCH not found. Are you sure it is a valid .bsch file?")
#
#         if end_of_header != "#"*32:
#             raise AssertionError(f"While loading '{filename}', could not find end of header. Are you sure it is a valid .bsch file?")
#
#         recognised_generators = ("cyclics", "orbital", "none")
#         if generator not in recognised_generators:
#             raise AssertionError(f"While loading '{filename}', encountered unknown generator name {generator}. Currently supported generators: {recognised_generators}")
#
#         raw_schedule = bsch_file.readlines()
#         n = len(raw_schedule)
#         # print(raw_schedule, type(raw_schedule), len(raw_schedule))
#
#         t = empty(n)
#         B = empty((n, 3))
#         for i, line in enumerate(raw_schedule):
#             stringvals = line.strip("\n").split(",")
#             t[i] = stringvals[2]
#             B[i, :] = array((stringvals[3], stringvals[4], stringvals[5]))
#         B = column_stack(B)
#
#     bsch_file.close()
#
#     return t, B, schedule_name, generator, generation_parameters, interpolation_parameters


class TestEvalWindowMain(QMainWindow):
    def __init__(self, config_file) -> None:
        super().__init__()

        # Load config
        self.config = config_file

        self.setWindowIcon(QIcon("../assets/icons/icon2c.png"))
        self.resize(1600, 900)      # Default w x h dimensions

        # Data objects
        self.Bc = None
        self.t = None
        self.schedule_name = None
        self.generator = None
        self.generation_parameters = None
        self.interpolation_parameters = None

        self.manifold_axes_colour = True

        # self.skip_start = 0.0           # [s] Set start time to skip (to discard start-up transients)
        # self.do_delay_correction = False
        # self.manifold_colour_angle = True   # Use angle error to colour 3D manifold, else use field error
        # self.command_delay = 0.100      # [s] Set desired command delay
        # self.csd = 0                    # [S] Set 0 samples as default command delay

        # Tab widgets and layouts
        self.envelopeplot = BcEnvelopePlot()
        self.envelopeplot.setMinimumHeight(420)

        self.cage3dplot = Cage3DTab(self, self.config)
        self.cage3dplot.setMinimumHeight(420)
        self.cage3dplot_L = Cage3DTab(self, self.config)

        self.layout_infobox = QGridLayout()
        self.layout_infobox.addWidget(QLabel("TEST"), 1, 0)

        self.layout_top = QHBoxLayout()
        self.layout_top.addLayout(self.layout_infobox)
        self.layout_top.addWidget(self.cage3dplot)

        self.layout1 = QVBoxLayout()
        self.layout1.addLayout(self.layout_top)
        self.layout1.addWidget(self.envelopeplot)

        dummy_widget = QWidget()
        dummy_widget.setLayout(self.layout1)

        self.plottabs = QTabWidget()
        self.plottabs.addTab(dummy_widget, "Summary")
        self.plottabs.addTab(self.cage3dplot_L, "Cage plot")
        self.setCentralWidget(self.plottabs)

        # Make a menu bar
        menubar = self.create_menubar()
        self.setMenuBar(menubar)

    def create_menubar(self):
        menubar = QMenuBar()
        menu_file = menubar.addMenu("&File")

        act_load = QAction(
            QIcon("../assets/icons/feather/folder.svg"),
            "&Load test data...", self)
        act_load.setStatusTip("Load B-schedule")
        act_load.triggered.connect(self.load_file)
        act_load.setCheckable(False)
        act_load.setShortcut(QKeySequence("Ctrl+o"))
        menu_file.addAction(act_load)

        # act_clear = QAction(
        #     QIcon("../assets/icons/feather/trash.svg"),
        #     "&Clear internal data...", self)
        # act_clear.setStatusTip("Clear all previously loaded test data")
        # act_clear.triggered.connect(self.clearData)
        # act_clear.setCheckable(False)
        # act_clear.setShortcut(QKeySequence("Ctrl+D"))
        # menu_file.addAction(act_clear)

        return menubar


    def load_file(self):
        # Load dialog box
        filename = QFileDialog.getOpenFileName(
            parent=None,
            caption="Select a B-schedule file",
            directory=os.getcwd(),
            filter="B-schedule file (*.bsch);; All files (*.*)",
            initialFilter="B-schedule file (*.bsch)"
        )[0]
        if filename == "":
            print(f"No file selected!")
            return

        self.t = np.empty(0)    # Delete old data first
        self.Bc = np.empty(0)    # Delete old data first

        # try:
        (
            self.t, self.Bc, self.schedule_name, self.generator,
            self.generation_parameters, self.interpolation_parameters
        ) = read_bsch_file(filename)
        # except:
        #     print(f"Error during loading of file '{filename}'!\n")

        # Measure sample time in dataset
        sample_time = np.mean(self.t[1:8] - self.t[0:7])
        print(f"Sample rate: {round(1 / sample_time, 2)} S/s")
        assert (sample_time > 0.0)

        self.setWindowTitle(filename)

        # self.doDataAnalysis()

        self.envelopeplot.generate_plot(self.t, self.Bc)

        self.cage3dplot.clear()
        self.cage3dplot.draw_statics()
        self.cage3dplot.draw_simdata()

        self.cage3dplot_L.clear()
        self.cage3dplot_L.draw_statics()
        self.cage3dplot_L.draw_simdata()

    def clearData(self):
        # self.envelopetab.envelope_plot.plot_obj.clearPlots()
        #
        # self.errortab1.error_plot_abs.plot_obj.clearPlots()
        # self.errortab1.envelope_plot.plot_obj.clearPlots()
        #
        # # self.errortab2.error_plot_abs.plot_obj.clearPlots()
        # self.errortab2.error_plot_ang.plot_obj.clearPlots()
        # self.errortab2.envelope_plot.plot_obj.clearPlots()
        #
        # self.derivtab1.deriv_plot.plot_obj_t.clearPlots()
        # self.derivtab1.deriv_plot.plot_obj_dt.clearPlots()
        # self.derivtab1.deriv_plot.plot_obj_e.clearPlots()
        #
        # self.currenttab1.current_plot.plot_obj_t.clearPlots()
        # self.currenttab1.current_plot.plot_obj_i.clearPlots()
        # self.currenttab1.current_plot.plot_obj_e.clearPlots()
        #
        # self.cage3dtab.clear()
        # self.cage3dtab.draw_statics()
        #
        # self.data = None

        pass




class BcEnvelopePlot(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-6)

        # Add a more prominent zero axis
        self.zeroaxis = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj.addItem(self.zeroaxis)

        # self.vline = pg.InfiniteLine(angle=90, movable=False,
        #                              pen=pg.mkPen("c", width=2),)
        # self.vline.setZValue(10)
        # self.plot_obj.addItem(self.vline, ignoreBounds=True)

        # if data:
        #     self.generate_plot(data)

    def generate_plot(self, t, Bc, show_actual=True, show_points=False):
        # t = data["t"]
        # Bc = array([
        #     data["Bcx"],
        #     data["Bcy"],
        #     data["Bcz"],
        # ])

        print(Bc)
        Bc_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
        Bc_colours_line = [(255, 0, 0, 64), (0, 255, 0, 64), (0, 0, 255, 64)]

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        Bc_stag = array((repeat(Bc[0, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[1, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[2, push[0]:push[1]], 2)[:-1],
                         ))

        self.plot_obj.clearPlots()

        for i in range(3):
            # Staggered line
            self.plot_obj.plot(
                t_stag,
                Bc_stag[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj.plot(
                t, Bc[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )


class Cage3DTab(GLViewWidget):
    def __init__(self, parent, config):
        super().__init__()

        # print("[DEBUG] Cage3DPlot.__init__() called")
        self.mw = parent
        self.config = config
        self.resize(720, 360)

        # Shorthands for common config settings
        self.ps = self.config["c3dcw_plotscale"]  # Plot scale
        self.c = self.config["ov_plotcolours"]
        self.aa = self.config["ov_use_antialiasing"]
        self.zo = self.config["c3dcw_cage_dimensions"]["z_offset"] * self.ps
        self.zov = array([0.0, 0.0, self.zo])
        self.linescale = 1

        print("zov 0 ", self.zov)

        self.tail_length = self.config["c3dcw_tail_length"]

        self.opts["center"] = QVector3D(0, 0, self.zo)
        self.setCameraPosition(distance=5*self.ps, azimuth=-20, elevation=25)
        # self.setCameraPosition(distance=5*self.ps, pos=(0, 0, 2.5*self.ps))

        self.max_b_absvals = np.array([200, 200, 200])
        self.draw_statics()


    def draw_statics(self):

        """Draws static objects into the GLViewWidget. Static objects are
        objects whose plots are independent of the schedule or simulation data,
        and so they ideally are drawn only once.
        """

        # print("[DEBUG] Cage3DPlot.draw_statics() called")

        # Generate grid
        self.make_xy_grid()

        # Generate frame tripod_components
        self.make_tripod_b()

        # Generate cage structure components
        self.make_cage_structure()

        # Generate satellite model
        self.make_satellite_model()

    def draw_simdata(self):
        max_b_absvals = [
            max(abs(min(self.mw.Bc[0])), abs(max(self.mw.Bc[0]))),
            max(abs(min(self.mw.Bc[1])), abs(max(self.mw.Bc[1]))),
            max(abs(min(self.mw.Bc[2])), abs(max(self.mw.Bc[2]))),
        ]
        self.linescale = 0.7 * (100/max(max_b_absvals))
        # print(f"[DEBUG] B_abs_max: {max(max_b_absvals)}")
        print(f"[DEBUG] LINE SCALE set to {self.linescale}")

        if self.mw.t is None or self.mw.Bc is None:     # If simdata is not generated yet, skip plotting
            return 0

        self.make_lineplot_Bc()
        # self.make_lineplot_Bm(normalize_value=0)
        self.make_linespokes()

    def make_xy_grid(self):
        # Add horizontal grid
        self.xy_grid = GLGridItem(antialias=self.aa)
        self.xy_grid.setColor((255, 255, 255, 24))
        self.xy_grid.setSize(x=2*self.ps, y=2*self.ps)
        self.xy_grid.setSpacing(x=int(self.ps/10), y=int(self.ps/10))  # Comment out this line at your peril...
        self.xy_grid.setDepthValue(20)  # Ensure grid is drawn after most other features

        if self.config["c3d_draw"]["xy_grid"]:
            self.addItem(self.xy_grid)

    def make_tripod_b(self):
        self.frame_b = PGFrame3D(o=self.zov)
        self.tripod_b = plotframe2(
            self.frame_b,
            width=3, plotscale=0.25 * self.ps, alpha=0.9, antialias=self.aa
        )
        if self.config["c3d_draw"]["tripod_b"]:
            for item in self.tripod_b:
                self.addItem(item)

    def make_cage_structure(self):
        self.cage_structure = []

        scale = self.ps
        dim_x = self.config["c3d_cage_dimensions"]["x"]
        dim_y = self.config["c3d_cage_dimensions"]["y"]
        dim_z = self.config["c3d_cage_dimensions"]["z"]
        dim_t = self.config["c3d_cage_dimensions"]["t"]
        s = self.config["c3d_cage_dimensions"]["spacing"]

        m = [1, 1, -1, -1, 1, 1]

        alpha = self.config["c3d_cage_alpha"]

        # Make an array containing all corners of the cage structure, and
        # repeat the first entry at the end to "close" it when plotting.

        # X-coils
        x_coil_pos = array(
            [[dim_x * s / 2, m[i] * dim_x / 2, m[i + 1] * dim_x / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        x_coil_neg = 1 * x_coil_pos  # 1 * array is a poor man's deepcopy()
        x_coil_neg[:, 0] = -1 * x_coil_neg[:, 0]

        self.cage_structure.append(GLLinePlotItem(
            pos=x_coil_pos,
            color=(0.5, 0, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=x_coil_neg,
            color=(0.5, 0, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))


        # Y-coils
        y_coil_pos = array(
            [[m[i] * dim_y / 2, dim_y * s / 2, m[i + 1] * dim_y / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        y_coil_neg = 1 * y_coil_pos
        y_coil_neg[:, 1] = -1 * y_coil_neg[:, 1]

        self.cage_structure.append(GLLinePlotItem(
            pos=y_coil_pos,
            color=(0, 0.5, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=y_coil_neg,
            color=(0, 0.5, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))


        # Z-coils
        z_coil_pos = array(
            [[m[i] * dim_z / 2, m[i + 1] * dim_z / 2, dim_z * s / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        z_coil_neg = 1 * z_coil_pos
        z_coil_neg[:, 2] = (-1 * (z_coil_neg[:, 2] - self.zo/self.ps*scale)) + self.zo/self.ps*scale

        self.cage_structure.append(GLLinePlotItem(
            pos=z_coil_pos,
            color=(0.15, 0.15, 0.5, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=z_coil_neg,
            color=(0.15, 0.15, 0.5, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))

        if self.config["c3d_draw"]["cage_structure"]:
            for element in self.cage_structure:
                self.addItem(element)

    def make_satellite_model(self):
        [x_dim, y_dim, z_dim, x, y, z] = \
        [self.config["c3d_satellite_model"][item] for item in
         ["x_dim", "y_dim", "z_dim", "x", "y", "z"]]
        corners = array([
            [ x_dim / 2,  y_dim / 2, -z_dim / 2],
            [ x_dim / 2, -y_dim / 2, -z_dim / 2],
            [-x_dim / 2, -y_dim / 2, -z_dim / 2],
            [-x_dim / 2,  y_dim / 2, -z_dim / 2],
            [ x_dim / 2,  y_dim / 2,  z_dim / 2],
            [ x_dim / 2, -y_dim / 2,  z_dim / 2],
            [-x_dim / 2, -y_dim / 2,  z_dim / 2],
            [-x_dim / 2,  y_dim / 2,  z_dim / 2],
        ]) * self.ps

        points = []
        for i in range(8):
            points.append(corners[i])
            points.append(corners[(i+4) % 8])
            points.append(corners[i])
            if i == 3:
                points.append(corners[0])
            if i == 7:
                points.append(corners[4])

        points = array(points)

        for i, point in enumerate(points):
            points[i] = point + array([x, y, z])*self.ps + self.zov
        #
        # # Offset all the data for plotting purposes
        # for i in range(len(points)):
        #     points[i][2] = points[i][2]+self.zo

        self.satellite_model = GLLinePlotItem(
            pos=points,
            # color=self.c[self.config["c3d_preferred_colour"]],
            color=(1.0, 0.5, 0.0, 0.4),
            width=3,
            antialias=self.config["ov_use_antialiasing"]
        )
        self.satellite_model.setDepthValue(0)

        if self.config["c3d_draw"]["satellite_model"]:
            self.addItem(self.satellite_model)

    def make_lineplot_Bc(self):
        points = self.mw.Bc.transpose() * self.linescale
        # points = np.array([
        #     self.mw.data["Bcx"],
        #     self.mw.data["Bcy"],
        #     self.mw.data["Bcz"],
        # ]).transpose() * self.linescale

        max_axesval = max(np.array([
            max(np.abs(self.mw.Bc[0])),
            max(np.abs(self.mw.Bc[1])),
            max(np.abs(self.mw.Bc[2])),
        ]))

        magvals = np.sqrt(self.mw.Bc[0]**2 + self.mw.Bc[1]**2 + self.mw.Bc[2]**2)
        max_magval = max(magvals)

        # Prevent singularity
        if max_axesval == 0:
            max_axesval = 1
        # Prevent singularity
        if max_magval == 0:
            max_magval = 1

        colour_array = None
        if self.mw.manifold_axes_colour:
            colour_array = np.array([
                1.2 * np.abs(self.mw.Bc[0])/max_axesval + 0.5 * (1 - magvals/max_magval),
                1.2 * np.abs(self.mw.Bc[1])/max_axesval + 0.5 * (1 - magvals/max_magval),
                1.2 * np.abs(self.mw.Bc[2])/max_axesval + 0.5 * (1 - magvals/max_magval),
                np.zeros_like(self.mw.Bc[0]) + 0.75,
            ]).transpose()

        # print("/n [DEBUG] Bc[0:10], Bc[-10:]")
        # print(points[:][0:10], "\n")
        # print(points[:][-10:], "\n")

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        print("Bc: ", points[0][2])

        if self.mw.manifold_axes_colour:
            self.lineplot = GLLinePlotItem(
                pos=points,
                # color=self.c[self.config["c3d_preferred_colour"]],
                # color=[Ecnorm, 1-Ecnorm, np.full(1.), np.full((0.25)],
                color=colour_array,
                # color=(1.0, 0.3, 0.0, 0.25),
                width=2,
                antialias=self.config["ov_use_antialiasing"]
            )
        else:
            self.lineplot = GLLinePlotItem(
                pos=points,
                # color=self.c[self.config["c3d_preferred_colour"]],
                color=(1, 0.38, 0, 0.75),
                width=2,
                antialias=self.config["ov_use_antialiasing"]
            )

        self.lineplot.setDepthValue(1)

        if self.config["c3d_draw"]["lineplot"]:
            self.addItem(self.lineplot)

    def make_lineplot_Bm(self, normalize_value: float = 0.0):
        # Ecabs = self.mw.Ecabs
        # Ecmag = np.sqrt(Ecabs[0]**2 + Ecabs[1]**2 + Ecabs[2]**2)
        # Ecmax = max(Ecmag)
        # Ecnorm = Ecmag/Ecmax

        # print("Ecmax: ", Ecmax)
        Enorm = None

        if self.mw.manifold_colour_angle:
            if normalize_value <= 0:  # Normalize to Ecmax
                Emax = self.mw.Eanglemax
                Enorm = self.mw.Eangle / Emax
            else:
                Enorm = self.mw.Eangle / normalize_value
        else:
            if normalize_value <= 0:  # Normalize to Ecmax
                Emax = max(self.mw.Ecmag)
                Enorm = self.mw.Ecmag / Emax
            else:
                Enorm = self.mw.Ecmag / normalize_value

        colour_array = np.array([
            Enorm,
            1 - Enorm,
            np.zeros(len(Enorm)),
            np.zeros(len(Enorm)) + 0.75,
        ]).transpose()

        # colour_array = [
        #     Ecnorm.tolist(),
        #     (1 - Ecnorm).tolist(),
        #     (np.ones(len(Ecnorm))).tolist(),
        #     (np.zeros(len(Ecnorm)) + 0.25).tolist(),
        # ]
        points = self.mw.Bc.transpose() * self.linescale
        # points = np.array([
        #     self.mw.data["Bmx"],
        #     self.mw.data["Bmy"],
        #     self.mw.data["Bmz"],
        # ]).transpose() * self.linescale

        # print("/n [DEBUG] Bm[0:10], Bm[-10:]")
        # print(points[:][0:10], "\n")
        # print(points[:][-10:], "\n")

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.config["c3d_preferred_colour"]],
            # color=[Ecnorm, 1-Ecnorm, np.full(1.), np.full((0.25)],
            color=colour_array,
            # color=(1.0, 0.3, 0.0, 0.25),
            width=2,
            antialias=self.config["ov_use_antialiasing"]
        )
        self.lineplot.setDepthValue(1)

        if self.config["c3d_draw"]["lineplot"]:
            self.addItem(self.lineplot)

    def make_linespokes(self):
        # Add all line spokes as one long line, so it fits in one big GLLinePlotItem,
        # which is MUCH more efficient than making one for each spoke.

        ppoints = self.mw.Bc.transpose() * self.linescale

        points = []
        for i in range(len(self.mw.t)):
            points.append(ppoints[i])
            points.append(3/4*ppoints[i])
            points.append(ppoints[i])

        points = np.array(points)

        self.linespokes = GLLinePlotItem(
            pos=points + np.array([0, 0, self.zo]),
            color=(0.5, 0.5, 0.5, 0.1),
            antialias=self.config["ov_use_antialiasing"],
            width=1)
        self.linespokes.setDepthValue(0)

        self.addItem(self.linespokes)

        return None


if __name__ == "__main__":

    app = QApplication(sys.argv)

    theme_file = "dark_teal.xml"
    apply_stylesheet(app, theme=theme_file)

    window = TestEvalWindowMain(config)
    window.show()
    app.exec()