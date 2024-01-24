import numpy as np
from numpy import (
    pi,
    array, ndarray,
    sin, cos, arccos,
    dot, zeros, eye, linspace, vstack
)

import matplotlib.pyplot as plt
from time import time
from PyQt5 import QtCore
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

from pg3d import (
    RX, RY, RZ, R,
    PGPoint3D, PGVector3D, PGFrame3D,
    plotgrid, plotpoint, plotpoints, plotvector, plotframe,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
    sign, wrap, uv3d,
    conv_ECI_geoc,
    R_NED_ECI, R_ECI_NED,
    R_SI_B, R_B_SI,
    R_ECI_ECEF, R_ECEF_ECI
)

from orbit import Orbit, Earth

# Goal: define and describe an orbit fully from its six orbital elements:
# - Generalized OrbitVisualizer class that can:
#     - Be docked into existing PyQt5 Window
#     - Gather orbits
#     - Gather body
#     - Orbit patch function for drawing
#     - Generalized update class, that can be synchronized externally
# - Support for 5 coordinate systems:
#     - ECI (General Inertial of Earth (ECI))
#     - ECEF (Earth Fixed (ECEF))
#     - SI (Satellite Inertial reference frame)
#     - BF (satellite Body Fixed reference frame)
#     - GC (Geographic Coordinate system used by IGRF (GCS))
# - Support for real-time marching, rather than point-marching, with time multiplier
# - Integration of IGRF
# - Integration in
# Then propagate these properties over time (and maybe plot)
# Then convert to x, y, z, t coordinates that IGRF can eat
#
# Also:
# - Experiment with computational shortcuts

