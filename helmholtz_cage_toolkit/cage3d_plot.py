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



class Cage3DPlot(GLViewWidget):
    def __init__(self, datapool):
        super().__init__()

        # print("[DEBUG] Cage3DPlot.__init__() called")

        self.data = datapool
        self.data.cage3d_plot = self

        self.resize(720, 360)

        # Shorthands for common config settings
        self.ps = self.data.config["c3d_plotscale"]  # Plot scale
        self.c = self.data.config["ov_plotcolours"]
        self.aa = self.data.config["ov_use_antialiasing"]
        self.zo = self.data.config["c3d_cage_dimensions"]["z_offset"] * self.ps
        self.zov = array([0.0, 0.0, self.zo])

        self.tail_length = self.data.config["c3d_tail_length"]

        self.opts["center"] = QVector3D(0, 0, self.zo)
        self.setCameraPosition(distance=5*self.ps)
        # self.setCameraPosition(distance=5*self.ps, pos=(0, 0, 2.5*self.ps))


    def draw_statics(self):

        """Draws static objects into the GLViewWidget. Static objects are
        objects whose plots are independent of the schedule or simulation data,
        and so they ideally are drawn only once.

        Static objects to draw:
            - XY grid
            - ECI tripod
            - Earth meshitem
        """

        # print("[DEBUG] Cage3DPlot.draw_statics() called")

        # Generate grid
        self.make_xy_grid()

        # Generate frame tripod_components
        self.make_tripod_b()

        # Generate cage structure components
        self.make_cage_structure()

        # # Draw Earth meshitem
        # if self.data.config["ov_draw"]["earth_model"]:
        #     self.earth_meshitem = self.make_earth_meshitem()
        #     # if self.th_E != 0: # Moved to draw_simdata()
        #     #     self.earth_meshitem.rotate(self.th_E*180/pi, 0, 0, 1, local=False)
        #     self.addItem(self.earth_meshitem)


    def draw_simdata(self, i_step=0):

        if self.data.simdata is None:     # If simdata is not generated yet, skip plotting
            return 0

        self.i_step = i_step

        if self.data.config["c3d_draw"]["lineplot"]:
            self.make_lineplot()

        if self.data.config["c3d_draw"]["b_vector"]:
            self.make_b_vector()

        if self.data.config["c3d_draw"]["b_dot"]:
            self.make_b_dot()

        if self.data.config["c3d_draw"]["b_tail"]:
            self.make_b_tail()

        if self.data.config["c3d_draw"]["linespokes"]:
            self.make_linespokes()


        #
        # simdata = self.data.simdata
        #
        # self.i_step = i_step
        #
        # if simdata is None:     # If simdata is not generated yet, skip plotting
        #     return 0
        #
        # # Earth axial rotation angle at current timestep
        # self.th_Ei = (simdata["th_E0"]+i_step*simdata["dth_E"]) % (2*pi)
        #
        # # Rotate Earth meshitem
        # # Since the meshitem has no meaningful absolute position, just make it
        # # look as though it's doing stuff, i.e. at the start, just rotate
        # # backwards by
        # if self.data.config["ov_draw"]["earth_model"]:
        #     if simdata["dth_E"] != 0.:
        #         self.earth_meshitem.rotate(self.th_Ei*180/pi, 0, 0, 1, local=False)
        #
        # # ==== FRAME TRIPODS =================================================
        #
        # # Generate ECEF-frame tripod_components
        # # self.th_E0 = simdata["th_E0"]
        # # self.th_Ei = (simdata["th_E0"]+i_step*simdata["dth_E"]) % (2*pi)  # Earth axial rotation angle
        # Ri_ECEF_ECI = R_ECEF_ECI(self.th_Ei)
        # self.frame_ECEF = PGFrame3D(r=Ri_ECEF_ECI)
        # if self.data.config["ov_draw"]["tripod_ECEF"]:
        #     self.tripod_ECEF_ps = Earth().r
        #     self.frame_ECEF_plotitems = plotframe(
        #         self.frame_ECEF, self,
        #         plotscale=self.tripod_ECEF_ps, alpha=0.4, antialias=self.aa
        #     )
        #
        #
        # # Generate NED-frame tripod_components
        # xyzi = simdata["xyz"][i_step]
        #
        # # print(f"i_step: {i_step} th_Ei: {self.th_Ei*180/pi} deg")
        # # # TODO Compare timing of using conv_ECI_geoc vs. using hll->shift to ECI
        # # t0 = time()
        # # for i in range(100):
        # #     rll = conv_ECI_geoc(xyzi)
        # # print(f"rlonglat: long {round(rll[1], 3)} lat {round(rll[2], 3)} time {round(1E6*(time()-t0))} us")
        # # t0 = time()
        # # for i in range(100):
        # #     oll = array((
        # #         0,
        # #         simdata["hll"][i_step, 1],
        # #         simdata["hll"][i_step, 2]
        # #     ))
        # # print(f"hll     : long {round(oll[1], 3)} lat {round(oll[2], 3)} time {round(1E6 * (time() - t0))} us")
        #
        # # xyz_ECEF = R_ECI_ECEF(self.th_E)@self.points[self.data.i_satpos]
        # # self.rlonglat = conv_ECI_geoc(xyzi)
        # # Ri_NED_ECI = R_NED_ECI(self.rlonglat[1], self.rlonglat[2]).transpose()  # TODO Homogenise transpose
        # Ri_NED_ECI = R_NED_ECI(
        #     simdata["hll"][i_step, 1], simdata["hll"][i_step, 2]).transpose()  # TODO Homogenise transpose
        # self.frame_NED = PGFrame3D(o=xyzi, r=Ri_NED_ECI)
        # if self.data.config["ov_draw"]["tripod_NED"]:
        #     self.tripod_NED_ps = 0.4 * self.ps
        #     self.frame_NED_plotitems = plotframe(
        #         self.frame_NED, self,
        #         plotscale=self.tripod_NED_ps, alpha=0.4, antialias=self.aa
        #     )
        #
        # # Generate SI-frame tripod_components
        # Ri_ECI_SI = simdata["Rt_ECI_SI"][i_step]
        # self.frame_SI = PGFrame3D(o=xyzi, r=Ri_ECI_SI)
        # if self.data.config["ov_draw"]["tripod_SI"]:
        #     self.tripod_SI_ps = 0.4 * self.ps
        #     self.frame_SI_plotitems = plotframe(
        #         self.frame_SI, self,
        #         plotscale=self.tripod_SI_ps, alpha=0.4, antialias=self.aa
        #     )
        #
        # # Generate B-frame tripod_components
        # ab0 = simdata["angle_body0"]    # Initial rotation
        # self.ab = ab0                   # Euler angles of SI -> B transformation
        # Ri_ECI_B = R_SI_B(self.ab)@Ri_ECI_SI
        # self.frame_B = PGFrame3D(o=xyzi, r=Ri_ECI_B)
        # if self.data.config["ov_draw"]["tripod_B"]:
        #     self.tripod_B_ps = 0.25 * self.ps
        #     self.frame_B_plotitems = plotframe(
        #         self.frame_B, self,
        #         plotscale=self.tripod_B_ps, alpha=1, width=3, antialias=self.aa
        #     )
        #
        # # ==== ORBIT =========================================================
        #
        # # Draw orbit lineplot
        # if self.data.config["ov_draw"]["orbit_lineplot"]:
        #     self.orbit_lineplot = self.make_orbit_lineplot()
        #     self.addItem(self.orbit_lineplot)
        #
        # # Draw orbit scatterplot
        # if self.data.config["ov_draw"]["orbit_scatterplot"]:
        #     self.orbit_scatterplot = self.make_orbit_scatterplot()
        #     self.addItem(self.orbit_scatterplot)
        #
        # # Draw helpers (vertical coordinate lines and a XY-projected orbit)
        # if self.data.config["ov_draw"]["orbit_helpers"]:
        #     self.orbit_flatcircle, self.orbit_vlines = self.make_orbit_helpers()
        #     self.addItem(self.orbit_flatcircle)
        #     [self.addItem(vline) for vline in self.orbit_vlines]
        #
        # # ==== SATELLITE =====================================================
        #
        # # Draw representation of satellite, including highlighted helpers
        # self.satellite, self.vline_sat, self.vdot_sat = self.make_satellite()
        # self.addItem(self.satellite)
        # if self.data.config["ov_draw"]["satellite_helpers"]:
        #     self.addItem(self.vline_sat)
        #     self.addItem(self.vdot_sat)
        #
        # # Draw angular momentum unit vector
        # # self.huv_scale = 2E6
        # # self.huv_plotitem = self.make_angular_momentum_vector()
        # # self.addItem(self.huv_plotitem)
        #
        # # Draw position vector
        # if self.data.config["ov_draw"]["position_vector"]:
        #     self.pv_plotitem = self.make_position_vector()
        #     self.addItem(self.pv_plotitem)
        #
        # # Draw velocity vector
        # if self.data.config["ov_draw"]["velocity_vector"]:
        #     self.vv_scale = 0.2E-3*self.ps
        #     self.vv_plotitem = self.make_velocity_vector()
        #     self.addItem(self.vv_plotitem)
        #
        # # ==== MAGNETIC FIELD ================================================
        #
        # # Draw B vector
        # if self.data.config["ov_draw"]["B_vector"]:
        #     self.bv_scale = 1.5E-5*self.ps * 2
        #     self.bv_plotitem = self.make_B_vector()
        #     self.addItem(self.bv_plotitem)
        #
        # # Quick and dirty 3D vector plot of field elements
        # # Skip if neither scatter nor lineplots are selected, to prevent performance hog:
        # if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"] or self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
        #     print("CHECK")
        #     # Sort out some parameters
        #     self.bfg_lp_scale = 1E-5 * self.ps
        #     layers = 3
        #     h_min = 5E5
        #     h_spacing = 15E5
        #     brows = 16
        #     bcols = 8
        #
        #     B_fieldgrid_sp_plotitems = [0]*layers
        #     B_fieldgrid_lp_plotitems = [0]*layers
        #
        #     # Sequentially call make_B_fieldgrid() to make the plotitems
        #     for i in range(layers):
        #         B_fieldgrid_sp_plotitems[i], B_fieldgrid_lp_plotitems[i] = self.make_B_fieldgrid(
        #         h=h_min+i*h_spacing, rows=brows, cols=bcols, alpha=0.4)
        #
        #     # Sequentially add the plotitems, but only when configured to do so
        #     for i in range(layers):
        #         if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"]:
        #             self.addItem(B_fieldgrid_sp_plotitems[i])
        #
        #         if self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
        #             [self.addItem(bline) for bline in B_fieldgrid_lp_plotitems[i]]  # noqa
        #
        #
        # # # DEBUGGING VECTOR FOR RLONGLAT - TODO: Remove after verification complete
        # # self.vector_pos = self.make_vector_pos()
        # # self.addItem(self.vector_pos)
        #
        # # Generate NED tripod_components
        # # self.tripod_NED_components = self.make_tripod_NED()
        # # [self.addItem(comp) for comp in self.tripod_NED_components]
        #
        # # # Timer
        # # self.timer = QTimer()
        # # self.timer.timeout.connect(self.satellite_update)
        # # self.timer.start(50)  # TODO

    def draw_step(self, i_step):
        """Update the Orbital Plot with the simdata corresponding to time step
        i_step.
        """
        # print("test1", self.data.simdata["B_B"][i_step % self.data.simdata["n_step"]])
        bbi = self.data.simdata["B_B"][i_step % self.data.simdata["n_step"]]*1 + self.zov

        # print("test2", bbi)
        bbx = array((bbi[0], 0., self.zo))
        bby = array((0., bbi[1], self.zo))
        bbz = array((0., 0., bbi[2]))

        if self.data.config["c3d_draw"]["b_vector"]:
            self.b_vector_plotitem.setData(pos=[self.zov, bbi])

        if self.data.config["c3d_draw"]["b_dot"]:
            self.b_dot_plotitem.setData(pos=bbi)

        if self.data.config["c3d_draw"]["b_tail"]:
            # print("DEBUG ", type(self.data.simdata["B_B"][0]))
            # print("DEBUG ", type(self.data.simdata["B_B"]))
            # print("DEBUG ", type(self.data.simdata["B_B"]))
            # print("DEBUG ", i_step)
            # print("DEBUG ", self.tail_length)
            # print("DEBUG min", min(i_step, self.tail_length))
            # print("DEBUG i-min", i_step - min(i_step, self.tail_length))
            # print("DEBUG pt", self.data.simdata["B_B"][i_step])
            for i, segment_length in enumerate(self.tail_length):
                segment = self.data.simdata["B_B"][max(0, i_step - min(i_step, segment_length)):i_step]*1 + self.zov
                self.b_tail_plotitems[i].setData(pos=segment)

            # points_tail = self.data.simdata["B_B"][min(self.tail_length, self.i_step):self.i_step]

            # print(points_tail)

            # # Offset all the data for plotting purposes
            # for i in range(len(points_tail)):
            #     points_tail[i][2] = points_tail[i][2] + self.zo





        #
        # simdata = self.data.simdata
        #
        # # Satellite position
        # xyzi = simdata["xyz"][i_step % simdata["n_orbit_subs"]]
        # xy0i = array((xyzi[0], xyzi[1], 0.))
        #
        # th_Ei_1 = self.th_Ei    # Save "previous angle"
        # # Earth axial rotation angle at current timestep
        # self.th_Ei = (simdata["th_E0"]+i_step*simdata["dth_E"]) % (2*pi)
        #
        #
        # # # TODO TEST THEN REMOVE
        # # print(f"i_step: {i_step} xyzi: {xyzi.round()} th_Ei: {round(self.th_Ei*180/pi, 1)} deg")
        # # t0 = time()
        # # for i in range(100):
        # #     rll = conv_ECI_geoc(xyzi)
        # # print(f"rlonglat: long {round(rll[1], 3)} lat {round(rll[2], 3)} time {round(1E6*(time()-t0))} us")
        # # t0 = time()
        # # for i in range(100):
        # #     oll = array((
        # #         0,
        # #         simdata["hll"][i_step, 1],
        # #         simdata["hll"][i_step, 2]
        # #     ))
        # # print(f"hll     : long {round(oll[1], 3)} lat {round(oll[2], 3)} time {round(1E6 * (time() - t0))} us")
        #
        #
        #
        # # ==== FRAME TRIPODS
        # # Update ECEF tripod:
        # # if self.data.config["ov_rotate_earth"]:
        # #     self.th_E = (self.data.i_satpos * self.dth_E + self.th_E0) % (2 * pi)
        # Ri_ECEF_ECI = R_ECEF_ECI(self.th_Ei)
        # self.frame_ECEF.set_r(Ri_ECEF_ECI)
        # if self.data.config["ov_draw"]["tripod_ECEF"] \
        #         and self.data.config["ov_anim"]["tripod_ECEF"]:
        #     updateframe(self.frame_ECEF_plotitems, self.frame_ECEF,
        #                 plotscale=self.tripod_ECEF_ps)
        #
        # # Update NED tripod:
        # # xyz_ECEF = R_ECI_ECEF(self.th_E)@self.points[self.data.i_satpos]
        # # self.rlonglat = conv_ECI_geoc(xyzi)
        # Ri_NED_ECI = R_NED_ECI(
        #     simdata["hll"][i_step, 1],
        #     simdata["hll"][i_step, 2]).transpose()  # TODO Homogenise transpose
        # self.frame_NED.set_o(xyzi)
        # self.frame_NED.set_r(Ri_NED_ECI)
        # if self.data.config["ov_draw"]["tripod_NED"] \
        #         and self.data.config["ov_anim"]["tripod_NED"]:
        #     updateframe(self.frame_NED_plotitems, self.frame_NED,
        #                 plotscale=self.tripod_NED_ps)
        #
        # # Update SI tripod:
        # Ri_ECI_SI = simdata["Rt_ECI_SI"][i_step % simdata["n_orbit_subs"]]
        # self.frame_SI.set_o(xyzi)
        # self.frame_SI.set_r(Ri_ECI_SI)
        # if self.data.config["ov_draw"]["tripod_SI"] \
        #         and self.data.config["ov_anim"]["tripod_SI"]:
        #     updateframe(self.frame_SI_plotitems, self.frame_SI,
        #                 plotscale=self.tripod_SI_ps)
        #
        # # Update B tripod:
        # # self.ab = array([simdata["ma"][i_step], 0, 0]) # TODO WTF IS THIS
        # Ri_ECI_B = simdata["Rt_SI_B"][i_step] @ Ri_ECI_SI
        # self.frame_B.set_o(xyzi)
        # self.frame_B.set_r(Ri_ECI_B)
        # if self.data.config["ov_draw"]["tripod_B"] \
        #         and self.data.config["ov_anim"]["tripod_B"]:
        #     updateframe(self.frame_B_plotitems, self.frame_B,
        #                 plotscale=self.tripod_B_ps)
        #
        # # ==== SATELLITE ITEMS
        # if self.data.config["ov_draw"]["satellite"] \
        #         and self.data.config["ov_anim"]["satellite"]:
        #     self.satellite.setData(pos=xyzi)
        #
        # if self.data.config["ov_draw"]["satellite_helpers"] \
        #         and self.data.config["ov_anim"]["satellite_helpers"]:
        #     self.vline_sat.setData(pos=[xy0i, xyzi])
        #     self.vdot_sat.setData(pos=xy0i)
        #
        # if self.data.config["ov_draw"]["position_vector"] \
        #         and self.data.config["ov_anim"]["satellite_helpers"]:
        #     self.pv_plotitem.setData(pos=[array([0, 0, 0]), xyzi])
        #
        # if self.data.config["ov_draw"]["velocity_vector"] \
        #         and self.data.config["ov_anim"]["velocity_vector"]:
        #     v_xyzi = simdata["v_xyz"][i_step % simdata["n_orbit_subs"]]
        #     self.vv_plotitem.setData(pos=[xyzi, xyzi + v_xyzi*self.vv_scale])
        # # self.huv_plotitem.setData(pos=[xyzi, xyzi+simdata["huv"]*self.huv_scale])
        #
        # # ==== MAGNETIC FIELD
        # self.Bi = self.data.simdata["B_ECI"][i_step]
        # if self.data.config["ov_draw"]["B_vector"] \
        #         and self.data.config["ov_anim"]["B_vector"]:
        #     self.bv_plotitem.setData(pos=[xyzi, xyzi + self.Bi * self.bv_scale])
        #
        # # ==== EARTH MESHITEM
        # if (
        #         self.data.config["ov_draw"]["earth_model"]
        #         and self.data.config["ov_rotate_earth"]
        #         and self.data.config["ov_anim"]["earth_model"]
        # ):
        #     rotangle = (self.th_Ei-th_Ei_1) * 180 / pi
        #     self.earth_meshitem.rotate(rotangle, 0, 0, 1, local=False)
        #
        # # self.data.i_satpos = (self.data.i_satpos + 1) % self.data.orbit_subs

    def make_xy_grid(self):
        # Add horizontal grid
        self.xy_grid = GLGridItem(antialias=self.aa)
        self.xy_grid.setColor((255, 255, 255, 24))
        self.xy_grid.setSize(x=2*self.ps, y=2*self.ps)
        self.xy_grid.setSpacing(x=int(self.ps/10), y=int(self.ps/10))  # Comment out this line at your peril...
        self.xy_grid.setDepthValue(20)  # Ensure grid is drawn after most other features

        if self.data.config["c3d_draw"]["xy_grid"]:
            self.addItem(self.xy_grid)

    def make_tripod_b(self):
        self.frame_b = PGFrame3D(o=self.zov)
        self.tripod_b = plotframe2(
            self.frame_b,
            plotscale=0.25 * self.ps, alpha=0.4, antialias=self.aa
        )
        if self.data.config["c3d_draw"]["tripod_b"]:
            for item in self.tripod_b:
                self.addItem(item)

    #
    # def make_earth_meshitem(self, alpha=1.0):
    #     sr = self.data.config["ov_earth_model_resolution"]
    #
    #     mesh = MeshData.sphere(rows=sr[0], cols=sr[1], radius=Earth().r)
    #
    #     ec = self.data.config["ov_earth_model_colours"]
    #
    #     # Pre-allocate empty array for storing colour data for each mesh triangle
    #     colours = ones((mesh.faceCount(), 4), dtype=float)
    #
    #     # Add ocean base layer
    #     colours[:, 0:3] = hex2rgb(ec["ocean"])
    #
    #     # Add polar ice
    #     pole_line = (int(0.15*sr[0])*sr[1]+1, (int(sr[0]*0.75)*sr[1])+1)
    #     colours[:pole_line[0], 0:3] = hex2rgb(ec["ice"])
    #     colours[pole_line[1]:, 0:3] = hex2rgb(ec["ice"])
    #
    #     # Add landmasses
    #     tropic_line = (int(0.25*sr[0])*sr[1]+1, (int(sr[0]*0.65)*sr[1])+1)
    #     i_land = []
    #
    #     for i_f in range(pole_line[0], pole_line[1], 1):
    #
    #         # Determine chance of land (increases for adjacent land tiles)
    #         p_land = 0.2
    #         if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
    #             p_land += 0.4
    #         if i_f-1 in i_land or i_f+1 in i_land:
    #             p_land += 0.2
    #
    #         # Flip a coin to determine land
    #         if random() <= p_land:
    #             i_land.append(i_f)
    #             if tropic_line[0] <= i_f <= tropic_line[1] and random() >= 0.5:
    #                 colours[i_f, 0:3] = hex2rgb(ec["green2"])
    #             else:
    #                 colours[i_f, 0:3] = hex2rgb(ec["green1"])
    #
    #     # Add cloud cover
    #     i_cloud = []
    #     for i_f in range(len(colours)):
    #         # Determine chance of cloud
    #         p_cloud = 0.1
    #         if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
    #             p_cloud += 0.3
    #
    #         if random() <= p_cloud:
    #             i_cloud.append(i_f)
    #             colours[i_f, 0:3] = hex2rgb(ec["cloud"])
    #
    #     # Apply alpha (does not work)
    #     colours[:, 3] = alpha
    #
    #     # Apply the colour data to the mesh triangles
    #     mesh.setFaceColors(colours)
    #
    #     # Embed the data into a GLMeshItem (that Qt can work with)
    #     meshitem = GLMeshItem(
    #         meshdata=mesh,
    #         smooth=self.data.config["ov_earth_model_smoothing"],
    #         computeNormals=True,
    #         shader="shaded",
    #     )
    #
    #     meshitem.setDepthValue(-2)
    #
    #     return meshitem

    def make_cage_structure(self):
        self.cage_structure = []

        scale = self.ps
        dim_x = self.data.config["c3d_cage_dimensions"]["x"]
        dim_y = self.data.config["c3d_cage_dimensions"]["y"]
        dim_z = self.data.config["c3d_cage_dimensions"]["z"]
        dim_t = self.data.config["c3d_cage_dimensions"]["t"]
        s = self.data.config["c3d_cage_dimensions"]["spacing"]

        m = [1, 1, -1, -1, 1, 1]

        alpha = self.data.config["c3d_cage_alpha"]

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

        if self.data.config["c3d_draw"]["cage_structure"]:
            for element in self.cage_structure:
                self.addItem(element)

    # def make_lineplot(self):
    #
    #     points = self.data.simdata["B_B"][:]
    #
    #     # Offset all the data for plotting purposes
    #     for i in range(len(points)):
    #         points[i][2] = points[i][2] + self.zo
    #
    #     lineplot = GLLinePlotItem(
    #         pos=points,
    #         # color=self.c[self.data.config["c3d_preferred_colour"]],
    #         color=(0, 1, 1, 0.25),
    #         width=2,
    #         antialias=self.data.config["ov_use_antialiasing"]
    #     )
    #     lineplot.setDepthValue(1)
    #     return lineplot

    def make_lineplot(self):

        points = self.data.simdata["B_B"][:]*1

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.data.config["c3d_preferred_colour"]],
            color=(0, 1, 1, 0.25),
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.lineplot.setDepthValue(1)
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
        self.addItem(self.b_vector_plotitem)


    def make_b_dot(self):

        point = self.data.simdata["B_B"][self.i_step]*1 + self.zov
        self.b_dot_plotitem = GLScatterPlotItem(
            pos=point,
            color=(0.0, 1.0, 1.0, 1),
            size=8,
            pxMode=True)
        self.b_dot_plotitem.setDepthValue(2)
        self.addItem(self.b_dot_plotitem)


    def make_b_tail(self):

        self.b_tail_plotitems = []

        # la = self.data.config["c3d_line_alpha"]
        # alphas = [i/len(self.tail_length)*(1-la)+la for i in range(len(self.tail_length), 0, -1)]
        intensity = [i/len(self.tail_length) for i in range(len(self.tail_length), 0, -1)]
        # print("DEBUG alphas", intensity)

        for i, segment_length in enumerate(self.tail_length):
            segment = self.data.simdata["B_B"][self.i_step-min(self.i_step, segment_length):self.i_step]*1

            self.b_tail_plotitems.append(GLLinePlotItem(
                pos=segment,
                # color=self.c[self.data.config["c3d_preferred_colour"]],
                color=(intensity[i], 1, 1, 0.1),
                width=3,
                antialias=self.data.config["ov_use_antialiasing"]
            ))
            self.b_tail_plotitems[i].setDepthValue(1)

        # Offset all the data for plotting purposes
        # for i in range(len(points)):
        #     points[i][2] = points[i][2]+self.zo

        for i, element in enumerate(self.b_tail_plotitems):
            self.addItem(element)

    # def make_line_spokes(self):
    #     spokes = []
    #     for i in range(self.data.simdata["n_step"]):
    #         spoke = GLLinePlotItem(
    #             pos=[3/4*self.data.simdata["B_B"][i]+array([0., 0., self.zo/4]), self.data.simdata["B_B"][i]],
    #             # pos=[array([0.0, 0.0, self.zo]), self.data.simdata["B_B"][i]],
    #             color=(0.5, 0.5, 0.5, 0.2),
    #             # antialias=self.data.config["ov_use_antialiasing"],
    #             width=1)
    #         spoke.setDepthValue(0)
    #         spokes.append(spoke)
    #     return spokes

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
        self.addItem(self.linespokes)

    # def make_orbit_helpers(self):
        # # Add flat circle
        # # Always patch this circle:
        # points_flatZ = vstack([self.data.simdata["xyz"][:],
        #                        self.data.simdata["xyz"][0]])
        #
        # # Flatten Z-coordinates
        # points_flatZ[:, 2] = 0
        #
        # flatcircle = GLLinePlotItem(
        #     pos=points_flatZ,
        #     color=(1, 1, 1, 0.2),
        #     width=1,
        #     antialias=self.data.config["ov_use_antialiasing"])
        # flatcircle.setDepthValue(0)
        #
        # # Add vlines
        # vlines = []
        # for i in range(len(self.data.simdata["xyz"])):
        #     vline = GLLinePlotItem(
        #         pos=[points_flatZ[i], self.data.simdata["xyz"][i]],
        #         color=(1, 1, 1, 0.1),
        #         antialias=self.data.config["ov_use_antialiasing"],
        #         width=1)
        #     vline.setDepthValue(0)
        #     vlines.append(vline)
        #
        # return flatcircle, vlines

    # def make_satellite(self):
    #     # Draw satellite
    #     point = self.data.simdata["xyz"][self.i_step]
    #     point_flatZ = array([point[0], point[1], 0])
    #     sat = GLScatterPlotItem(
    #         pos=point,
    #         color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
    #         size=8,
    #         pxMode=True)
    #     sat.setDepthValue(1)
    #
    #     vline_sat = GLLinePlotItem(
    #         pos=[point_flatZ, point],
    #         color=(1.0, 1.0, 1.0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=1)
    #
    #     vline_sat.setDepthValue(1)
    #
    #     vdot_sat = GLScatterPlotItem(
    #         pos=[point_flatZ, point],
    #         color=(1.0, 1.0, 1.0, 0.8),
    #         size=3,
    #         pxMode=True)
    #     vdot_sat.setDepthValue(1)
    #
    #     return sat, vline_sat, vdot_sat
    #
    # def make_angular_momentum_vector(self):
    #     base = self.data.simdata["xyz"][self.i_step]
    #     tip = base + self.huv*self.huv_scale
    #
    #     vector = GLLinePlotItem(
    #         pos=[base, tip],
    #         color=(1.0, 1.0, 0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=3)
    #     vector.setDepthValue(0)
    #     return vector

    # def make_velocity_vector(self):
    #
    #     base = self.data.simdata["xyz"][self.i_step]
    #     tip = base + self.data.simdata["v_xyz"][self.i_step]*self.vv_scale
    #
    #     vector = GLLinePlotItem(
    #         pos=[base, tip],
    #         color=(1.0, 1.0, 0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=3)
    #     vector.setDepthValue(0)
    #     return vector

    # def make_position_vector(self):
    #
    #     base = array([0, 0, 0])
    #     tip = self.data.simdata["xyz"][self.i_step]
    #
    #     vector = GLLinePlotItem(
    #         pos=[base, tip],
    #         color=(1.0, 1.0, 0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=2)
    #     vector.setDepthValue(0)
    #     return vector
    #
    # def make_B_vector(self):
    #     # Calculate magnetic field vector
    #     # _, _, _, bx, by, bz, _ = igrf_value(
    #     #     180/pi*self.rlonglat[2],                         # Latitude [deg]
    #     #     180/pi*wrap(self.rlonglat[1]-self.th_E, 2*pi),   # Longitude (ECEF) [deg]
    #     #     1E-3*(self.rlonglat[0]-self.data.orbit.body.r),  # Altitude [km]
    #     #     self.year)                                       # Date formatted as decimal year
    #
    #     self.Bi = self.data.simdata["B_ECI"][self.i_step]
    #
    #     # print("[OLD] in:", [180/pi*self.rlonglat[2],
    #     #                     180/pi*wrap(self.rlonglat[1]-self.th_E, 2*pi),
    #     #                     1E-3 * (self.rlonglat[0] - self.data.orbit.body.r),
    #     #                     self.year])
    #     # print("[OLD] B", [bx, by, bz])
    #
    #     # print("B_NED:", B_NED)
    #     # print("B_ECI:", self.Bi)
    #
    #     base = self.data.simdata["xyz"][self.i_step]
    #     tip = base + self.Bi*self.bv_scale
    #
    #     vector = GLLinePlotItem(
    #         pos=[base, tip],
    #         color=(0.0, 1.0, 1.0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=6)
    #     vector.setDepthValue(0)
    #     return vector
    #
    #
    # def make_B_fieldgrid(self, h=5E5, rows=16, cols=16, alpha=0.5):
    #     t0 = time()
    #
    #     r = Earth().r + h
    #
    #     xyz = MeshData.sphere(rows=rows, cols=cols, radius=r).vertexes()
    #     print("Number of fieldgrid points:", len(xyz))
    #
    #     if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"]:
    #         scatterplot = GLScatterPlotItem(
    #             pos=xyz,
    #             color=(0.0, 1.0, 1.0, alpha),
    #             size=3,
    #             pxMode=True)
    #         scatterplot.setDepthValue(0)
    #     else:
    #         scatterplot = None
    #
    #     if self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
    #         lineplots = []
    #         for p in xyz:
    #             p_rlonglat = conv_ECI_geoc(p)
    #
    #             _, _, _, bx, by, bz, _ = igrf_value(
    #                 180 / pi * p_rlonglat[2],                            # Latitude [deg]
    #                 180 / pi * wrap(p_rlonglat[1] - self.th_Ei, 2 * pi),  # Longitude (ECEF) [deg]
    #                 1E-3 * r,                                            # Altitude [km]
    #                 self.data.config["orbital_default_generation_parameters"]["date0"])  # Date formatted as decimal year
    #
    #             B_p = R_NED_ECI(p_rlonglat[1], p_rlonglat[2]) @ array([bx, by, bz])
    #
    #
    #             b_line = GLLinePlotItem(
    #                 pos=[p, p+B_p*self.bfg_lp_scale],
    #                 color=(0.0, 1.0, 1.0, alpha),
    #                 antialias=self.data.config["ov_use_antialiasing"],
    #                 width=1)
    #             b_line.setDepthValue(0)
    #             lineplots.append(b_line)
    #     else:
    #         lineplots = None
    #
    #     t1 = time()
    #     print(f"[DEBUG] make_B_fieldgrid() time: {round((t1-t0)*1E6,1)} us")
    #
    #     return scatterplot, lineplots
    #
    # def make_vector_pos(self):  # TODO: Remove (after verification complete)
    #     point = self.points[self.data.i_satpos]
    #
    #     rlonglat = conv_ECEF_geoc(point)
    #     xcalc = rlonglat[0] * cos(rlonglat[1]) * sin(pi / 2 - rlonglat[2])
    #     ycalc = rlonglat[0] * sin(rlonglat[1]) * sin(pi / 2 - rlonglat[2])
    #     zcalc = rlonglat[0] * cos(pi / 2 - rlonglat[2])
    #
    #     vector = GLLinePlotItem(
    #         pos=[array([0, 0, 0]), array([xcalc, ycalc, zcalc])],
    #         color=(1.0, 1.0, 0, 0.8),
    #         antialias=self.data.config["ov_use_antialiasing"],
    #         width=1)
    #     vector.setDepthValue(0)
    #     return vector

