from time import time
from scipy.special import jv
from pyIGRF import igrf_value

import pyqtgraph as pg
from pyqtgraph.opengl import (
    GLGridItem,
    GLLinePlotItem,
    GLMeshItem,
    GLScatterPlotItem,
    GLViewWidget,
    MeshData,
)

from helmholtz_cage_toolkit import *

from helmholtz_cage_toolkit.pg3d import (
    RX, RY, RZ, R,
    PGPoint3D, PGVector3D, PGFrame3D,
    plotgrid, plotpoint, plotpoints, plotvector, plotframe2,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
    sign, wrap, uv3d,
    conv_ECI_geoc,
    R_NED_ECI, R_ECI_NED,
    R_SI_B, R_B_SI,
    R_ECI_ECEF, R_ECEF_ECI
)

from helmholtz_cage_toolkit.orbit import Orbit, Earth
from helmholtz_cage_toolkit.utilities import cross3d

# Goal: display simdata output from Orbitals generator
# - Generalized OrbitalPlot class that can:
#     - Initialize visual screen
#     - Take simdata from <somewhere>
#     - Draw non-updatables
#     - Draw updatables
#     - Loop controls using timers
#     -



class Cage3DPlotCW(GLViewWidget):
    def __init__(self, datapool):
        super().__init__()

        # print("[DEBUG] Cage3DPlot.__init__() called")

        self.data = datapool
        self.data.cage3d_plot = self

        self.resize(720, 360)

        # Shorthands for common config settings
        self.ps = self.data.config["c3dcw_plotscale"]  # Plot scale
        self.c = self.data.config["ov_plotcolours"]
        self.aa = self.data.config["ov_use_antialiasing"]
        self.zo = self.data.config["c3dcw_cage_dimensions"]["z_offset"] * self.ps
        self.zov = array([0.0, 0.0, self.zo])

        print("zov 0 ", self.zov)

        self.tail_length = self.data.config["c3dcw_tail_length"]

        self.opts["center"] = QVector3D(0, 0, self.zo)
        self.setCameraPosition(distance=5*self.ps, azimuth=-20, elevation=25)
        # self.setCameraPosition(distance=5*self.ps, pos=(0, 0, 2.5*self.ps))

        self.prev = {
            "be": [0., 0., 0.],
            "bm": [0., 0., 0.],
        }


    def draw_statics(self):

        """Draws static objects into the GLViewWidget. Static objects are
        objects whose plots are independent of the schedule or simulation data,
        and so they ideally are drawn only once.
        """

        # print("[DEBUG] Cage3DPlot.draw_statics() called")

        # Generate grid
        self.make_xy_grid()

        # Generate tripod_components
        self.make_tripod()

        # Draw cage structure
        self.make_cage_structure()

        # Generate satellite model
        self.make_satellite_model()

        # # Draw Earth meshitem
        # if self.data.config["ov_draw"]["earth_model"]:
        #     self.earth_meshitem = self.make_earth_meshitem()
        #     # if self.th_E != 0: # Moved to draw_simdata()
        #     #     self.earth_meshitem.rotate(self.th_E*180/pi, 0, 0, 1, local=False)
        #     self.addItem(self.earth_meshitem)


    def draw_data(self, i_step=0):

        # self.max_b_absvals = [
        #     max(
        #         abs(min(self.data.simdata["B_B"][:, 0])),
        #         abs(max(self.data.simdata["B_B"][:, 0]))
        #     ),
        #     max(
        #         abs(min(self.data.simdata["B_B"][:, 1])),
        #         abs(max(self.data.simdata["B_B"][:, 1]))
        #     ),
        #     max(
        #         abs(min(self.data.simdata["B_B"][:, 2])),
        #         abs(max(self.data.simdata["B_B"][:, 2]))
        #     ),
        # ]

        # self.max_b_absvals = [1E4, 1E4, 1E4] # TODO Update
        # print("max_b_absvals: ", self.max_b_absvals)

        # if self.data.simdata is None:     # If simdata is not generated yet, skip plotting
        #     return 0

        # self.i_step = i_step
        #
        # self.make_lineplot()
        #
        # self.make_b_vector()
        #
        # self.make_b_dot()
        #
        # self.make_b_tail()
        #
        # self.make_linespokes()
        #
        # self.make_b_components()

        self.make_be()

        self.make_bm()



    def draw_update(self):
        """Pulls new data from the datapool and draws what it needs to draw.
        """

        # print("draw_update()")

        be = self.data.Be
        # Update if it is not hidden, not zero, and not equal to the previous
        if self.data.config["c3dcw_draw"]["be"]\
                and be != self.prev["be"]:
            self.be_plotitem.setData(pos=[self.zov, self.zov + be])
            self.prev["be"] = be

        bm = self.data.Bm
        # Update if it is not hidden, not zero, and not equal to the previous
        if self.data.config["c3dcw_draw"]["bm"] \
                and bm != self.prev["bm"]:
            self.bm_plotitem.setData(pos=[self.zov, self.zov + bm])
            self.prev["bm"] = bm

        # # print("test1", self.data.simdata["B_B"][i_step % self.data.simdata["n_step"]])
        # bbi = self.data.simdata["B_B"][i_step % self.data.simdata["n_step"]]*1 + self.zov
        #
        # # print("test2", bbi)
        # bbx = array((bbi[0], 0., self.zo))
        # bby = array((0., bbi[1], self.zo))
        # bbz = array((0., 0., bbi[2]))
        #
        # if self.data.config["c3dcw_draw"]["b_vector"]:
        #     self.b_vector_plotitem.setData(pos=[self.zov, bbi])
        #
        # if self.data.config["c3dcw_draw"]["b_dot"]:
        #     self.b_dot_plotitem.setData(pos=bbi)
        #
        # if self.data.config["c3dcw_draw"]["b_tail"]:
        #     for i, segment_length in enumerate(self.tail_length):
        #         segment = self.data.simdata["B_B"][max(0, i_step - min(i_step, segment_length)):i_step]*1 + self.zov
        #         self.b_tail_plotitems[i].setData(pos=segment)
        #
        # if self.data.config["c3dcw_draw"]["b_components"]:
        #     self.b_components[0].setData(pos=[self.zov, bbx])
        #     self.b_components[1].setData(pos=[self.zov, bby])
        #     self.b_components[2].setData(pos=[self.zov, bbz])
        #     xy = array([bbi[0], bbi[1], self.zo])
        #     self.b_components[3].setData(
        #         pos=[xy, bbx, xy, bby, xy, bbi, xy]
        #     )
        #
        # if self.data.config["c3dcw_draw"]["cage_structure"] and \
        #     self.data.config["c3dcw_draw"]["cage_illumination"]:
        #     # Vary the colour and alpha intensity based on component magnitude
        #     intensity = [
        #         abs(bbi[0]) / self.max_b_absvals[0] * 0.5,
        #         abs(bbi[1]) / self.max_b_absvals[1] * 0.5,
        #         abs(bbi[2]-self.zo) / self.max_b_absvals[2] * 0.5 * 1.25,
        #     ]
        #     colours = [
        #         (0.5 + intensity[1], 0.0, 0.0,      # RGB channels X
        #          0.1 + intensity[0]),               # alpha channel X
        #         ( 0.0, 0.5 + intensity[1], 0.0,     # etc...
        #           0.1 + intensity[1]),
        #         (intensity[2]/3, intensity[2]/3, 0.5 + intensity[2],
        #          0.1 + intensity[2]),
        #     ]
        #
        #     for i, coil in enumerate(self.cage_structure):
        #         coil.setData(color=colours[int(i/2)])


    def make_be(self):
        base = self.zov
        tip = self.data.Be + self.zov

        print("TIP BE:", tip)

        self.be_plotitem = GLLinePlotItem(
            pos=[base, tip],
            color=(0.0, 0.85, 0.0, 1.0),
            antialias=self.data.config["ov_use_antialiasing"],
            width=4)
        self.be_plotitem.setDepthValue(0)

        if self.data.config["c3dcw_draw"]["be"]:
            self.addItem(self.be_plotitem)


    def make_bm(self):
        base = self.zov
        tip = self.data.Bm + self.zov

        print("TIP BM:", tip)

        self.bm_plotitem = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 0.5, 0.0, 1.0),
            antialias=self.data.config["ov_use_antialiasing"],
            width=4)
        self.bm_plotitem.setDepthValue(0)

        if self.data.config["c3dcw_draw"]["bm"]:
            self.addItem(self.bm_plotitem)


    def make_xy_grid(self):
        # Add horizontal grid
        self.xy_grid = GLGridItem(antialias=self.aa)
        self.xy_grid.setColor((255, 255, 255, 24))
        self.xy_grid.setSize(x=2*self.ps, y=2*self.ps)
        self.xy_grid.setSpacing(x=int(self.ps/10), y=int(self.ps/10))  # Comment out this line at your peril...
        self.xy_grid.setDepthValue(20)  # Ensure grid is drawn after most other features

        if self.data.config["c3dcw_draw"]["xy_grid"]:
            self.addItem(self.xy_grid)

    def make_tripod(self):
        self.frame = PGFrame3D(o=self.zov)
        self.tripod = plotframe2(
            self.frame,
            plotscale=0.25 * self.ps, alpha=0.4, antialias=self.aa
        )
        if self.data.config["c3dcw_draw"]["tripod"]:
            for item in self.tripod:
                self.addItem(item)


    def make_cage_structure(self):
        self.cage_structure = []

        scale = self.ps
        dim_x = self.data.config["c3dcw_cage_dimensions"]["x"]
        dim_y = self.data.config["c3dcw_cage_dimensions"]["y"]
        dim_z = self.data.config["c3dcw_cage_dimensions"]["z"]
        dim_t = self.data.config["c3dcw_cage_dimensions"]["t"]
        s = self.data.config["c3dcw_cage_dimensions"]["spacing"]

        m = [1, 1, -1, -1, 1, 1]

        alpha = self.data.config["c3dcw_cage_alpha"]

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
            antialias=self.data.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=x_coil_neg,
            color=(0.5, 0, 0, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
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
            antialias=self.data.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=y_coil_neg,
            color=(0, 0.5, 0, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
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
            antialias=self.data.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=z_coil_neg,
            color=(0.15, 0.15, 0.5, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
        ))

        if self.data.config["c3dcw_draw"]["cage_structure"]:
            for element in self.cage_structure:
                self.addItem(element)


    def make_satellite_model(self):
        [x_dim, y_dim, z_dim, x, y, z] = \
        [self.data.config["c3dcw_satellite_model"][item] for item in
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
            # color=self.c[self.data.config["c3dcw_preferred_colour"]],
            color=(1.0, 0.5, 0.0, 0.4),
            width=3,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.satellite_model.setDepthValue(0)

        if self.data.config["c3dcw_draw"]["satellite_model"]:
            self.addItem(self.satellite_model)

    def make_lineplot(self):

        points = self.data.simdata["B_B"][:]*1

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.data.config["c3dcw_preferred_colour"]],
            color=(0, 1, 1, 0.25),
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.lineplot.setDepthValue(1)

        if self.data.config["c3dcw_draw"]["lineplot"]:
            self.addItem(self.lineplot)


    # def make_scatterplot(self):
    #
    #     scatterplot = GLScatterPlotItem(
    #         pos=self.data.simdata["xyz"],
    #         color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
    #         size=4,
    #         pxMode=True)
    #     scatterplot.setDepthValue(0)
    #     return scatterplot

    def make_b_vector(self):

        base = self.zov
        tip = self.data.simdata["B_B"][self.i_step]*1 + self.zov

        self.b_vector_plotitem = GLLinePlotItem(
            pos=[base, tip],
            color=(0., 1.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=4)
        self.b_vector_plotitem.setDepthValue(0)

        if self.data.config["c3dcw_draw"]["b_vector"]:
            self.addItem(self.b_vector_plotitem)


    def make_b_dot(self):

        point = self.data.simdata["B_B"][self.i_step]*1 + self.zov
        self.b_dot_plotitem = GLScatterPlotItem(
            pos=point,
            color=(0.0, 1.0, 1.0, 1),
            size=8,
            pxMode=True)
        self.b_dot_plotitem.setDepthValue(2)

        if self.data.config["c3dcw_draw"]["b_dot"]:
            self.addItem(self.b_dot_plotitem)


    def make_b_tail(self):

        self.b_tail_plotitems = []

        # la = self.data.config["c3dcw_line_alpha"]
        # alphas = [i/len(self.tail_length)*(1-la)+la for i in range(len(self.tail_length), 0, -1)]
        intensity = [i/len(self.tail_length) for i in range(len(self.tail_length), 0, -1)]
        # print("DEBUG alphas", intensity)

        for i, segment_length in enumerate(self.tail_length):
            segment = self.data.simdata["B_B"][self.i_step-min(self.i_step, segment_length):self.i_step]*1

            self.b_tail_plotitems.append(GLLinePlotItem(
                pos=segment,
                # color=self.c[self.data.config["c3dcw_preferred_colour"]],
                color=(intensity[i], 1, 1, 0.1),
                width=3,
                antialias=self.data.config["ov_use_antialiasing"]
            ))
            self.b_tail_plotitems[i].setDepthValue(1)

        # Offset all the data for plotting purposes
        # for i in range(len(points)):
        #     points[i][2] = points[i][2]+self.zo

        if self.data.config["c3dcw_draw"]["b_tail"]:
            for i, element in enumerate(self.b_tail_plotitems):
                self.addItem(element)


    def make_b_components(self):
        self.b_components = []

        base = self.zov

        [x, y, z] = self.data.simdata["B_B"][self.i_step] * 1

        x_tip = array([x, 0, 0]) + self.zov
        y_tip = array([0, y, 0]) + self.zov
        z_tip = array([0, 0, z]) + self.zov

        alpha = self.data.config["c3dcw_component_alpha"]

        self.b_components.append(GLLinePlotItem(
            pos=[base, x_tip],
            color=(0.8, 0, 0, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
        ))
        self.b_components.append(GLLinePlotItem(
            pos=[base, y_tip],
            color=(0, 0.8, 0, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
        ))
        self.b_components.append(GLLinePlotItem(
            pos=[base, z_tip],
            color=(0, 0, 0.8, alpha),
            width=5,
            antialias=self.data.config["ov_use_antialiasing"]
        ))

        xy = array([x, y, 0]) + self.zov
        skeleton = [xy, x_tip, xy, y_tip, xy, array([x, y, z]), xy]

        self.b_components.append(GLLinePlotItem(
            pos=skeleton,
            color=(0.5, 0.5, 0.5, 0.2),
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        ))

        if self.data.config["c3dcw_draw"]["b_components"]:
            for element in self.b_components:
                self.addItem(element)


    def make_linespokes(self):
        # Add all line spokes as one long line, so it fits in one big GLLinePlotItem,
        # which is MUCH more efficient than making one for each spoke.
        points = []
        for i in range(self.data.simdata["n_step"]):
            points.append(self.data.simdata["B_B"][i]*1)
            points.append(3/4*self.data.simdata["B_B"][i]*1)
            # points.append(3/4*self.data.simdata["B_B"][i])
            points.append(self.data.simdata["B_B"][i]*1)

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.linespokes = GLLinePlotItem(
            pos=points,
            color=(0.5, 0.5, 0.5, 0.2),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        self.linespokes.setDepthValue(0)

        if self.data.config["c3dcw_draw"]["linespokes"]:
            self.addItem(self.linespokes)



class Cage3DPlotButtonsCW(QGroupBox):
    """Description"""
    def __init__(self, cage3dplot, datapool) -> None:
        super().__init__()

        self.cage3dplot = cage3dplot
        self.data = datapool

        self.layout0 = QGridLayout()
        self.buttons = []

        # Generate buttons
        self.button_bc = QPushButton(QIcon("./assets/icons/vector_bc.svg"), "")
        self.setup(self.button_bc, "bc")
        self.button_bc.toggled.connect(self.toggle_bc)

        self.button_satellite_model = QPushButton(QIcon("./assets/icons/satellite.svg"), "")
        self.setup(self.button_satellite_model, "satellite_model")
        self.button_satellite_model.toggled.connect(self.toggle_satellite_model)


        self.button_br = QPushButton(QIcon("./assets/icons/vector_br.svg"), "")
        self.setup(self.button_br, "br")
        self.button_bc.toggled.connect(self.toggle_br)

        self.button_cage_structure = QPushButton(QIcon("./assets/icons/cage.svg"), "")
        self.setup(self.button_cage_structure, "cage_structure")
        self.button_cage_structure.toggled.connect(self.toggle_cage_structure)


        self.button_bt = QPushButton(QIcon("./assets/icons/vector_bt.svg"), "")
        self.setup(self.button_bt, "bt")
        self.button_bt.toggled.connect(self.toggle_bt)

        self.button_cage_illumination = QPushButton(QIcon("./assets/icons/cage_i2.svg"), "")
        self.setup(self.button_cage_illumination, "cage_illumination")
        self.button_cage_illumination.toggled.connect(self.toggle_cage_illumination)


        self.button_bm = QPushButton(QIcon("./assets/icons/vector_bm.svg"), "")
        self.setup(self.button_bm, "bm")
        self.button_bm.toggled.connect(self.toggle_bm)

        self.button_dots = QPushButton(QIcon("./assets/icons/dot.svg"), "")
        self.setup(self.button_dots, "dots")
        self.button_dots.toggled.connect(self.toggle_dots)


        self.button_ec = QPushButton(QIcon("./assets/icons/vector_ec.svg"), "")
        self.setup(self.button_ec, "ec")
        self.button_ec.toggled.connect(self.toggle_ec)

        self.button_tails = QPushButton(QIcon("./assets/icons/tail2.svg"), "")
        self.setup(self.button_tails, "tails")
        self.button_tails.toggled.connect(self.toggle_tails)


        self.button_be = QPushButton(QIcon("./assets/icons/vector_be.svg"), "")
        self.setup(self.button_be, "be")
        self.button_be.toggled.connect(self.toggle_be)

        self.button_b_components = QPushButton(QIcon("./assets/icons/components.svg"), "")
        self.setup(self.button_b_components, "b_components")
        self.button_b_components.toggled.connect(self.toggle_b_components)


        self.button_xy_grid = QPushButton(QIcon("./assets/icons/grid2.svg"), "")
        self.setup(self.button_xy_grid, "xy_grid")
        self.button_xy_grid.toggled.connect(self.toggle_xy_grid)

        self.button_lineplot = QPushButton(QIcon("./assets/icons/lineplot.svg"), "")
        self.setup(self.button_lineplot, "lineplot")
        self.button_lineplot.toggled.connect(self.toggle_lineplot)


        self.button_tripod = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod, "tripod")
        self.button_tripod.toggled.connect(self.toggle_tripod)

        self.button_linespokes = QPushButton(QIcon("./assets/icons/lineplot_spokes.svg"), "")
        self.setup(self.button_linespokes, "linespokes")
        self.button_linespokes.toggled.connect(self.toggle_linespokes)


        self.button_autorotate = QPushButton(QIcon("./assets/icons/autorotate.svg"), "")
        self.setup(self.button_autorotate, "autorotate")
        self.button_autorotate.toggled.connect(self.toggle_autorotate)


        # self.setStyleSheet(self.data.config["stylesheet_groupbox_smallmargins_notitle"])
        self.setLayout(self.layout0)
        self.layout0.setSizeConstraint(QLayout.SetMinimumSize)
        self.setMaximumSize(32, 320)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout0.setVerticalSpacing(1)
        self.layout0.setColumnStretch(0, 0)
        self.layout0.setColumnStretch(1, 0)


    def setup(self, button, reference: str, label="", hpos=0):
        """A shorthand function to inherit the 'checked' properties based on
        the visibility of various plot items as defined in the config file.
        This must be done before the toggled() action is connected, in order
        to prevent the toggled () action being triggered and causing plot
        elements to be redrawn unnecessarily.
        """
        button.setCheckable(True)
        if self.data.config["c3dcw_draw"][reference] is True:
            button.setChecked(True)
        button.setFixedSize(QSize(32, 32))
        button.setIconSize(QSize(24, 24))

        # Put the buttons on two colums in the GridLayout
        d, r = divmod(len(self.buttons), 2)
        self.layout0.addWidget(button, d, r)
        self.buttons.append(button)


    def toggle_bc(self):
        if self.button_bc.isChecked():
            self.data.config["c3dcw_draw"]["bc"] = True
            self.cage3dplot.make_bc()
        else:
            self.data.config["c3dcw_draw"]["bc"] = False
            self.cage3dplot.removeItem(self.cage3dplot.bc_plotitem)

    def toggle_br(self):
        if self.button_br.isChecked():
            self.data.config["c3dcw_draw"]["br"] = True
            self.cage3dplot.make_br()
        else:
            self.data.config["c3dcw_draw"]["br"] = False
            self.cage3dplot.removeItem(self.cage3dplot.br_plotitem)

    def toggle_bt(self):
        if self.button_bt.isChecked():
            self.data.config["c3dcw_draw"]["bt"] = True
            self.cage3dplot.make_bt()
        else:
            self.data.config["c3dcw_draw"]["bt"] = False
            self.cage3dplot.removeItem(self.cage3dplot.bt_plotitem)

    def toggle_bm(self):
        if self.button_bm.isChecked():
            self.data.config["c3dcw_draw"]["bm"] = True
            self.cage3dplot.make_bm()
        else:
            self.data.config["c3dcw_draw"]["bm"] = False
            self.cage3dplot.removeItem(self.cage3dplot.bm_plotitem)

    def toggle_ec(self):
        if self.button_ec.isChecked():
            self.data.config["c3dcw_draw"]["ec"] = True
            self.cage3dplot.make_ec()
        else:
            self.data.config["c3dcw_draw"]["ec"] = False
            self.cage3dplot.removeItem(self.cage3dplot.ec_plotitem)

    def toggle_be(self):
        if self.button_be.isChecked():
            self.data.config["c3dcw_draw"]["be"] = True
            self.cage3dplot.make_be()
        else:
            self.data.config["c3dcw_draw"]["be"] = False
            self.cage3dplot.removeItem(self.cage3dplot.be_plotitem)


    def toggle_satellite_model(self):
        if self.button_satellite_model.isChecked():
            self.data.config["c3dcw_draw"]["satellite_model"] = True
            self.cage3dplot.make_satellite_model()
        else:
            self.data.config["c3dcw_draw"]["satellite_model"] = False
            self.cage3dplot.removeItem(self.cage3dplot.satellite_model)


    def toggle_cage_structure(self):
        if self.button_cage_structure.isChecked():
            self.data.config["c3dcw_draw"]["cage_structure"] = True
            self.cage3dplot.make_cage_structure()
        else:
            self.data.config["c3dcw_draw"]["cage_structure"] = False
            for item in self.cage3dplot.cage_structure:
                self.cage3dplot.removeItem(item)


    def toggle_cage_illumination(self):
        if self.button_cage_illumination.isChecked():
            self.data.config["c3dcw_draw"]["cage_illumination"] = True
        else:
            self.data.config["c3dcw_draw"]["cage_illumination"] = False
            if self.data.config["c3dcw_draw"]["cage_structure"] is True:
                for item in self.cage3dplot.cage_structure:
                    self.cage3dplot.removeItem(item)
                self.cage3dplot.make_cage_structure()

    def toggle_dots(self):
        if self.button_dots.isChecked():
            self.data.config["c3dcw_draw"]["dots"] = True
            self.cage3dplot.make_dots()
        else:
            self.data.config["c3dcw_draw"]["dots"] = False
            self.cage3dplot.removeItem(self.cage3dplot.dots)


    def toggle_tails(self):
        if self.button_tails.isChecked():
            self.data.config["c3dcw_draw"]["tails"] = True
            self.cage3dplot.make_b_tail()
        else:
            self.data.config["c3dcw_draw"]["tails"] = False
            for item in self.cage3dplot.tails_plotitems:
                self.cage3dplot.removeItem(item)


    def toggle_b_components(self): # TODO WHAT TO SHOW??
        pass
        # if self.button_b_components.isChecked():
        #     self.data.config["c3dcw_draw"]["b_components"] = True
        #     self.cage3dplot.make_b_components()
        # else:
        #     self.data.config["c3dcw_draw"]["b_components"] = False
        #     for item in self.cage3dplot.b_components:
        #         self.cage3dplot.removeItem(item)



    def toggle_xy_grid(self):
        if self.button_xy_grid.isChecked():
            self.data.config["c3dcw_draw"]["xy_grid"] = True
            self.cage3dplot.make_xy_grid()
        else:
            self.data.config["c3dcw_draw"]["xy_grid"] = False
            self.cage3dplot.removeItem(self.cage3dplot.xy_grid)

    def toggle_lineplot(self):
        if self.button_lineplot.isChecked():
            self.data.config["c3dcw_draw"]["lineplot"] = True
            self.cage3dplot.make_lineplot()
        else:
            self.data.config["c3dcw_draw"]["lineplot"] = False
            self.cage3dplot.removeItem(self.cage3dplot.lineplot)

    def toggle_tripod(self):
        if self.button_tripod.isChecked():
            self.data.config["c3dcw_draw"]["tripod"] = True
            self.cage3dplot.make_tripod()
        else:
            self.data.config["c3dcw_draw"]["tripod"] = False
            for item in self.cage3dplot.tripod:
                self.cage3dplot.removeItem(item)


    def toggle_linespokes(self):
        if self.button_linespokes.isChecked():
            self.data.config["c3dcw_draw"]["linespokes"] = True
            self.cage3dplot.make_linespokes()
        else:
            self.data.config["c3dcw_draw"]["linespokes"] = False
            self.cage3dplot.removeItem(self.cage3dplot.linespokes)


    def toggle_autorotate(self):
        if self.button_autorotate.isChecked():
            self.data.config["c3dcw_draw"]["autorotate"] = True
        else:
            self.data.config["c3dcw_draw"]["autorotate"] = False