# class Orbit:
#     def __init__(self, body, a, e, i, raan, argp, ta,
#                  spacing="isochronal"):
#         if 0 > e >= 1:
#             raise ValueError(f"Eccentricity value {e} not allowed (only elliptical orbits are supported)!")
#         if a <= 0:
#             raise ValueError(f"Invalid semi-major axis specified {a}!")
#
#         self.d2r = pi / 180
#         self.body = body
#
#         # All internal angles defined in radians
#         self.a = a                          # Semi-major axis
#         self.e = e                          # Eccentricity
#         self.i = self.d2r*(i % 180)         # Inclination
#         self.raan = self.d2r*(raan % 360)   # Right ascention of the ascending node
#         self.argp = self.d2r*(argp % 360)   # Argument of periapsis
#         self.ma0 = self.d2r*(ta % 360)      # Initial Mean anomaly
#
#
#         # General orbital properties
#         self.period = self.get_period()     # Orbital period
#         self.b = self.a*(1-self.e**2)**0.5  # Semi-minor axis
#
#     def orbit_transformation_matrix(self):
#         so, sO, si = sin(self.argp), sin(self.raan), sin(self.i)
#         co, cO, ci = cos(self.argp), cos(self.raan), cos(self.i)
#
#         # Source: Wakker
#         T = array([
#             [co*cO - so*sO*ci, -so*cO - co*sO*ci,  sO*si],
#             [co*sO + so*cO*ci, -so*sO + co*cO*ci, -cO*si],
#             [           so*si,             co*si,     ci]]
#         )
#
#         return T
#
#     def get_i(self):
#         return self.i/self.d2r
#
#     def get_period(self):
#         return 2*pi * (self.a**3 / self.body.gm)**0.5
#
#     def equation_of_the_center(self, M, e, order=12):
#         # General expression in terms of Bessel functions of the first kind
#         # (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
#         v = M
#         if 0 < e < 1:  # If e == 0 (circular orbit) don't bother
#             b = 1 / e * (1 - (1 - e * e) ** 0.5)
#             for s in range(1, order):
#                 bt = 0
#                 for p in range(1, order):
#                     bt += b**p*(jv(s-p, s*e)+jv(s+p, s*e))
#                 v += 2/s * (jv(s, s*e) + bt)*sin(s*M)
#
#         return v
#
#     def draw(self, subdivisions=128, spacing="isochronal", order=12):
#
#         t0 = time()
#         if spacing in ("equitemporal", "isochronal"):
#             if self.e > 0.5:
#                 print("WARNING! Isochronal point generation of orbits with eccentricity > 0.5 may be subjected to oscillations. Consider increasing the order of the method, or using equidistant instead")
#
#             # Spacing of mean anomaly
#             mean_anomaly = linspace(0, 2 * pi, subdivisions + 1)[:-1]
#             mean_anomaly = [(ma+self.ma0) % (2*pi) for ma in mean_anomaly]
#             angulars = np.zeros(len(mean_anomaly))
#             for i in range(len(mean_anomaly)):
#                 angulars[i] = self.equation_of_the_center(
#                     mean_anomaly[i], self.e, order=order)
#
#
#         elif spacing == "equidistant":
#             # Using polar coordinates:
#             angulars = np.linspace(0, 2*pi, subdivisions+1)[:-1]
#             # angulars = np.linspace(0, 2*pi, subdivisions)
#
#         else:
#             raise ValueError("Valid spacing settings: 'equidistant', 'isochronal'")
#
#         # Radial components relative to focus:
#         radials = self.a*(1-self.e**2) / (1 + self.e * cos(angulars))
#         # # Radial components centered:
#         # radials = self.b/(1-(self.e*cos(angulars))**2)**0.5
#
#         # Flat coordinates
#         xf = radials * cos(angulars)
#         yf = radials * sin(angulars)
#         zf = np.zeros(len(xf))
#
#         x = np.zeros(len(xf))
#         y = np.zeros(len(xf))
#         z = np.zeros(len(xf))
#
#         T = self.orbit_transformation_matrix()
#
#         for i in range(len(xf)):
#             x[i], y[i], z[i] = np.dot(T, np.array([xf[i], yf[i], zf[i]]))
#
#         print(f"draw() time: {round((time()-t0)*1E6, 1)} us")
#         return [x, y, z]
#
#     # @staticmethod
#     # def conv_ECI_GC(x_sat, x_zero):
#     #
#     #     def unit(vector):
#     #         return vector / np.linalg.norm(vector)
#     #
#     #     def vector_angle(a, b):
#     #         au, bu = unit(a), unit(b)
#     #         return np.arccos(np.dot(au, bu))
#     #
#     #     x_sat_p = np.array([x_sat[0], x_sat[1], 0])
#     #     print(f"x_sat_p = {x_sat_p}")
#     #
#     #     tau = vector_angle(x_zero, x_sat_p)
#     #     delta = vector_angle(x_sat, x_sat_p)
#     #
#     #     print(f"tau   = {round(tau * 180 / np.pi, 1)} deg")
#     #     print(f"delta = {round(delta * 180 / np.pi, 1)} deg")
#     #
#     #     R_ECI_GC = np.array([
#     #         [-sin(delta) * cos(delta), -sin(delta) * sin(delta), cos(delta)],
#     #         [-sin(tau), cos(delta), 0],
#     #         [-cos(delta) * cos(delta), -cos(delta) * sin(delta), cos(delta)],
#     #     ])
#     #
#     #     return R_ECI_GC@x_sat
#
#     # @staticmethod
#     # def conv_ECEF_geoc(coor_ECEF):
#     #
#     #     def unit(vector):
#     #         return vector / np.linalg.norm(vector)
#     #
#     #     def vector_angle(a, b):
#     #         au, bu = unit(a), unit(b)
#     #         return np.arccos(np.dot(au, bu))
#     #
#     #     if len(coor_ECEF) != 3:
#     #         raise AssertionError(f"coor_ECEF is length {len(coor_ECEF)} but must be length 3!")
#     #
#     #     # Project coor_ECEF onto XY plane:
#     #     coor_pXY = np.array([coor_ECEF[0], coor_ECEF[1], 0])
#     #
#     #     print(f"[DEBUG] coor_ECEF = {coor_ECEF}")
#     #     print(f"[DEBUG] coor_pXY = {coor_pXY}")
#     #
#     #     xaxis_ECEF = np.array([1, 0, 0])
#     #
#     #     longitude = coor_ECEF[1] / abs(coor_ECEF[1]) * vector_angle(xaxis_ECEF, coor_pXY)
#     #     latitude = coor_ECEF[2] / abs(coor_ECEF[2]) * vector_angle(coor_ECEF, coor_pXY)
#     #     r = np.linalg.norm(coor_ECEF)
#     #
#     #     print(f"[DEBUG] longitude   = {round(longitude * 180 / np.pi, 1)} deg")
#     #     print(f"[DEBUG] latitude = {round(latitude * 180 / np.pi, 1)} deg")
#     #     print(f"[DEBUG] r = {round(r / 1E3, 0)} km")
#     #
#     #     return np.array([longitude, latitude, r])
#
#
#     def calc(self, ):
#         pass
#
#     def plot_simple(self, coordinates):
#         x, y, z = coordinates
#         fig, ax = plt.subplots()
#         ax.plot(x, y, "r")
#         ax.set(aspect=1)
#         plt.show()
#
#     def print_properties(self):
#         print("To be implemented...")
#
#
# class Body:
#     def __init__(self, name: str, m, r):
#         self.name = name
#         self.m = m
#         self.g = 6.67430E-11
#         self.gm = self.m*self.g
#         self.r = r
#
#
# class Earth(Body):
#     def __init__(self):
#         super().__init__("Earth", 5.9722E24, 6.371E6)