class Cage3DPlotButtons(QGroupBox):
    """Description"""
    def __init__(self, cage3dplot, datapool) -> None:
        super().__init__()

        self.cage3dplot = cage3dplot
        self.data = datapool

        self.layout0 = QGridLayout()
        self.buttons = []

        # Generate buttons

        self.button_xy_grid = QPushButton(QIcon("./assets/icons/feather/grid.svg"), "")
        self.setup(self.button_xy_grid, "xy_grid", label="XY")
        self.button_xy_grid.toggled.connect(self.toggle_xy_grid)

        self.button_tripod_b = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_b, "tripod_b", label="B")
        self.button_tripod_b.toggled.connect(self.toggle_tripod_b)

        self.button_cage_structure = QPushButton(QIcon("./assets/icons/feather/box.svg"), "")
        self.setup(self.button_cage_structure, "tripod_b")
        self.button_cage_structure.toggled.connect(self.toggle_cage_structure)

        self.button_b_dot = QPushButton(QIcon("./assets/icons/dot.svg"), "")
        self.setup(self.button_b_dot, "b_dot")
        self.button_b_dot.toggled.connect(self.toggle_b_dot)

        self.button_b_vector = QPushButton(QIcon("./assets/icons/feather/arrow-up-right.svg"), "")
        self.setup(self.button_b_vector, "b_vector")
        self.button_b_vector.toggled.connect(self.toggle_b_vector)

        self.button_b_tail = QPushButton(QIcon("./assets/icons/tail.svg"), "")
        self.setup(self.button_b_tail, "b_tail")
        self.button_b_tail.toggled.connect(self.toggle_b_tail)

        self.button_lineplot = QPushButton(QIcon("./assets/icons/wave.svg"), "")
        self.setup(self.button_lineplot, "lineplot")
        self.button_lineplot.toggled.connect(self.toggle_lineplot)

        self.button_linespokes = QPushButton(QIcon("./assets/icons/feather/bar-chart.svg"), "")
        self.setup(self.button_linespokes, "linespokes")
        self.button_linespokes.toggled.connect(self.toggle_linespokes)


        # self.setStyleSheet(self.data.config["stylesheet_groupbox_smallmargins_notitle"])
        self.setLayout(self.layout0)
        self.layout0.setSizeConstraint(QLayout.SetMinimumSize)
        self.setMaximumSize(32, 320)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.layout0.setVerticalSpacing(1)
        self.layout0.setColumnStretch(0, 0)
        self.layout0.setColumnStretch(1, 0)


    def setup(self, button, reference: str, label=""):
        """A shorthand function to inherit the 'checked' properties based on
        the visibility of various plot items as defined in the config file.
        This must be done before the toggled() action is connected, in order
        to prevent the toggled () action being triggered and causing plot
        elements to be redrawn unnecessarily.
        """
        button.setCheckable(True)
        if self.data.config["c3d_draw"][reference] is True:
            button.setChecked(True)
        button.setFixedSize(QSize(32, 32))
        button.setIconSize(QSize(24, 24))
        self.layout0.addWidget(button, len(self.buttons), 0)
        self.layout0.addWidget(QLabel(label), len(self.buttons), 1)
        self.buttons.append(button)


    def toggle_xy_grid(self):
        if self.button_xy_grid.isChecked():
            self.data.config["c3d_draw"]["xy_grid"] = True
            self.cage3dplot.make_xy_grid()
        else:
            self.data.config["c3d_draw"]["xy_grid"] = False
            self.cage3dplot.removeItem(self.cage3dplot.xy_grid)

    def toggle_tripod_b(self):
        if self.button_tripod_b.isChecked():
            self.data.config["c3d_draw"]["tripod_b"] = True
            self.cage3dplot.make_tripod_b()
        else:
            self.data.config["c3d_draw"]["tripod_b"] = False
            for item in self.cage3dplot.tripod_b:
                self.cage3dplot.removeItem(item)

    def toggle_cage_structure(self):
        if self.button_cage_structure.isChecked():
            self.data.config["c3d_draw"]["cage_structure"] = True
            self.cage3dplot.make_cage_structure()
        else:
            self.data.config["c3d_draw"]["cage_structure"] = False
            for item in self.cage3dplot.cage_structure:
                self.cage3dplot.removeItem(item)

    def toggle_b_dot(self):
        if self.button_b_dot.isChecked():
            self.data.config["c3d_draw"]["b_dot"] = True
            self.cage3dplot.make_b_dot()
        else:
            self.data.config["c3d_draw"]["b_dot"] = False
            self.cage3dplot.removeItem(self.cage3dplot.b_dot_plotitem)

    def toggle_lineplot(self):
        if self.button_lineplot.isChecked():
            self.data.config["c3d_draw"]["lineplot"] = True
            self.cage3dplot.make_lineplot()
        else:
            self.data.config["c3d_draw"]["lineplot"] = False
            self.cage3dplot.removeItem(self.cage3dplot.lineplot)

    def toggle_linespokes(self):
        if self.button_linespokes.isChecked():
            self.data.config["c3d_draw"]["linespokes]"] = True
            self.cage3dplot.make_linespokes()
        else:
            self.data.config["c3d_draw"]["linespokes"] = False
            self.cage3dplot.removeItem(self.cage3dplot.linespokes)

    def toggle_b_vector(self):
        if self.button_b_vector.isChecked():
            self.data.config["c3d_draw"]["b_vector"] = True
            self.cage3dplot.make_b_vector()
        else:
            self.data.config["c3d_draw"]["b_vector"] = False
            self.cage3dplot.removeItem(self.cage3dplot.b_vector_plotitem)

    def toggle_b_tail(self):
        if self.button_b_tail.isChecked():
            self.data.config["c3d_draw"]["b_tail"] = True
            self.cage3dplot.make_b_tail()
        else:
            self.data.config["c3d_draw"]["b_tail"] = False
            for item in self.cage3dplot.b_tail_plotitems:
                self.cage3dplot.removeItem(item)
