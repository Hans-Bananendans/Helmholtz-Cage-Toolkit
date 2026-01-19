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
    plotgrid, plotpoint, plotpoints, plotvector, plotframe, plotframe2,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
    sign, wrap, norm3d, uv3d,
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



class OrbitalPlot(GLViewWidget):
    def __init__(self, datapool):
        super().__init__()

        # print("[DEBUG] OrbitalPlot.__init__() called")

        self.data = datapool
        self.data.orbital_plot = self

        self.resize(720, 360)

        # Shorthands for common config settings
        self.ps = self.data.config["ov_plotscale"]  # Plot scale
        self.psm = self.data.config["ov_plotscale_mult"]  # Plot scale multiplier
        self.c = self.data.config["ov_plotcolours"]
        self.aa = self.data.config["ov_use_antialiasing"]

        self.setCameraPosition(
            distance=self.psm*self.ps,
            azimuth=self.data.config["ov_azimuth"],
            elevation=self.data.config["ov_elevation"],
        )

    def draw_statics(self):
        """Draws static objects into the GLViewWidget. Static objects are
        objects whose plots are independent of the schedule or simulation data,
        and so they ideally are drawn only once.

        Static objects to draw:
            - XY grid
            - ECI tripod
            - Earth model
        """

        # Generate grid
        self.make_xy_grid()

        # Generate ECI-frame tripod_components
        self.make_tripod_ECI()

        # Draw Earth meshitem
        self.make_earth_model()


    def draw_simdata(self, i_step=0):

        simdata = self.data.simdata

        self.i_step = i_step

        if simdata is None:     # If simdata is not generated yet, skip plotting
            return 0

        # Earth axial rotation angle at current timestep
        self.th_Ei = (simdata["th_E0"]+i_step*simdata["dth_E"]) % (2*pi)

        # Rotate Earth meshitem
        # Since the meshitem has no meaningful absolute position, just make it
        # look as though it's doing stuff, i.e. at the start, just rotate
        # backwards by theta_E,i
        if self.data.config["ov_draw"]["earth_model"]:
            if simdata["dth_E"] != 0.:
                self.earth_model.rotate(self.th_Ei*180/pi, 0, 0, 1, local=False)

        # ==== FRAME TRIPODS =================================================

        # Generate ECEF-frame tripod_components
        self.make_tripod_ECEF()

        # Generate NED-frame tripod_components
        self.make_tripod_NED()

        # Generate SI-frame tripod_components
        self.make_tripod_SI()

        # Generate B-frame tripod_components
        self.make_tripod_B()


        # ==== ORBIT =========================================================

        # Draw orbit lineplot
        self.make_orbit_lineplot()

        # Draw orbit scatterplot
        self.make_orbit_scatterplot()

        # Draw helpers (vertical coordinate lines and a XY-projected orbit)
        self.make_orbit_helpers()


        # ==== SATELLITE =====================================================

        # Draw representation of satellite, including highlighted helpers
        self.make_satellite()
        self.make_satellite_helpers()
        self.make_satellite_model()

        # Draw angular momentum unit vector
        self.make_angular_momentum_vector()

        # Draw position vector
        self.vv_scale = 4E-5 * self.ps
        self.make_position_vector()

        # Draw velocity vector
        self.make_velocity_vector()


        # ==== MAGNETIC FIELD ================================================

        # Draw B vector
        self.bv_scale = 1.5E-2 * self.ps
        self.make_b_vector()

        self.make_b_lineplot()
        self.make_b_linespokes()
        # if self.data.config["ov_draw"]["B_vector"]:
        #     self.bv_plotitem = self.make_B_vector()
        #     self.addItem(self.bv_plotitem)


        # Quick and dirty 3D vector plot of field elements
        # Skip if neither scatter nor lineplots are selected, to prevent performance hog:
        self.make_b_fieldgrid()


    def draw_step(self, i_step):
        """Update the Orbital Plot with the simdata corresponding to time step
        i_step.
        """
        simdata = self.data.simdata

        # Satellite position
        xyzi = simdata["xyz"][i_step % simdata["n_orbit_subs"]]
        xy0i = array((xyzi[0], xyzi[1], 0.))

        th_Ei_1 = self.th_Ei    # Save "previous angle"
        # Earth axial rotation angle at current timestep
        self.th_Ei = (simdata["th_E0"]+i_step*simdata["dth_E"]) % (2*pi)


        # ==== FRAME TRIPODS
        # Update ECEF tripod:
        Ri_ECEF_ECI = R_ECEF_ECI(self.th_Ei)
        self.frame_ECEF.set_r(Ri_ECEF_ECI)
        if self.data.config["ov_draw"]["tripod_ECEF"]:
            updateframe(self.tripod_ECEF, self.frame_ECEF,
                        plotscale=self.tripod_ECEF_ps)

        # Update NED tripod:
        Ri_NED_ECI = R_NED_ECI(
            # Longitude, with correction for the instantaneous Earth rotation
            simdata["hll"][i_step, 1] * pi / 180 + self.th_Ei,
            simdata["hll"][i_step, 2] * pi / 180  # Latitude
        ).transpose()
        self.frame_NED.set_o(xyzi)
        self.frame_NED.set_r(Ri_NED_ECI)
        if self.data.config["ov_draw"]["tripod_NED"]:
            updateframe(self.tripod_NED, self.frame_NED,
                        plotscale=self.tripod_NED_ps)

        # Update SI tripod:
        Ri_ECI_SI = simdata["Rt_ECI_SI"][i_step % simdata["n_orbit_subs"]]
        self.frame_SI.set_o(xyzi)
        self.frame_SI.set_r(Ri_ECI_SI)
        if self.data.config["ov_draw"]["tripod_SI"]:
            updateframe(self.tripod_SI, self.frame_SI,
                        plotscale=self.tripod_SI_ps)

        # Update B tripod:
        Ri_ECI_B = simdata["Rt_SI_B"][i_step] @ Ri_ECI_SI
        self.frame_B.set_o(xyzi)
        self.frame_B.set_r(Ri_ECI_B)
        if self.data.config["ov_draw"]["tripod_B"]:
            updateframe(self.tripod_B, self.frame_B,
                        plotscale=self.tripod_B_ps)


        # ==== SATELLITE ITEMS
        if self.data.config["ov_draw"]["satellite"]:
            self.satellite.setData(pos=xyzi)

        if self.data.config["ov_draw"]["satellite_helpers"]:
            self.satellite_helpers[0].setData(pos=[xy0i, xyzi])
            self.satellite_helpers[1].setData(pos=xy0i)

        if self.data.config["ov_draw"]["satellite_model"]:
            model_points = self.satellite_model_points0 @ Ri_ECI_B + xyzi
            self.satellite_model.setData(pos=model_points)

        if self.data.config["ov_draw"]["position_vector"]:
            self.position_vector.setData(pos=[array([0, 0, 0]), xyzi])

        if self.data.config["ov_draw"]["velocity_vector"]:
            v_xyzi = simdata["v_xyz"][i_step % simdata["n_orbit_subs"]]
            self.velocity_vector.setData(pos=[xyzi, xyzi + v_xyzi*self.vv_scale])

        # ==== MAGNETIC FIELD
        self.Bi = self.data.simdata["B_ECI"][i_step]
        if self.data.config["ov_draw"]["b_vector"]:
            self.b_vector.setData(pos=[xyzi, xyzi + self.Bi * self.bv_scale])

        # ==== EARTH MESHITEM
        if (self.data.config["ov_draw"]["earth_model"]
                and self.data.config["ov_rotate_earth"]
            ):
            rotangle = (self.th_Ei-th_Ei_1) * 180 / pi
            self.earth_model.rotate(rotangle, 0, 0, 1, local=False)

        # # ==== AUTO ROTATION -> MOVED TO WINDOW LEVEL
        # if self.data.config["ov_draw"]["autorotate"]:
        #     angle = self.data.config["ov_autorotate_angle"]
        #     self.setCameraPosition(
        #         azimuth=(self.opts["azimuth"] + angle) % 360
        #     )


    def make_tripod_ECI(self):
        self.frame_ECI = PGFrame3D()
        self.tripod_ECI = plotframe2(
            self.frame_ECI,
            plotscale=1.5*self.ps, alpha=0.4, antialias=self.aa
        )
        if self.data.config["ov_draw"]["tripod_ECI"]:
            for item in self.tripod_ECI:
                self.addItem(item)


    def make_tripod_ECEF(self):
        Ri_ECEF_ECI = R_ECEF_ECI(self.th_Ei)
        self.frame_ECEF = PGFrame3D(r=Ri_ECEF_ECI)
        self.tripod_ECEF_ps = Earth().r
        self.tripod_ECEF = plotframe2(
            self.frame_ECEF,
            plotscale=self.tripod_ECEF_ps, alpha=0.4, antialias=self.aa
        )
        if self.data.config["ov_draw"]["tripod_ECEF"]:
            for item in self.tripod_ECEF:
                self.addItem(item)


    def make_tripod_NED(self):
        simdata = self.data.simdata
        Ri_NED_ECI = R_NED_ECI(
            simdata["hll"][self.i_step, 1],
            simdata["hll"][self.i_step, 2]
        ).transpose()
        self.frame_NED = PGFrame3D(
            o=simdata["xyz"][self.i_step],
            r=Ri_NED_ECI
        )
        self.tripod_NED_ps = 0.4 * self.ps
        self.tripod_NED = plotframe2(
            self.frame_NED,
            plotscale=self.tripod_NED_ps, alpha=0.4, antialias=self.aa
        )

        if self.data.config["ov_draw"]["tripod_NED"]:
            for item in self.tripod_NED:
                self.addItem(item)


    def make_tripod_SI(self):
        simdata = self.data.simdata
        Ri_ECI_SI = simdata["Rt_ECI_SI"][self.i_step]
        self.frame_SI = PGFrame3D(
            o=simdata["xyz"][self.i_step % simdata["n_orbit_subs"]],
            r=Ri_ECI_SI
        )
        self.tripod_SI_ps = 0.4 * self.ps
        self.tripod_SI = plotframe2(
            self.frame_SI,
            plotscale=self.tripod_SI_ps, alpha=0.4, antialias=self.aa
        )

        if self.data.config["ov_draw"]["tripod_SI"]:
            for item in self.tripod_SI:
                self.addItem(item)


    def make_tripod_B(self):
        simdata = self.data.simdata

        # Initial Euler angles of SI -> B transformation:
        self.ab0 = simdata["angle_body0"]
        Ri_ECI_B = R_SI_B(self.ab0) @ simdata["Rt_ECI_SI"][self.i_step]
        self.frame_B = PGFrame3D(
            o=simdata["xyz"][self.i_step % simdata["n_orbit_subs"]],
            r=Ri_ECI_B
        )
        self.tripod_B_ps = 0.25 * self.ps
        self.tripod_B = plotframe2(
            self.frame_B,
            plotscale=self.tripod_B_ps, alpha=1, width=4, antialias=self.aa
        )

        if self.data.config["ov_draw"]["tripod_B"]:
            for item in self.tripod_B:
                self.addItem(item)


    def make_xy_grid(self):
        # Add horizontal grid
        self.xy_grid = GLGridItem(antialias=self.aa)
        self.xy_grid.setColor((255, 255, 255, 24))
        self.xy_grid.setSpacing(x=self.ps/10, y=self.ps/10)  # Comment out this line at your peril...
        self.xy_grid.setSize(x=2*self.ps, y=2*self.ps)
        self.xy_grid.setDepthValue(20)  # Ensure grid is drawn after most other features

        if self.data.config["ov_draw"]["xy_grid"]:
            self.addItem(self.xy_grid)


    def make_earth_model(self, alpha=1.0):
        sr = self.data.config["ov_earth_model_resolution"]

        mesh = MeshData.sphere(rows=sr[0], cols=sr[1], radius=Earth().r)

        ec = self.data.config["ov_earth_model_colours"]

        # Pre-allocate empty array for storing colour data for each mesh triangle
        colours = ones((mesh.faceCount(), 4), dtype=float)

        # Add ocean base layer
        colours[:, 0:3] = hex2rgb(ec["ocean"])

        # Add polar ice
        pole_line = (int(0.15*sr[0])*sr[1]+1, (int(sr[0]*0.75)*sr[1])+1)
        colours[:pole_line[0], 0:3] = hex2rgb(ec["ice"])
        colours[pole_line[1]:, 0:3] = hex2rgb(ec["ice"])

        # Add landmasses
        tropic_line = (int(0.25*sr[0])*sr[1]+1, (int(sr[0]*0.65)*sr[1])+1)
        i_land = []

        for i_f in range(pole_line[0], pole_line[1], 1):

            # Determine chance of land (increases for adjacent land tiles)
            p_land = 0.2
            if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
                p_land += 0.4
            if i_f-1 in i_land or i_f+1 in i_land:
                p_land += 0.2

            # Flip a coin to determine land
            if random() <= p_land:
                i_land.append(i_f)
                if tropic_line[0] <= i_f <= tropic_line[1] and random() >= 0.5:
                    colours[i_f, 0:3] = hex2rgb(ec["green2"])
                else:
                    colours[i_f, 0:3] = hex2rgb(ec["green1"])

        # Add cloud cover
        i_cloud = []
        for i_f in range(len(colours)):
            # Determine chance of cloud
            p_cloud = 0.1
            if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
                p_cloud += 0.3

            if random() <= p_cloud:
                i_cloud.append(i_f)
                colours[i_f, 0:3] = hex2rgb(ec["cloud"])

        # Apply alpha (does not work)
        colours[:, 3] = alpha

        # Apply the colour data to the mesh triangles
        mesh.setFaceColors(colours)

        # Embed the data into a GLMeshItem (that Qt can work with)
        self.earth_model = GLMeshItem(
            meshdata=mesh,
            smooth=self.data.config["ov_earth_model_smoothing"],
            computeNormals=True,
            shader="shaded",
            # shader="balloon",
            glOptions="opaque",
        )
        self.earth_model.setDepthValue(-2)

        if self.data.config["ov_draw"]["earth_model"]:
            self.addItem(self.earth_model)


    def make_orbit_lineplot(self):
        # Depending on 'orbit_endpatching' setting, patch gap at pericentre
        if self.data.config["ov_endpatching"]:
            points = vstack([self.data.simdata["xyz"][:],
                             self.data.simdata["xyz"][0]])
        else:
            points = simdata["xyz"][:]
        self.orbit_lineplot = GLLinePlotItem(
            pos=points,
            color=self.c[self.data.config["ov_preferred_colour"]],
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.orbit_lineplot.setDepthValue(0)

        if self.data.config["ov_draw"]["orbit_lineplot"]:
            self.addItem(self.orbit_lineplot)


    def make_orbit_scatterplot(self):

        self.orbit_scatterplot = GLScatterPlotItem(
            pos=self.data.simdata["xyz"],
            color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
            size=4,
            pxMode=True)
        self.orbit_scatterplot.setDepthValue(0)

        if self.data.config["ov_draw"]["orbit_scatterplot"]:
            self.addItem(self.orbit_scatterplot)


    def make_orbit_helpers(self):

        vline_points = []
        flatcircle_points = []

        for i in range(len(self.data.simdata["xyz"])):
            [x, y, z] = self.data.simdata["xyz"][i]
            vline_points.append(array([x, y, 0.0]))
            vline_points.append(array([x, y, z]))
            vline_points.append(array([x, y, 0.0]))

            flatcircle_points.append(array([x, y, 0.0]))

        # Patch the circle
        [x, y, z] = self.data.simdata["xyz"][0]
        vline_points.append(array([x, y, 0.0]))
        flatcircle_points.append(array([x, y, 0.0]))

        self.orbit_helpers = []

        # Add vlines
        self.orbit_helpers.append(GLLinePlotItem(
            pos=vline_points,
            color=(1, 1, 1, 0.05),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        )

        self.orbit_helpers.append(GLLinePlotItem(
            pos=flatcircle_points,
            color=(1, 1, 1, 0.2),
            width=1,
            antialias=self.data.config["ov_use_antialiasing"])
        )
        [item.setDepthValue(0) for item in self.orbit_helpers]

        if self.data.config["ov_draw"]["orbit_helpers"]:
            for item in self.orbit_helpers:
                self.addItem(item)


    def make_satellite(self):
        # Draw satellite
        point = self.data.simdata["xyz"][self.i_step]*1
        point_flatZ = array([point[0], point[1], 0])
        self.satellite = GLScatterPlotItem(
            pos=point,
            color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
            size=8,
            pxMode=True)
        self.satellite.setDepthValue(1)

        if self.data.config["ov_draw"]["satellite"]:
            self.addItem(self.satellite)


    def make_satellite_helpers(self):
        # Draw satellite
        point = self.data.simdata["xyz"][self.i_step]*1
        point_flatZ = array([point[0], point[1], 0])

        self.satellite_helpers = []

        self.satellite_helpers.append(GLLinePlotItem(
            pos=[point_flatZ, point],
            color=(1.0, 1.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        )
        self.satellite_helpers[0].setDepthValue(1)

        self.satellite_helpers.append(GLScatterPlotItem(
            pos=[point_flatZ, point],
            color=(1.0, 1.0, 1.0, 0.8),
            size=3,
            pxMode=True)
        )
        self.satellite_helpers[1].setDepthValue(1)

        if self.data.config["ov_draw"]["orbit_helpers"]:
            for item in self.satellite_helpers:
                self.addItem(item)

    def make_satellite_model(self):
        scale = self.data.config["ov_satellite_model_scale"]
        [x_dim, y_dim, z_dim] = [scale / 2, scale / 2, scale]

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

        self.satellite_model_points0 = points * 1

        for i, point in enumerate(points):
            points[i] = point + self.data.simdata["xyz"][self.i_step]
        #
        # # Offset all the data for plotting purposes
        # for i in range(len(points)):
        #     points[i][2] = points[i][2]+self.zo

        self.satellite_model = GLLinePlotItem(
            pos=points,
            # color=self.c[self.data.config["c3d_preferred_colour"]],
            color=(1.0, 0.5, 0.0, 0.4),
            width=3,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.satellite_model.setDepthValue(0)

        if self.data.config["ov_draw"]["satellite_model"]:
            self.addItem(self.satellite_model)

    def make_angular_momentum_vector(self):
        self.huv_scale = 8E6
        # base = self.data.simdata["xyz"][self.i_step]
        base = array([0.0, 0.0, 0.0])
        tip = base + self.data.simdata["huv"]*self.huv_scale

        self.angular_momentum_vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 0.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=3)
        self.angular_momentum_vector.setDepthValue(0)
        if self.data.config["ov_draw"]["angular_momentum_vector"]:
            self.addItem(self.angular_momentum_vector)

    def make_velocity_vector(self):

        base = self.data.simdata["xyz"][self.i_step]
        tip = base + self.data.simdata["v_xyz"][self.i_step]*self.vv_scale

        self.velocity_vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=3)
        self.velocity_vector.setDepthValue(0)

        if self.data.config["ov_draw"]["velocity_vector"]:
            self.addItem(self.velocity_vector)

    def make_position_vector(self):

        base = array([0, 0, 0])
        tip = self.data.simdata["xyz"][self.i_step]

        self.position_vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=2)
        self.position_vector.setDepthValue(0)

        if self.data.config["ov_draw"]["position_vector"]:
            self.addItem(self.position_vector)

    def make_b_vector(self):
        self.Bi = self.data.simdata["B_ECI"][self.i_step]

        base = self.data.simdata["xyz"][self.i_step]
        tip = base + self.Bi*self.bv_scale

        self.b_vector = GLLinePlotItem(
            pos=[base, tip],
            color=(0.0, 1.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=6)
        self.b_vector.setDepthValue(0)

        if self.data.config["ov_draw"]["b_vector"]:
            self.addItem(self.b_vector)

    def make_b_lineplot(self):

        # TODO can clean this up
        n_steps_orbit = len(self.data.simdata["xyz"])
        n_steps_simdata = len(self.data.simdata["B_ECI"])
        mult = int(ceil(n_steps_simdata/n_steps_orbit))

        points = tile(self.data.simdata["xyz"][:], (mult, 1))[:n_steps_simdata] \
                 + self.data.simdata["B_ECI"][:]*self.bv_scale

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]

        self.b_lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.data.config["c3d_preferred_colour"]],
            color=(0, 1, 1, 0.25),
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        self.b_lineplot.setDepthValue(1)

        if self.data.config["ov_draw"]["b_lineplot"]:
            self.addItem(self.b_lineplot)


    def make_b_linespokes(self):

        # TODO can clean this up
        n_steps_orbit = len(self.data.simdata["xyz"])
        n_steps_simdata = len(self.data.simdata["B_ECI"])
        mult = int(ceil(n_steps_simdata/n_steps_orbit))

        points_outer = tile(self.data.simdata["xyz"][:], (mult, 1))[:n_steps_simdata] \
                 + self.data.simdata["B_ECI"][:]*self.bv_scale
        points_inner = tile(self.data.simdata["xyz"][:], (mult, 1))[:n_steps_simdata] \
                 + 1 / 2 * self.data.simdata["B_ECI"][:]*self.bv_scale

        points = []
        for i in range(self.data.simdata["n_step"]):
            points.append(points_outer[i] * 1)
            points.append(points_inner[i] * 1)
            points.append(points_outer[i] * 1)

        self.b_linespokes = GLLinePlotItem(
            pos=points,
            color=(0.8, 0.8, 0.8, 0.05),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        self.b_linespokes.setDepthValue(0)

        if self.data.config["ov_draw"]["b_linespokes"]:
            self.addItem(self.b_linespokes)


    def make_b_fieldgrid(self, layers=3, h_min=5E5, h_spacing=15E5, brows=16, bcols=8):

        # def make_b_fieldgrid_set(h=5E5, rows=16, cols=16, alpha=0.5):
        #     t0 = time()
        #
        #     r = Earth().r + h
        #
        #     xyz = MeshData.sphere(rows=rows, cols=cols, radius=r).vertexes()
        #     print("Number of fieldgrid points:", len(xyz))
        #
        #     scatterplot = GLScatterPlotItem(
        #         pos=xyz,
        #         color=(0.0, 1.0, 1.0, alpha),
        #         size=3,
        #         pxMode=True)
        #     scatterplot.setDepthValue(0)
        #
        #     lineplots = []
        #     for p in xyz:
        #         p_rlonglat = conv_ECI_geoc(p)
        #
        #         _, _, _, bx, by, bz, _ = igrf_value(
        #             180 / pi * p_rlonglat[2],                            # Latitude [deg]
        #             180 / pi * wrap(p_rlonglat[1] - self.th_Ei, 2 * pi),  # Longitude (ECEF) [deg]
        #             1E-3 * r,                                            # Altitude [km]
        #             self.data.config["orbital_default_generation_parameters"]["date0"])  # Date formatted as decimal year
        #
        #         B_p = R_NED_ECI(p_rlonglat[1], p_rlonglat[2]) @ array([bx/1000, by/1000, bz/1000])  # nT -> uT
        #
        #
        #         b_line = GLLinePlotItem(
        #             pos=[p, p+B_p*self.bfg_lp_scale],
        #             color=(0.0, 1.0, 1.0, alpha),
        #             antialias=self.data.config["ov_use_antialiasing"],
        #             width=1)
        #         b_line.setDepthValue(0)
        #         lineplots.append(b_line)
        #
        #
        #     t1 = time()
        #     print(f"[DEBUG] make_B_fieldgrid() time: {round((t1-t0)*1E6,1)} us")
        #
        #     return scatterplot, lineplots
        #
        # self.b_fieldgrid = []
        #
        # self.bfg_lp_scale = 1E-2 * self.ps
        #
        # # Sequentially call make_B_fieldgrid() to make the plotitems
        # for i in range(layers):
        #     b_fieldgrid_sp, b_fieldgrid_lp = \
        #         make_b_fieldgrid_set(
        #             h=h_min + i * h_spacing, rows=brows, cols=bcols, alpha=0.4
        #         )
        #
        #     self.b_fieldgrid.append(b_fieldgrid_sp)
        #     self.b_fieldgrid += b_fieldgrid_lp
        #
        # # Sequentially add the plotitems, but only when configured to do so
        # if self.data.config["ov_draw"]["b_fieldgrid"]:
        #     for item in self.b_fieldgrid:
        #         self.addItem(item)

        tb0 = time()

        self.b_fieldlines = []
        self.b_fieldlines_points = []

        # def make_fieldline(xyz_start, step_size=1E6):
        #     xyz_points = [xyz_start,]
        #     iters = 0
        #
        #     while not (norm3d(xyz_points[-1]) < 1.1*Earth().r
        #         and xyz_points[-1][2] > 0) and (iters < 5000):
        #         iters += 1
        #         rlonglat = conv_ECI_geoc(xyz_points[-1])
        #
        #         # r = max((xyz_start[0]**2 + xyz_start[1]**2 + xyz_start[2]**2)**0.5 - Earth().r, 0)
        #         r = norm3d(xyz_points[-1]) - Earth().r
        #
        #         _, _, _, bx, by, bz, _ = igrf_value(
        #             180 / pi * rlonglat[2],  # Latitude [deg]
        #             180 / pi * wrap(rlonglat[1] - self.th_Ei, 2 * pi),  # Longitude (ECEF) [deg]
        #             1E-3 * r,  # Altitude [km]
        #             self.data.config["orbital_default_generation_parameters"]["date0"])  # Date formatted as decimal year
        #
        #         B_xyz = R_NED_ECI(rlonglat[1], rlonglat[2]) @ array([bx / 1000, by / 1000, bz / 1000])  # nT -> uT
        #         xyz_points.append(xyz_points[-1] + uv3d(B_xyz)*step_size)
        #
        #     fieldline_lp = GLLinePlotItem(
        #         pos=xyz_points,
        #         color=(0.0, 1.0, 1.0, 0.25),
        #         antialias=self.data.config["ov_use_antialiasing"],
        #         width=1)
        #     fieldline_lp.setDepthValue(0)
        #     self.b_fieldlines.append(fieldline_lp)
        #     print(f"[DEBUG] make_fieldline iters: {iters}  ,  len(fieldline) = {len(xyz_points)}")

        def make_fieldlines(start_points, step_size=7.5E5):
            Bmags = []
            iters = []
            all_points = empty((0, 3))
            # For each start point, propagate along the field line:
            for i, start_point in enumerate(start_points):
                xyz_points = [start_point,]
                itr = 0

                while not (norm3d(xyz_points[-1]) < 1.1*Earth().r
                    and xyz_points[-1][2] > 0) and (itr < 2048):
                    itr += 1
                    rlonglat = conv_ECI_geoc(xyz_points[-1])

                    # r = max((xyz_start[0]**2 + xyz_start[1]**2 + xyz_start[2]**2)**0.5 - Earth().r, 0)
                    r = norm3d(xyz_points[-1]) - Earth().r

                    _, _, _, bx, by, bz, _ = igrf_value(
                        180 / pi * rlonglat[2],  # Latitude [deg]
                        180 / pi * wrap(rlonglat[1] - self.th_Ei, 2 * pi),  # Longitude (ECEF) [deg]
                        1E-3 * r,  # Altitude [km]
                        self.data.config["orbital_default_generation_parameters"]["date0"])  # Date formatted as decimal year

                    B_xyz = R_NED_ECI(rlonglat[1], rlonglat[2]) @ array([bx / 1000, by / 1000, bz / 1000])  # nT -> uT

                    # Record Bmag, to be used later for alpha/intensity
                    Bmag = norm3d(B_xyz)
                    if itr == 1:
                        Bmag = 0    # Set all first points to zero, so we hide cross lines
                    Bmags.append(Bmag)

                    # Turn magnetic vector to unit vector, and move 'step_size' meters
                    # in that direction for the next point.
                    xyz_points.append(xyz_points[-1] + uv3d(B_xyz)*step_size)

                Bmags.append(0.)
                all_points = concatenate((all_points, array(xyz_points)))
                iters.append(itr)

            # print(f"all_points: {all_points}")

            # print(f"len(all_points): {len(all_points)}")

            # print(f"len(Bmags): {len(Bmags)}")
            # print(Bmags)

            # Drawing the concatenated field lines
            intensities = []
            for ppoint in all_points:
                intensities.append(norm3d(ppoint))

            Bmags = array(Bmags)
            Bmag_max = max(Bmags)

            # intensities = (Bmags/Bmag_max)**0.75  # Use root to compress colour intensities
            intensities = Bmags/Bmag_max  # Use root to compress colour intensities

            colour_array = array([
                zeros(len(all_points) - 1),
                ones(len(all_points) - 1),
                ones(len(all_points) - 1),
                intensities[:-1],
            ]).transpose()

            fieldline_lp = GLLinePlotItem(
                pos=all_points,
                color=colour_array,
                antialias=self.data.config["ov_use_antialiasing"],
                width=0.5,
                glOptions='additive')
            fieldline_lp.setDepthValue(-3)
            self.b_fieldlines.append(fieldline_lp)
            print(f"[DEBUG] make_fieldline iters: {iters}  ,  len(fieldline) = {len(all_points)}")



        start_points = []

        def create_start_points(start_points, points_per_circle = 12, side_mag = 0.5, z_mag = 1.0):
            for i in range(points_per_circle):
                temp = 2*pi/points_per_circle
                start_points.append(array([
                    side_mag * sin(i * temp),
                    side_mag * cos(i * temp),
                    -z_mag
                ]))
                # print(f"[DEBUG] appended {sin(i * temp)}, {cos(i * temp)}, {-side_mag}")
            return start_points

        points_per_circle = 12

        start_points = create_start_points(start_points, 12, 0.6, 1)
        start_points = create_start_points(start_points, 12, 0.9, 1)
        start_points = create_start_points(start_points, 12, 1, 0.5)

        # start_points = [
        #     array([   0,    1, -0.95]),
        #     array([ 0.5*s2,  0.5*s2, -0.95]),
        #     array([   1,  0.0, -0.95]),
        #     array([ 0.5*s2, -0.5*s2, -0.95]),
        #     array([   0,   -1, -0.95]),
        #     array([-0.5*s2, -0.5*s2, -0.95]),
        #     array([  -1,    0, -0.95]),
        #     array([-0.5*s2,  0.5*s2, -0.95]),
        # ]
        for i in range(len(start_points)):
            start_points[i] = 0.9*Earth().r * uv3d(start_points[i])

        # start_points_scatterplot = GLScatterPlotItem(
        #         pos=start_points,
        #         color=(0.0, 1.0, 1.0, 0.5),
        #         size=5,
        #         pxMode=True)
        # start_points_scatterplot.setDepthValue(0)

        # print(f"start_points: {start_points}")

        # self.b_fieldlines_points.append(
        #     start_points_scatterplot
        # )

        # for start_point in start_points:
        #     make_fieldline(start_point)

        make_fieldlines(start_points)


        # self.addItem(start_points_scatterplot)
        for item in self.b_fieldlines:
            self.addItem(item)
        print(f"[DEBUG] b_fieldline draw duration: {round(1E3*(time() - tb0),1)} ms")


        # ## Geomagnetic axis
        # ## South pole as of 2020 by IGRF-13 fit:
        # # North: 80.7 N,  72.7 W
        # # South: 80.7 S, 107.3 E
        # _, _, _, bx0, by0, bz0, _ = igrf_value(
        #     107.3,  # Latitude [deg]
        #     80.7,  # Longitude (ECEF) [deg]
        #     0,  # Altitude [km]
        #     self.data.config["orbital_default_generation_parameters"]["date0"])  # Date formatted as decimal year
        # geomag_axis_points = [
        #      3 * Earth().r * uv3d(array([bx0, by0, bz0])),
        #     -3 * Earth().r * uv3d(array([bx0, by0, bz0])),
        # ]
        #
        # geomag_axis_lp = GLLinePlotItem(
        #     pos=geomag_axis_points,
        #     color=(0.0, 1.0, 1.0, 0.5),
        #     antialias=self.data.config["ov_use_antialiasing"],
        #     width=4)
        # geomag_axis_lp.setDepthValue(0)
        # self.addItem(geomag_axis_lp)


    def make_vector_pos(self):  # TODO: Remove (after verification complete)
        point = self.points[self.data.i_satpos]

        rlonglat = conv_ECEF_geoc(point)
        xcalc = rlonglat[0] * cos(rlonglat[1]) * sin(pi / 2 - rlonglat[2])
        ycalc = rlonglat[0] * sin(rlonglat[1]) * sin(pi / 2 - rlonglat[2])
        zcalc = rlonglat[0] * cos(pi / 2 - rlonglat[2])

        vector = GLLinePlotItem(
            pos=[array([0, 0, 0]), array([xcalc, ycalc, zcalc])],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        vector.setDepthValue(0)
        return vector


class OrbitalPlotButtons(QGroupBox):
    """Description"""
    def __init__(self, orbitalplot, datapool) -> None:
        super().__init__()

        self.orbitalplot = orbitalplot
        self.data = datapool

        self.layout0 = QGridLayout()
        self.buttons = []

        # Generate buttons
        self.button_tripod_ECI = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_ECI, "tripod_ECI", label="ECI")
        self.button_tripod_ECI.toggled.connect(self.toggle_tripod_ECI)

        self.button_tripod_ECEF = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_ECEF, "tripod_ECEF", label="ECEF")
        self.button_tripod_ECEF.toggled.connect(self.toggle_tripod_ECEF)

        self.button_tripod_NED = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_NED, "tripod_NED", label="NED")
        self.button_tripod_NED.toggled.connect(self.toggle_tripod_NED)

        self.button_tripod_SI = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_SI, "tripod_SI", label="SI")
        self.button_tripod_SI.toggled.connect(self.toggle_tripod_SI)

        self.button_tripod_B = QPushButton(QIcon("./assets/icons/tripod.svg"), "")
        self.setup(self.button_tripod_B, "tripod_B", label="B")
        self.button_tripod_B.toggled.connect(self.toggle_tripod_B)

        self.button_xy_grid = QPushButton(QIcon("./assets/icons/grid2.svg"), "")
        self.setup(self.button_xy_grid, "xy_grid", label="XY")
        self.button_xy_grid.toggled.connect(self.toggle_xy_grid)

        self.button_earth_model = QPushButton(QIcon("./assets/icons/feather/globe.svg"), "")
        self.setup(self.button_earth_model, "earth_model")
        self.button_earth_model.toggled.connect(self.toggle_earth_model)

        self.button_orbit_lineplot = QPushButton(QIcon("./assets/icons/orbitB.svg"), "")
        self.setup(self.button_orbit_lineplot, "orbit_lineplot")
        self.button_orbit_lineplot.toggled.connect(self.toggle_orbit_lineplot)

        self.button_orbit_scatterplot = QPushButton(QIcon("./assets/icons/orbitB_dots.svg"), "")
        self.setup(self.button_orbit_scatterplot, "orbit_scatterplot")
        self.button_orbit_scatterplot.toggled.connect(self.toggle_orbit_scatterplot)

        self.button_orbit_helpers = QPushButton(QIcon("./assets/icons/orbit_spokes.svg"), "")
        self.setup(self.button_orbit_helpers, "orbit_helpers")
        self.button_orbit_helpers.toggled.connect(self.toggle_orbit_helpers)

        self.button_satellite = QPushButton(QIcon("./assets/icons/dot.svg"), "")
        self.setup(self.button_satellite, "satellite")
        self.button_satellite.toggled.connect(self.toggle_satellite)

        self.button_satellite_helpers = QPushButton(QIcon("./assets/icons/components.svg"), "")
        self.setup(self.button_satellite_helpers, "satellite_helpers")
        self.button_satellite_helpers.toggled.connect(self.toggle_satellite_helpers)

        self.button_satellite_model = QPushButton(QIcon("./assets/icons/satellite.svg"), "")
        self.setup(self.button_satellite_model, "satellite_model")
        self.button_satellite_model.toggled.connect(self.toggle_satellite_model)

        self.button_position_vector = QPushButton(QIcon("./assets/icons/vector_r.svg"), "")
        self.setup(self.button_position_vector, "position_vector")
        self.button_position_vector.toggled.connect(self.toggle_position_vector)

        self.button_velocity_vector = QPushButton(QIcon("./assets/icons/vector_v.svg"), "")
        self.setup(self.button_velocity_vector, "velocity_vector")
        self.button_velocity_vector.toggled.connect(self.toggle_velocity_vector)

        self.button_angular_momentum_vector = QPushButton(QIcon("./assets/icons/vector_h.svg"), "")
        self.setup(self.button_angular_momentum_vector, "angular_momentum_vector")
        self.button_angular_momentum_vector.toggled.connect(self.toggle_angular_momentum_vector)

        self.button_b_vector = QPushButton(QIcon("./assets/icons/vector_b.svg"), "")
        self.setup(self.button_b_vector, "b_vector")
        self.button_b_vector.toggled.connect(self.toggle_b_vector)

        self.button_b_lineplot = QPushButton(QIcon("./assets/icons/lineplot.svg"), "")
        self.setup(self.button_b_lineplot, "b_lineplot")
        self.button_b_lineplot.toggled.connect(self.toggle_b_lineplot)

        self.button_b_linespokes = QPushButton(QIcon("./assets/icons/lineplot_spokes.svg"), "")
        self.setup(self.button_b_linespokes, "b_linespokes")
        self.button_b_linespokes.toggled.connect(self.toggle_b_linespokes)

        self.button_b_fieldgrid = QPushButton(QIcon("./assets/icons/field_lines.svg"), "")
        self.setup(self.button_b_fieldgrid, "b_fieldgrid")
        self.button_b_fieldgrid.toggled.connect(self.toggle_b_fieldgrid)

        self.button_autorotate = QPushButton(QIcon("./assets/icons/autorotate.svg"), "")
        self.setup(self.button_autorotate, "autorotate")
        self.button_autorotate.toggled.connect(self.toggle_autorotate)


        self.setLayout(self.layout0)
        self.layout0.setSizeConstraint(QLayout.SetMinimumSize)
        self.setMaximumSize(32, 860)
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
        if self.data.config["ov_draw"][reference] is True:
            button.setChecked(True)
        button.setFixedSize(QSize(32, 32))
        button.setIconSize(QSize(24, 24))
        self.layout0.addWidget(button, len(self.buttons), 0)
        self.layout0.addWidget(QLabel(label), len(self.buttons), 1)
        self.buttons.append(button)


    def toggle_tripod_ECI(self):
        if self.button_tripod_ECI.isChecked():
            self.data.config["ov_draw"]["tripod_ECI"] = True
            self.orbitalplot.make_tripod_ECI()
        else:
            self.data.config["ov_draw"]["tripod_ECI"] = False
            for item in self.orbitalplot.tripod_ECI:
                self.orbitalplot.removeItem(item)

    def toggle_tripod_ECEF(self):
        if self.button_tripod_ECEF.isChecked():
            self.data.config["ov_draw"]["tripod_ECEF"] = True
            self.orbitalplot.make_tripod_ECEF()
        else:
            self.data.config["ov_draw"]["tripod_ECEF"] = False
            for item in self.orbitalplot.tripod_ECEF:
                self.orbitalplot.removeItem(item)

    def toggle_tripod_NED(self):
        if self.button_tripod_NED.isChecked():
            self.data.config["ov_draw"]["tripod_NED"] = True
            self.orbitalplot.make_tripod_NED()
        else:
            self.data.config["ov_draw"]["tripod_NED"] = False
            for item in self.orbitalplot.tripod_NED:
                self.orbitalplot.removeItem(item)

    def toggle_tripod_SI(self):
        if self.button_tripod_SI.isChecked():
            self.data.config["ov_draw"]["tripod_SI"] = True
            self.orbitalplot.make_tripod_SI()
        else:
            self.data.config["ov_draw"]["tripod_SI"] = False
            for item in self.orbitalplot.tripod_SI:
                self.orbitalplot.removeItem(item)

    def toggle_tripod_B(self):
        if self.button_tripod_B.isChecked():
            self.data.config["ov_draw"]["tripod_B"] = True
            self.orbitalplot.make_tripod_B()
        else:
            self.data.config["ov_draw"]["tripod_B"] = False
            for item in self.orbitalplot.tripod_B:
                self.orbitalplot.removeItem(item)

    def toggle_xy_grid(self):
        if self.button_xy_grid.isChecked():
            self.data.config["ov_draw"]["xy_grid"] = True
            self.orbitalplot.make_xy_grid()
        else:
            self.data.config["ov_draw"]["xy_grid"] = False
            self.orbitalplot.removeItem(self.orbitalplot.xy_grid)

    def toggle_earth_model(self):
        if self.button_earth_model.isChecked():
            self.data.config["ov_draw"]["earth_model"] = True
            self.orbitalplot.make_earth_model()
        else:
            self.data.config["ov_draw"]["earth_model"] = False
            self.orbitalplot.removeItem(self.orbitalplot.earth_model)

    def toggle_orbit_lineplot(self):
        if self.button_orbit_lineplot.isChecked():
            self.data.config["ov_draw"]["orbit_lineplot"] = True
            self.orbitalplot.make_orbit_lineplot()
        else:
            self.data.config["ov_draw"]["orbit_lineplot"] = False
            self.orbitalplot.removeItem(self.orbitalplot.orbit_lineplot)

    def toggle_orbit_scatterplot(self):
        if self.button_orbit_scatterplot.isChecked():
            self.data.config["ov_draw"]["orbit_scatterplot"] = True
            self.orbitalplot.make_orbit_scatterplot()
        else:
            self.data.config["ov_draw"]["orbit_scatterplot"] = False
            self.orbitalplot.removeItem(self.orbitalplot.orbit_scatterplot)

    def toggle_orbit_helpers(self):
        if self.button_orbit_helpers.isChecked():
            self.data.config["ov_draw"]["orbit_helpers"] = True
            self.orbitalplot.make_orbit_helpers()
        else:
            self.data.config["ov_draw"]["orbit_helpers"] = False
            for item in self.orbitalplot.orbit_helpers:
                self.orbitalplot.removeItem(item)

    def toggle_satellite(self):
        if self.button_satellite.isChecked():
            self.data.config["ov_draw"]["satellite"] = True
            self.orbitalplot.make_satellite()
        else:
            self.data.config["ov_draw"]["satellite"] = False
            self.orbitalplot.removeItem(self.orbitalplot.satellite)

    def toggle_satellite_helpers(self):
        if self.button_satellite_helpers.isChecked():
            self.data.config["ov_draw"]["satellite_helpers"] = True
            self.orbitalplot.make_satellite_helpers()
        else:
            self.data.config["ov_draw"]["satellite_helpers"] = False
            for item in self.orbitalplot.satellite_helpers:
                self.orbitalplot.removeItem(item)

    def toggle_satellite_model(self):
        if self.button_satellite_model.isChecked():
            self.data.config["ov_draw"]["satellite_model"] = True
            self.orbitalplot.make_satellite_model()
        else:
            self.data.config["ov_draw"]["satellite_model"] = False
            self.orbitalplot.removeItem(self.orbitalplot.satellite_model)

    def toggle_position_vector(self):
        if self.button_position_vector.isChecked():
            self.data.config["ov_draw"]["position_vector"] = True
            self.orbitalplot.make_position_vector()
        else:
            self.data.config["ov_draw"]["position_vector"] = False
            self.orbitalplot.removeItem(self.orbitalplot.position_vector)

    def toggle_velocity_vector(self):
        if self.button_velocity_vector.isChecked():
            self.data.config["ov_draw"]["velocity_vector"] = True
            self.orbitalplot.make_velocity_vector()
        else:
            self.data.config["ov_draw"]["velocity_vector"] = False
            self.orbitalplot.removeItem(self.orbitalplot.velocity_vector)

    def toggle_angular_momentum_vector(self):
        if self.button_angular_momentum_vector.isChecked():
            self.data.config["ov_draw"]["angular_momentum_vector"] = True
            self.orbitalplot.make_angular_momentum_vector()
        else:
            self.data.config["ov_draw"]["angular_momentum_vector"] = False
            self.orbitalplot.removeItem(self.orbitalplot.angular_momentum_vector)

    def toggle_b_vector(self):
        if self.button_b_vector.isChecked():
            self.data.config["ov_draw"]["b_vector"] = True
            self.orbitalplot.make_b_vector()
        else:
            self.data.config["ov_draw"]["b_vector"] = False
            self.orbitalplot.removeItem(self.orbitalplot.b_vector)

    def toggle_b_lineplot(self):
        if self.button_b_lineplot.isChecked():
            self.data.config["ov_draw"]["b_lineplot"] = True
            self.orbitalplot.make_b_lineplot()
        else:
            self.data.config["ov_draw"]["b_lineplot"] = False
            self.orbitalplot.removeItem(self.orbitalplot.b_lineplot)

    def toggle_b_linespokes(self):
        if self.button_b_linespokes.isChecked():
            self.data.config["ov_draw"]["b_linespokes"] = True
            self.orbitalplot.make_b_linespokes()
        else:
            self.data.config["ov_draw"]["b_linespokes"] = False
            self.orbitalplot.removeItem(self.orbitalplot.b_linespokes)

    def toggle_b_fieldgrid(self):
        if self.button_b_fieldgrid.isChecked():
            self.data.config["ov_draw"]["b_fieldgrid"] = True
            for item in self.orbitalplot.b_fieldlines:
                self.orbitalplot.addItem(item)
            # for item in self.orbitalplot.b_fieldgrid:
                # self.orbitalplot.addItem(item)
        else:
            self.data.config["ov_draw"]["b_fieldgrid"] = False
            for item in self.orbitalplot.b_fieldlines:
                self.orbitalplot.removeItem(item)
            # for item in self.orbitalplot.b_fieldgrid:
                # self.orbitalplot.removeItem(item)

    def toggle_autorotate(self):
        if self.button_autorotate.isChecked():
            self.data.config["ov_draw"]["autorotate"] = True
        else:
            self.data.config["ov_draw"]["autorotate"] = False