# def conv_ECEF_geoc(coor_ECEF, rd=6):  # TODO: Remove:
#
#     if len(coor_ECEF) != 3:
#         raise AssertionError(f"coor_ECEF is length {len(coor_ECEF)} but must be length 3!")
#
#     x, y, z = coor_ECEF[0], coor_ECEF[1], coor_ECEF[2]
#     # print(f"[DEBUG] x, y, z = {x}  {y}  {z}")
#
#     # Subvert the singularities at -90 and 90 degrees pitch
#     # Using rounding to fix floating-point errors whilst sacrificing um
#     # precision around singularities (who cares about that anyway?)
#     # and increases function evaluation from 8 us to 16 us
#     if round(x, rd) == 0 and round(y, rd) == 0:
#         if round(z, rd) == 0:
#             raise ValueError("coor_ECEF has no defined direction, as its length is 0!")
#         else:
#             # print("[DEBUG] DIVERSION!")
#             r = abs(z)
#             longitude = 0
#             latitude = sign(z)*np.pi/2
#
#     else:
#         r = (x**2 + y**2 + z**2)**0.5
#         longitude = sign(y)*np.arccos(x/(x**2 + y**2)**0.5)
#         latitude = np.pi/2-np.arccos(z/r)
#
#         # print(f"[DEBUG] x: {x}, y: {y}, sign(y): {sign(y)}")
#         # print(f"[DEBUG] x/(x**2 + y**2)**0.5: {x/(x**2 + y**2)**0.5}")
#         # print(f"[DEBUG] arccos(x/(x**2 + y**2)**0.5): {180/np.pi*np.arccos(x/(x**2 + y**2)**0.5)} deg")
#     #
#     # print(f"[DEBUG] long: {round(180/np.pi*longitude,1)} deg")
#     # print(f"[DEBUG] lat:  {round(180/np.pi*latitude,1)} deg")
#     # print("")
#     return array([r, longitude, latitude])


# def conv_ECEF_NED(coor, r, long, lat):  # TODO: REMOVE
#     # long = -long
#     # lat = -lat
#     # long = wrap(long+np.pi/2, 2*np.pi)
#     # lat = wrap(lat-np.pi/2, np.pi)
#     # print("EFFECTIVE VALUES:")
#     # print(f"[DEBUG] long: {round(180/np.pi*long,1)} deg")
#     # print(f"[DEBUG] lat:  {round(180/np.pi*lat,1)} deg")
#     # print("")
#
#     # R_NED_ENU = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]])
#     R_NED_ENU = array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # TODO: REMOVE
#     # return np.dot(R_X, np.dot(R_Z, np.dot(R_NED_ENU, coor)))
#     # return np.dot(R_X, np.dot(R_Z, coor))
#
#     # coor = dot(RY(pi/2), coor)    # First rotate 90 deg around Y
#     # coor = dot(RZ(pi/2).transpose(), coor)    # Then rotate 90 deg around Z
#     # coor = dot(RY(pi/2).transpose(), coor)    # Then rotate 90 deg around X
#     # print(f"[DEBUG] Ry*Rz: {dot(RY(pi/2).transpose(), RZ(pi/2).transpose())}")
#
#     Ry_90Rz_90 = array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
#     # Ry90Rz90 = array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]])
#     coor = dot(Ry_90Rz_90, coor)
#
#
#     # coor = np.dot(RX(0*np.pi/2), np.dot(RZ(np.pi/2), coor))
#     # coor = np.dot(np.dot(RX(0*np.pi/2), RZ(np.pi/2)), coor)
#     # coor = np.dot(RZ(long), coor)
#     return coor


class OrbitVisualizer(GLViewWidget):
    def __init__(self, datapool):
        super().__init__()

        self.data = datapool

        # ==== PREAMBLE
        self.points, self.ma, self.ta, self.gamma, self.huv, self.v_xyz = self.generate_points()
        self.dt = self.data.orbit.get_period()/self.data.orbit_subs
        self.dth_E = Earth().axial_rate*self.dt
        self.year = 2020.

        self.Rta_ECI_SI = np.empty((self.data.orbit_subs, 3, 3))

        for i in range(self.data.orbit_subs):
            self.Rta_ECI_SI[i, :, :] = vstack([
                uv3d(self.v_xyz[i]),
                self.huv,
                np.cross(uv3d(self.v_xyz[i]), self.huv)])

        self.ps = self.data.config["ov_plotscale"]  # Plot scale
        self.c = self.data.config["ov_plotcolours"]
        self.aa = self.data.config["ov_use_antialiasing"]

        self.setCameraPosition(distance=3*self.ps)


        # ==== GRID ==========================================================
        # Generate grid
        if self.data.config["ov_draw"]["XY_grid"]:
            self.grid = plotgrid(self, plotscale=self.ps)


        # ==== FRAME TRIPODS =================================================
        # Generate ECI-frame tripod_components
        self.frame_ECI = PGFrame3D()
        if self.data.config["ov_draw"]["tripod_ECI"]:
            self.frame_ECI_plotitems = plotframe(
                self.frame_ECI, self,
                plotscale=1.5*self.ps, alpha=0.4, antialias=self.aa
            )

        # Generate ECEF-frame tripod_components
        self.th_E0 = 0
        self.th_E = (self.data.i_satpos*self.dth_E+self.th_E0) % (2*pi)  # Earth axial rotation angle
        Ri_ECEF_ECI = R_ECEF_ECI(self.th_E)
        self.frame_ECEF = PGFrame3D(r=Ri_ECEF_ECI)
        if self.data.config["ov_draw"]["tripod_ECEF"]:
            self.tripod_ECEF_ps = Earth().r
            self.frame_ECEF_plotitems = plotframe(
                self.frame_ECEF, self,
                plotscale=self.tripod_ECEF_ps, alpha=0.4, antialias=self.aa
            )

        # Generate NED-frame tripod_components
        xyz_sat = self.points[self.data.i_satpos]
        # xyz_ECEF = R_ECI_ECEF(self.th_E)@self.points[self.data.i_satpos]
        self.rlonglat = conv_ECI_geoc(xyz_sat)
        Ri_NED_ECI = R_NED_ECI(self.rlonglat[1], self.rlonglat[2]).transpose()  # TODO Homogenise transpose
        self.frame_NED = PGFrame3D(o=self.points[self.data.i_satpos], r=Ri_NED_ECI)
        if self.data.config["ov_draw"]["tripod_NED"]:
            self.tripod_NED_ps = 0.4 * self.ps
            self.frame_NED_plotitems = plotframe(
                self.frame_NED, self,
                plotscale=self.tripod_NED_ps, alpha=0.4, antialias=self.aa
            )

        # Generate SI-frame tripod_components
        Ri_ECI_SI = self.Rta_ECI_SI[self.data.i_satpos]
        self.frame_SI = PGFrame3D(o=xyz_sat, r=Ri_ECI_SI)
        if self.data.config["ov_draw"]["tripod_SI"]:
            self.tripod_SI_ps = 0.4 * self.ps
            self.frame_SI_plotitems = plotframe(
                self.frame_SI, self,
                plotscale=self.tripod_SI_ps, alpha=0.4, antialias=self.aa
            )

        # Generate B-frame tripod_components
        ab0 = array([0, pi/2, 0])      # Initial rotation
        self.ab = ab0               # Euler angles of SI -> B transformation
        Ri_ECI_B = R_SI_B(self.ab)@Ri_ECI_SI
        self.frame_B = PGFrame3D(o=self.points[self.data.i_satpos], r=Ri_ECI_B)
        if self.data.config["ov_draw"]["tripod_B"]:
            self.tripod_B_ps = 0.25 * self.ps
            self.frame_B_plotitems = plotframe(
                self.frame_B, self,
                plotscale=self.tripod_B_ps, alpha=1, width=3, antialias=self.aa
            )

        # ==== EARTH MODEL ===================================================
        # Draw Earth meshitem
        if self.data.config["ov_draw"]["earth_model"]:
            self.earth_meshitem = self.make_earth_meshitem()
            if self.th_E != 0:
                self.earth_meshitem.rotate(self.th_E*180/pi, 0, 0, 1, local=False)
            self.addItem(self.earth_meshitem)


        # ==== ORBIT =========================================================

        # Draw orbit lineplot
        if self.data.config["ov_draw"]["orbit_lineplot"]:
            self.orbit_lineplot = self.make_orbit_lineplot()
            self.addItem(self.orbit_lineplot)

        # Draw orbit scatterplot
        if self.data.config["ov_draw"]["orbit_scatterplot"]:
            self.orbit_scatterplot = self.make_orbit_scatterplot()
            self.addItem(self.orbit_scatterplot)

        # Draw helpers (vertical coordinate lines and a XY-projected orbit)
        if self.data.config["ov_draw"]["orbit_helpers"]:
            self.orbit_flatcircle, self.orbit_vlines = self.make_orbit_helpers()
            self.addItem(self.orbit_flatcircle)
            [self.addItem(vline) for vline in self.orbit_vlines]


        # ==== SATELLITE =====================================================

        # Draw representation of satellite, including highlighted helpers
        self.satellite, self.vline_sat, self.vdot_sat = self.make_satellite()
        self.addItem(self.satellite)
        if self.data.config["ov_draw"]["satellite_helpers"]:
            self.addItem(self.vline_sat)
            self.addItem(self.vdot_sat)

        # Draw angular momentum unit vector
        # self.huv_scale = 2E6
        # self.huv_plotitem = self.make_angular_momentum_vector()
        # self.addItem(self.huv_plotitem)

        # Draw position vector
        if self.data.config["ov_draw"]["position_vector"]:
            self.pv_plotitem = self.make_position_vector()
            self.addItem(self.pv_plotitem)

        # Draw velocity vector
        if self.data.config["ov_draw"]["velocity_vector"]:
            self.vv_scale = 0.25E-3*self.ps
            self.vv_plotitem = self.make_velocity_vector()
            self.addItem(self.vv_plotitem)


        # ==== MAGNETIC FIELD ================================================

        # Draw B vector
        if self.data.config["ov_draw"]["B_vector"]:
            self.bv_scale = 1.5E-5*self.ps * 2
            self.bv_plotitem = self.make_B_vector()
            self.addItem(self.bv_plotitem)

        # Quick and dirty 3D vector plot of field elements
        # Skip if neither scatter nor lineplots are selected, to prevent performance hog:
        if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"] or self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
            print("CHECK")
            # Sort out some parameters
            self.bfg_lp_scale = 1E-5 * self.ps
            layers = 3
            h_min = 5E5
            h_spacing = 15E5
            brows = 16
            bcols = 8

            B_fieldgrid_sp_plotitems = [0]*layers
            B_fieldgrid_lp_plotitems = [0]*layers

            # Sequentially call make_B_fieldgrid() to make the plotitems
            for i in range(layers):
                B_fieldgrid_sp_plotitems[i], B_fieldgrid_lp_plotitems[i] = self.make_B_fieldgrid(
                h=h_min+i*h_spacing, rows=brows, cols=bcols, alpha=0.4)

            # Sequentially add the plotitems, but only when configured to do so
            for i in range(layers):
                if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"]:
                    self.addItem(B_fieldgrid_sp_plotitems[i])

                if self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
                    [self.addItem(bline) for bline in B_fieldgrid_lp_plotitems[i]]  # noqa


        # # DEBUGGING VECTOR FOR RLONGLAT - TODO: Remove after verification complete
        # self.vector_pos = self.make_vector_pos()
        # self.addItem(self.vector_pos)

        # Generate NED tripod_components
        # self.tripod_NED_components = self.make_tripod_NED()
        # [self.addItem(comp) for comp in self.tripod_NED_components]

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.satellite_update)
        # self.timer.start(50)  # TODO


    def generate_points(self):
        """Invokes the draw() function in Orbit class to generate orbit points."""
        return self.data.orbit.draw(
            subdivisions=self.data.orbit_subs,
            spacing=self.data.orbit_spacing
        )

    def make_grid(self):
        # Add horizontal grid
        grid = GLGridItem()
        grid.setColor((255, 255, 255, 24))
        grid.setSpacing(x=self.ps/4, y=self.ps/4)  # Comment out this line at your peril...
        grid.setSize(x=3*self.ps, y=3*self.ps)
        grid.setDepthValue(20)  # Ensure grid is drawn after most other features
        return grid

    # def make_tripod_NED(self):  # TODO: Remove deprecated
    #     # Add NED tripod
    #     antialias = self.data.config["ov_use_antialiasing"]
    #     ps_tripod_NED = 0.25*self.ps
    #
    #     point = self.points[self.data.i_satpos]
    #
    #     r, long, lat = conv_ECEF_geoc(point)
    #
    #     point_t = conv_ECEF_NED(point, r, long, lat)
    #
    #     tripod_NED_x = GLLinePlotItem(
    #         pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
    #              conv_ECEF_NED(np.array([ps_tripod_NED, 0, 0]), r, long, lat)+point],
    #         color="#ff0000aa", width=3, antialias=antialias)
    #     tripod_NED_y = GLLinePlotItem(
    #         pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
    #              conv_ECEF_NED(np.array([0, ps_tripod_NED, 0]), r, long, lat)+point],
    #         color="#00ff00aa", width=3, antialias=antialias)
    #     tripod_NED_z = GLLinePlotItem(
    #         pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
    #              conv_ECEF_NED(np.array([0, 0, ps_tripod_NED]), r, long, lat)+point],
    #         color="#0000ffaa", width=3, antialias=antialias)
    #     tripod_components = (tripod_NED_x, tripod_NED_y, tripod_NED_z)
    #     for tripod_component in tripod_components:
    #         tripod_component.setDepthValue(10)
    #     return tripod_components

    def make_earth_meshitem(self, alpha=1.0):
        sr = self.data.config["ov_earth_model_resolution"]

        mesh = MeshData.sphere(rows=sr[0], cols=sr[1], radius=Earth().r)

        ec = self.data.config["ov_earth_model_colours"]

        # Pre-allocate empty array for storing colour data for each mesh triangle
        colours = np.ones((mesh.faceCount(), 4), dtype=float)

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
            if np.random.random() <= p_land:
                i_land.append(i_f)
                if tropic_line[0] <= i_f <= tropic_line[1] and np.random.random() >= 0.5:
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

            if np.random.random() <= p_cloud:
                i_cloud.append(i_f)
                colours[i_f, 0:3] = hex2rgb(ec["cloud"])

        # Apply alpha (does not work)
        colours[:, 3] = alpha

        # Apply the colour data to the mesh triangles
        mesh.setFaceColors(colours)

        # Embed the data into a GLMeshItem (that Qt can work with)
        meshitem = GLMeshItem(
            meshdata=mesh,
            smooth=self.data.config["ov_earth_model_smoothing"],
            computeNormals=True,
            shader="shaded",
        )

        meshitem.setDepthValue(-2)

        return meshitem

    def make_orbit_lineplot(self):
        # Depending on 'orbit_endpatching' setting, patch gap at pericentre
        if self.data.config["ov_endpatching"]:
            points = vstack([self.points, self.points[0]])
        else:
            points = self.points
        lineplot = GLLinePlotItem(
            pos=points,
            color=self.c[self.data.config["ov_preferred_colour"]],
            width=2,
            antialias=self.data.config["ov_use_antialiasing"]
        )
        lineplot.setDepthValue(0)
        return lineplot

    def make_orbit_scatterplot(self):

        scatterplot = GLScatterPlotItem(
            pos=self.points,
            color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
            size=4,
            pxMode=True)
        scatterplot.setDepthValue(0)
        return scatterplot

    def make_orbit_helpers(self):
        # Add flat circle
        # Always patch this circle:
        points_flatZ = vstack((self.points, self.points[0]))

        # Flatten Z-coordinates
        points_flatZ[:, 2] = 0

        flatcircle = GLLinePlotItem(
            pos=points_flatZ,
            color=(1, 1, 1, 0.2),
            width=1,
            antialias=self.data.config["ov_use_antialiasing"])
        flatcircle.setDepthValue(0)

        # Add vlines
        vlines = []
        for i in range(len(self.points)):
            vline = GLLinePlotItem(
                pos=[points_flatZ[i], self.points[i]],
                color=(1, 1, 1, 0.1),
                antialias=self.data.config["ov_use_antialiasing"],
                width=1)
            vline.setDepthValue(0)
            vlines.append(vline)

        return flatcircle, vlines

    def make_satellite(self):
        # Draw satellite
        point = self.points[self.data.i_satpos]
        point_flatZ = array([point[0], point[1], 0])
        sat = GLScatterPlotItem(
            pos=point,
            color=hex2rgb(self.c[self.data.config["ov_preferred_colour"]]),
            size=8,
            pxMode=True)
        sat.setDepthValue(1)

        vline_sat = GLLinePlotItem(
            pos=[point_flatZ, point],
            color=(1.0, 1.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)

        vline_sat.setDepthValue(1)

        vdot_sat = GLScatterPlotItem(
            pos=[point_flatZ, point],
            color=(1.0, 1.0, 1.0, 0.8),
            size=3,
            pxMode=True)
        vdot_sat.setDepthValue(1)

        return sat, vline_sat, vdot_sat

    def make_angular_momentum_vector(self):
        base = self.points[self.data.i_satpos]
        tip = base + self.huv*self.huv_scale

        vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=3)
        vector.setDepthValue(0)
        return vector

    def make_velocity_vector(self):

        base = self.points[self.data.i_satpos]
        tip = base + self.v_xyz[self.data.i_satpos]*self.vv_scale

        vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=3)
        vector.setDepthValue(0)
        return vector

    def make_position_vector(self):

        base = array([0, 0, 0])
        tip = self.points[self.data.i_satpos]

        vector = GLLinePlotItem(
            pos=[base, tip],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=2)
        vector.setDepthValue(0)
        return vector

    def make_B_vector(self):
        # Calculate magnetic field vector
        _, _, _, bx, by, bz, _ = igrf_value(
            180/pi*self.rlonglat[2],                         # Latitude [deg]
            180/pi*wrap(self.rlonglat[1]-self.th_E, 2*pi),   # Longitude (ECEF) [deg]
            1E-3*(self.rlonglat[0]-self.data.orbit.body.r),  # Altitude [km]
            self.year)                                       # Date formatted as decimal year
        B_NED = array([bx, by, bz])
        self.B = R_NED_ECI(self.rlonglat[1], self.rlonglat[2]) @ B_NED

        print("B_NED:", B_NED)
        print("B_ECI:", self.B)

        base = self.points[self.data.i_satpos]
        tip = base + self.B*self.bv_scale

        vector = GLLinePlotItem(
            pos=[base, tip],
            color=(0.0, 1.0, 1.0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=6)
        vector.setDepthValue(0)
        return vector


    def make_B_fieldgrid(self, h=5E5, rows=16, cols=16, alpha=0.5):
        t0 = time()

        r = Earth().r + h

        points = MeshData.sphere(rows=rows, cols=cols, radius=r).vertexes()
        print("Number of fieldgrid points:", len(points))

        if self.data.config["ov_draw"]["B_fieldgrid_scatterplot"]:
            scatterplot = GLScatterPlotItem(
                pos=points,
                color=(0.0, 1.0, 1.0, alpha),
                size=3,
                pxMode=True)
            scatterplot.setDepthValue(0)
        else:
            scatterplot = None

        if self.data.config["ov_draw"]["B_fieldgrid_lineplot"]:
            lineplots = []
            for p in points:
                p_rlonglat = conv_ECI_geoc(p)

                _, _, _, bx, by, bz, _ = igrf_value(
                    180 / pi * p_rlonglat[2],                            # Latitude [deg]
                    180 / pi * wrap(p_rlonglat[1] - self.th_E, 2 * pi),  # Longitude (ECEF) [deg]
                    1E-3 * r,                                            # Altitude [km]
                    self.year)                                           # Date formatted as decimal year

                B_p = R_NED_ECI(p_rlonglat[1], p_rlonglat[2]) @ array([bx, by, bz])


                b_line = GLLinePlotItem(
                    pos=[p, p+B_p*self.bfg_lp_scale],
                    color=(0.0, 1.0, 1.0, alpha),
                    antialias=self.data.config["ov_use_antialiasing"],
                    width=1)
                b_line.setDepthValue(0)
                lineplots.append(b_line)
        else:
            lineplots = None

        t1 = time()
        print(f"[DEBUG] make_B_fieldgrid() time: {round((t1-t0)*1E6,1)} us")

        return scatterplot, lineplots

    def make_vector_pos(self):  # TODO: Remove (after verification complete)
        point = self.points[self.data.i_satpos]

        rlonglat = conv_ECEF_geoc(point)
        xcalc = rlonglat[0] * np.cos(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        ycalc = rlonglat[0] * np.sin(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        zcalc = rlonglat[0] * np.cos(np.pi / 2 - rlonglat[2])

        vector = GLLinePlotItem(
            pos=[np.array([0, 0, 0]), np.array([xcalc, ycalc, zcalc])],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["ov_use_antialiasing"],
            width=1)
        vector.setDepthValue(0)
        return vector


    def satellite_update(self):

        xyz_sat = self.points[self.data.i_satpos]
        xy0_sat = array([xyz_sat[0], xyz_sat[1], 0])

        # print("[DEBUG] xyz_sat|ECI :", xyz_sat.round(0))
        # print("[DEBUG] xyz_sat|ECEF:", (R_ECI_ECEF(self.th_E).transpose()@xyz_sat).round(0))


        # ==== FRAME TRIPODS
        # Update ECEF tripod:
        if self.data.config["ov_rotate_earth"]:
            self.th_E = (self.data.i_satpos * self.dth_E + self.th_E0) % (2 * pi)
        Ri_ECEF_ECI = R_ECEF_ECI(self.th_E)
        self.frame_ECEF.set_r(Ri_ECEF_ECI)
        if self.data.config["ov_draw"]["tripod_ECEF"] and self.data.config["ov_anim"]["tripod_ECEF"]:
            updateframe(self.frame_ECEF_plotitems, self.frame_ECEF, plotscale=self.tripod_ECEF_ps)

        # Update NED tripod:
        # xyz_ECEF = R_ECI_ECEF(self.th_E)@self.points[self.data.i_satpos]
        self.rlonglat = conv_ECI_geoc(xyz_sat)
        Ri_NED_ECI = R_NED_ECI(self.rlonglat[1], self.rlonglat[2]).transpose()  # TODO Homogenise transpose
        self.frame_NED.set_o(xyz_sat)
        self.frame_NED.set_r(Ri_NED_ECI)
        if self.data.config["ov_draw"]["tripod_NED"] and self.data.config["ov_anim"]["tripod_NED"]:
            updateframe(self.frame_NED_plotitems, self.frame_NED, plotscale=self.tripod_NED_ps)

        # Update SI tripod:
        Ri_ECI_SI = self.Rta_ECI_SI[self.data.i_satpos]
        self.frame_SI.set_o(xyz_sat)
        self.frame_SI.set_r(Ri_ECI_SI)
        if self.data.config["ov_draw"]["tripod_SI"] and self.data.config["ov_anim"]["tripod_SI"]:
            updateframe(self.frame_SI_plotitems, self.frame_SI, plotscale=self.tripod_SI_ps)

        # Update B tripod:
        self.ab = array([self.ma[self.data.i_satpos], 0, 0])
        Ri_ECI_B = R_SI_B(self.ab) @ Ri_ECI_SI
        self.frame_B.set_o(xyz_sat)
        self.frame_B.set_r(Ri_ECI_B)
        if self.data.config["ov_draw"]["tripod_B"] and self.data.config["ov_anim"]["tripod_B"]:
            updateframe(self.frame_B_plotitems, self.frame_B, plotscale=self.tripod_B_ps)


        # ==== SATELLITE ITEMS
        if self.data.config["ov_draw"]["satellite"] and self.data.config["ov_anim"]["satellite"]:
            self.satellite.setData(pos=xyz_sat)

        if self.data.config["ov_draw"]["satellite_helpers"] and self.data.config["ov_anim"]["satellite_helpers"]:
            self.vline_sat.setData(pos=[xy0_sat, xyz_sat])
            self.vdot_sat.setData(pos=xy0_sat)

        if self.data.config["ov_draw"]["position_vector"] and self.data.config["ov_anim"]["satellite_helpers"]:
            self.pv_plotitem.setData(pos=[array([0, 0, 0]), xyz_sat])

        if self.data.config["ov_draw"]["velocity_vector"] and self.data.config["ov_anim"]["velocity_vector"]:
            self.vv_plotitem.setData(pos=[xyz_sat, xyz_sat+self.v_xyz[self.data.i_satpos]*self.vv_scale])
        # self.huv_plotitem.setData(pos=[xyz_sat, xyz_sat+self.huv*self.huv_scale])


        # ==== MAGNETIC FIELD
        # Calculate magnetic field vector
        _, _, _, bx, by, bz, _ = igrf_value(
            180 / pi * self.rlonglat[2],
            180 / pi * wrap(self.rlonglat[1] - self.th_E, 2 * pi),
            1E-3*(self.rlonglat[0]-self.data.orbit.body.r),
            self.year)

        # Transform to ECI and update plotitem
        B_NED = array([bx, by, bz])
        self.B = R_NED_ECI(self.rlonglat[1], self.rlonglat[2]) @ B_NED
        if self.data.config["ov_draw"]["B_vector"] and self.data.config["ov_anim"]["B_vector"]:
            self.bv_plotitem.setData(pos=[xyz_sat, xyz_sat+self.B*self.bv_scale])

        # # TODO: De-shittify
        # rlonglat = conv_ECEF_geoc(xyz_sat)
        # xcalc = rlonglat[0] * np.cos(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        # ycalc = rlonglat[0] * np.sin(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        # zcalc = rlonglat[0] * np.cos(np.pi / 2 - rlonglat[2])
        # self.vector_pos.setData(pos=[np.array([0, 0, 0]),
        #                              np.array([xcalc, ycalc, zcalc])])


        # TODO: De-shittify
        # r, long, lat = rlonglat
        # ps_tripod_NED = 0.25*self.ps
        # self.tripod_NED_components[0].setData(pos=[
        #     conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+xyz_sat,
        #     conv_ECEF_NED(np.array([ps_tripod_NED, 0, 0]), r, long, lat)+xyz_sat])
        # self.tripod_NED_components[1].setData(pos=[
        #     conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+xyz_sat,
        #     conv_ECEF_NED(np.array([0, ps_tripod_NED, 0]), r, long, lat)+xyz_sat])
        # self.tripod_NED_components[2].setData(pos=[
        #     conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+xyz_sat,
        #     conv_ECEF_NED(np.array([0, 0, ps_tripod_NED]), r, long, lat)+xyz_sat])

        # Update earth model
        if (
            self.data.config["ov_draw"]["earth_model"]
            and self.data.config["ov_rotate_earth"]
            and self.data.config["ov_anim"]["earth_model"]
        ):
            self.earth_meshitem.rotate(self.dth_E * 180 / pi, 0, 0, 1, local=False)

        # for item in (earth_meshitem, tripod_ECEF_x, tripod_ECEF_y, tripod_ECEF_z):  # TODO: Remove deprecated
        #     item.rotate(360/(24/1.5*subdivisions), 0, 0, 1, local=False)
        # for tripod_component in (tripod_ECEF_x, tripod_ECEF_y, tripod_ECEF_z):

        self.data.i_satpos = (self.data.i_satpos + 1) % self.data.orbit_subs