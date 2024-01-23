
import numpy as np
from numpy import pi, sin, cos, tan, arcsin, arccos, arctan, arctan2
import matplotlib.pyplot as plt
from time import time
from PyQt5 import QtCore
from scipy.special import jv

import pyqtgraph as pg
from pyqtgraph.opengl import (
    GLGridItem,
    GLLinePlotItem,
    GLMeshItem,
    GLScatterPlotItem,
    GLViewWidget,
    MeshData,
)


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

class Orbit:
    def __init__(self, body, a, e, i, raan, argp, ta,
                 invert_fix=False, spacing="isochronal"):
        if 0 > e >= 1:
            raise ValueError(f"Eccentricity value {e} not allowed (only elliptical orbits are supported)!")
        if a <= 0:
            raise ValueError(f"Invalid semi-major axis specified {a}!")

        self.d2r = pi / 180
        self.body = body

        # Using angle inversion to fix a bug where inclination and RAAN go in the opposite direction
        # TODO: Find the source of the bug and fix properly
        if invert_fix:
            inv = -1
        else:
            inv = 1

        # All internal angles defined in radians
        self.a = a                          # Semi-major axis
        self.e = e                          # Eccentricity
        self.i = self.d2r*(inv*i % 180)         # Inclination
        self.raan = self.d2r*(inv*raan % 360)   # Right ascention of the ascending node
        self.argp = self.d2r*(argp % 360)   # Argument of periapsis
        self.ta = self.d2r*(ta % 360)       # True anomaly


        # General orbital properties
        self.period = self.get_period()     # Orbital period
        self.b = self.a*(1-self.e**2)**0.5  # Semi-minor axis

    def orbit_transformation_matrix(self):
        T = np.zeros((3, 3))

        # "Fixed" version with RAAN and argument of periapsis switched around
        T[0][0] = cos(self.argp)*cos(self.raan) - sin(self.argp)*cos(self.i)*sin(self.raan)
        T[0][1] = sin(self.argp)*cos(self.raan) + cos(self.argp)*cos(self.i)*sin(self.raan)
        T[0][2] = sin(self.i)*sin(self.raan)
        T[1][0] = -cos(self.argp)*sin(self.raan) - sin(self.argp)*cos(self.i)*cos(self.raan)
        T[1][1] = -sin(self.argp)*sin(self.raan) + cos(self.argp)*cos(self.i)*cos(self.raan)
        T[1][2] = sin(self.i)*cos(self.raan)
        T[2][0] = sin(self.i)*sin(self.argp)
        T[2][1] = -sin(self.i)*cos(self.argp)
        T[2][2] = cos(self.i)

        # # Unmodified from https://en.wikipedia.org/wiki/Orbital_elements#Euler_angle_transformations
        # T[0][0] = cos(self.raan)*cos(self.argp) - sin(self.raan)*cos(self.i)*sin(self.argp)
        # T[0][1] = sin(self.raan)*cos(self.argp) + cos(self.raan)*cos(self.i)*sin(self.argp)
        # T[0][2] = sin(self.i)*sin(self.argp)
        # T[1][0] = -cos(self.raan)*sin(self.argp) - sin(self.raan)*cos(self.i)*cos(self.argp)
        # T[1][1] = -sin(self.raan)*sin(self.argp) + cos(self.raan)*cos(self.i)*cos(self.argp)
        # T[1][2] = sin(self.i)*cos(self.argp)
        # T[2][0] = sin(self.i)*sin(self.raan)
        # T[2][1] = -sin(self.i)*cos(self.raan)
        # T[2][2] = cos(self.i)

        return T

    def get_i(self):
        return self.i/self.d2r

    def get_period(self):
        return 2*pi * (self.a**3 / self.body.gm)**0.5

    def equation_of_the_center(self, M, e, order=6, method="B"):
        if method == "A":  # Fixed order e**7 truncated (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
            v = M
            v += 2*e*sin(M)
            v += 5/4*e**2*sin(2*M)
            v += e**3/12*(13*sin(3*M) - 3*sin(M))
            v += e**4/96*(103*sin(4*M) - 44*sin(2*M))
            v += e**5/960*(1097*sin(5*M) - 645*sin(3*M) + 50*sin(M))
            v += e**6/960*(1223*sin(6*M) - 902*sin(4*M) + 85*sin(2*M))

        if method == "B":  # General expression in terms of Bessel functions of the first kind (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
            v = M  # If e == 0 (circular orbit) don't bother
            if 0 < e < 1:
                b = 1 / e * (1 - (1 - e * e) ** 0.5)
                for s in range(1, order):
                    bt = 0
                    for p in range(1, order):
                        bt += b**p*(jv(s-p, s*e)+jv(s+p, s*e))
                    v += 2/s * (jv(s, s*e) + bt)*sin(s*M)

        return v

    def draw(self, subdivisions=128, spacing="isochronal", order=12, method="B"):

        t0 = time()
        if spacing in ("equitemporal", "isochronal"):
            if self.e > 0.5:
                print("WARNING! Isochronal point generation of orbits with eccentricity > 0.5 may be subjected to oscillations. Consider increasing the order of the method, or using equidistant instead")

            # Spacing of mean anomaly
            mean_anomaly = np.linspace(0, 2 * pi, subdivisions + 1)[:-1]
            angulars = np.zeros(len(mean_anomaly))
            for i in range(len(mean_anomaly)):
                angulars[i] = self.equation_of_the_center(mean_anomaly[i],
                                                          self.e,
                                                          order=order,
                                                          method=method)


        elif spacing == "equidistant":
            # Using polar coordinates:
            angulars = np.linspace(0, 2*pi, subdivisions+1)[:-1]
            # angulars = np.linspace(0, 2*pi, subdivisions)

        else:
            raise ValueError("Valid spacing settings: 'equidistant', 'isochronal'")

        # Radial components relative to focus:
        radials = self.a*(1-self.e**2) / (1 + self.e * cos(angulars))
        # # Radial components centered:
        # radials = self.b/(1-(self.e*cos(angulars))**2)**0.5

        # Flat coordinates
        xf = radials * cos(angulars)
        yf = radials * sin(angulars)
        zf = np.zeros(len(xf))

        x = np.zeros(len(xf))
        y = np.zeros(len(xf))
        z = np.zeros(len(xf))

        T = self.orbit_transformation_matrix()

        for i in range(len(xf)):
            x[i], y[i], z[i] = np.dot(T, np.array([xf[i], yf[i], zf[i]]))

        print(f"draw() time: {round((time()-t0)*1E6, 1)} us")
        return [x, y, z]

    @staticmethod
    def conv_ECI_GC(x_sat, x_zero):

        def unit(vector):
            return vector / np.linalg.norm(vector)

        def vector_angle(a, b):
            au, bu = unit(a), unit(b)
            return np.arccos(np.dot(au, bu))

        x_sat_p = np.array([x_sat[0], x_sat[1], 0])
        print(f"x_sat_p = {x_sat_p}")

        tau = vector_angle(x_zero, x_sat_p)
        delta = vector_angle(x_sat, x_sat_p)

        print(f"tau   = {round(tau * 180 / np.pi, 1)} deg")
        print(f"delta = {round(delta * 180 / np.pi, 1)} deg")

        R_ECI_GC = np.array([
            [-sin(delta) * cos(delta), -sin(delta) * sin(delta), cos(delta)],
            [-sin(tau), cos(delta), 0],
            [-cos(delta) * cos(delta), -cos(delta) * sin(delta), cos(delta)],
        ])

        return R_ECI_GC@x_sat

    @staticmethod
    def conv_ECEF_geoc(coor_ECEF):

        def unit(vector):
            return vector / np.linalg.norm(vector)

        def vector_angle(a, b):
            au, bu = unit(a), unit(b)
            return np.arccos(np.dot(au, bu))

        if len(coor_ECEF) != 3:
            raise AssertionError(f"coor_ECEF is length {len(coor_ECEF)} but must be length 3!")

        # Project coor_ECEF onto XY plane:
        coor_pXY = np.array([coor_ECEF[0], coor_ECEF[1], 0])

        print(f"[DEBUG] coor_ECEF = {coor_ECEF}")
        print(f"[DEBUG] coor_pXY = {coor_pXY}")

        xaxis_ECEF = np.array([1, 0, 0])

        longitude = coor_ECEF[1] / abs(coor_ECEF[1]) * vector_angle(xaxis_ECEF, coor_pXY)
        latitude = coor_ECEF[2] / abs(coor_ECEF[2]) * vector_angle(coor_ECEF, coor_pXY)
        r = np.linalg.norm(coor_ECEF)

        print(f"[DEBUG] longitude   = {round(longitude * 180 / np.pi, 1)} deg")
        print(f"[DEBUG] latitude = {round(latitude * 180 / np.pi, 1)} deg")
        print(f"[DEBUG] r = {round(r / 1E3, 0)} km")

        return np.array([longitude, latitude, r])


    def calc(self, ):
        pass

    def plot_simple(self, coordinates):
        x, y, z = coordinates
        fig, ax = plt.subplots()
        ax.plot(x, y, "r")
        ax.set(aspect=1)
        plt.show()

    def print_properties(self):
        print("To be implemented...")


class Body:
    def __init__(self, name: str, m, r):
        self.name = name
        self.m = m
        self.g = 6.67430E-11
        self.gm = self.m*self.g
        self.r = r


class Earth(Body):
    def __init__(self):
        super().__init__("Earth", 5.9722E24, 6.371E6)



def sign(number, rd=15):
    # if round(number, rd) == 0:
    if number == 0:
        return 1
    else:
        return number/abs(number)


def conv_ECEF_geoc(coor_ECEF, rd=6):

    if len(coor_ECEF) != 3:
        raise AssertionError(f"coor_ECEF is length {len(coor_ECEF)} but must be length 3!")

    x, y, z = coor_ECEF[0], coor_ECEF[1], coor_ECEF[2]

    # Subvert the singularities at -90 and 90 degrees pitch
    # Using rounding to fix floating-point errors whilst sacrificing um
    # precision around singularities (who cares about that anyway?)
    # and increases function evaluation from 8 us to 16 us
    if round(x, rd) == 0 and round(y, rd) == 0:
        if round(z, rd) == 0:
            raise ValueError("coor_ECEF has no defined direction, as its length is 0!")
        else:
            r = abs(z)
            longitude = 0
            latitude = sign(z)*np.pi/2

    else:
        r = (x**2 + y**2 + z**2)**0.5
        longitude = sign(y)*np.arccos(x/(x**2 + y**2)**0.5)
        latitude = np.pi/2-np.arccos(z/r)

        print(f"[DEBUG] x: {x}, y: {y}, sign(y): {sign(y)}")
        print(f"[DEBUG] x/(x**2 + y**2)**0.5: {x/(x**2 + y**2)**0.5}")
        print(f"[DEBUG] arccos(x/(x**2 + y**2)**0.5): {180/np.pi*np.arccos(x/(x**2 + y**2)**0.5)} deg")

    print(f"[DEBUG] long: {round(180/np.pi*longitude,1)} deg")
    print(f"[DEBUG] lat:  {round(180/np.pi*latitude,1)} deg")
    print("")
    return np.array([r, longitude, latitude])


def wrap(angle, angle_range):
    angle_wrapped = (angle + angle_range / 2) % angle_range - angle_range / 2
    if angle_wrapped == -angle:
        angle_wrapped = -angle_wrapped
    # print(f"[DEBUG] wrap({180/np.pi*angle}, {180/np.pi*angle_range}) = {180/np.pi*angle_wrapped} deg")
    return angle_wrapped

def RX(a):
    sa, ca = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls (7.4 us -> 5.8 us)
    return np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])

def RY(a):
    sa, ca = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls
    return np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])

def RZ(a):
    sa, ca = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls
    return np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])

def conv_ECEF_NED(coor, r, long, lat):
    # long = -long
    # lat = -lat
    # long = wrap(long+np.pi/2, 2*np.pi)
    # lat = wrap(lat-np.pi/2, np.pi)
    print("EFFECTIVE VALUES:")
    print(f"[DEBUG] long: {round(180/np.pi*long,1)} deg")
    print(f"[DEBUG] lat:  {round(180/np.pi*lat,1)} deg")
    print("")

    # R_NED_ENU = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]])
    R_NED_ENU = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # TODO: REMOVE
    # return np.dot(R_X, np.dot(R_Z, np.dot(R_NED_ENU, coor)))
    # return np.dot(R_X, np.dot(R_Z, coor))
    coor = np.dot(RZ(np.pi/2), coor)    # First rotate 90 deg around Z
    coor = np.dot(RY(np.pi/2), coor)    # First rotate 90 deg around X

    # coor = np.dot(RX(0*np.pi/2), np.dot(RZ(np.pi/2), coor))
    # coor = np.dot(np.dot(RX(0*np.pi/2), RZ(np.pi/2)), coor)
    coor = np.dot(RZ(long), coor)
    return coor


class OrbitVisualizer(GLViewWidget):
    def __init__(self, datapool):
        super().__init__()

        self.data = datapool

        self.points = self.generate_points()

        self.c = self.data.config["orbit_plotcolours"]
        self.ps = self.data.config["orbit_plotscale"]  # Plot scale

        self.setCameraPosition(distance=3*self.ps)

        # Generate grid
        self.grid = self.make_grid()
        self.addItem(self.grid)

        # Generate ECI tripod_components
        self.ECI_tripod_components = self.make_ECI_tripod()
        [self.addItem(comp) for comp in self.ECI_tripod_components]

        # Generate ECEF tripod_components
        self.ECEF_tripod_components = self.make_ECEF_tripod()
        [self.addItem(comp) for comp in self.ECEF_tripod_components]

        # Generate Earth meshitem
        if self.data.config["orbit_draw_earthmodel"]:
            self.earth_meshitem = self.make_earth_meshitem()
            self.addItem(self.earth_meshitem)

        # Generate orbit lineplot
        self.orbit_lineplot = self.make_orbit_lineplot()
        self.addItem(self.orbit_lineplot)

        if self.data.config["orbit_draw_scatterplot"]:
            self.orbit_scatterplot = self.make_orbit_scatterplot()
            self.addItem(self.orbit_scatterplot)

        if self.data.config["orbit_draw_helpers"]:
            self.orbit_flatcircle, self.orbit_vlines = self.make_orbit_helpers()
            self.addItem(self.orbit_flatcircle)
            [self.addItem(vline) for vline in self.orbit_vlines]

        # Visualize satellite
        self.satellite, self.vline_sat, self.vdot_sat = self.make_satellite()
        self.addItem(self.satellite)
        if self.data.config["orbit_draw_helpers"]:
            self.addItem(self.vline_sat)
            self.addItem(self.vdot_sat)

        # DEBUGGING VECTOR FOR RLONGLAT - TODO: Remove
        self.vector_pos = self.make_vector_pos()
        self.addItem(self.vector_pos)

        # Generate NED tripod_components
        self.NED_tripod_components = self.make_NED_tripod()
        [self.addItem(comp) for comp in self.NED_tripod_components]


        # Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.satellite_update)
        self.timer.start(1000)


    @staticmethod
    def hex2rgb(hex: str):
        """Converts a hex colour string (e.g. '#3faa00') to [0, 1] rgb values"""
        hex = hex.lstrip("#")
        if len(hex) == 8:
            rgb255 = list(int(hex[i:i + 2], 16) for i in (0, 2, 4, 6))
        else:
            rgb255 = list(int(hex[i:i + 2], 16) for i in (0, 2, 4))
        return [c/255 for c in rgb255]

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

    def make_ECI_tripod(self):
        antialias = self.data.config["orbit_use_antialiasing"]
        ps_ECI_tripod = 1.5*self.ps
        ECI_tripod_x = GLLinePlotItem(
            pos=np.column_stack(((0, ps_ECI_tripod), (0, 0), (0, 0))),
            color="#ff0000ff", width=2, antialias=antialias)
        ECI_tripod_y = GLLinePlotItem(
            pos=np.column_stack(((0, 0), (0, ps_ECI_tripod), (0, 0))),
            color="#00ff00ff", width=2, antialias=antialias)
        ECI_tripod_z = GLLinePlotItem(
            pos=np.column_stack(((0, 0), (0, 0), (0, ps_ECI_tripod))),
            color="#0000ffff", width=2, antialias=antialias)
        tripod_components = (ECI_tripod_x, ECI_tripod_y, ECI_tripod_z)
        for tripod_component in tripod_components:
            tripod_component.setDepthValue(10)
        return tripod_components

    def make_ECEF_tripod(self):
        # Add Earth-fixed tripod
        antialias = self.data.config["orbit_use_antialiasing"]
        ps_ECEF_tripod = 0.6378*self.ps
        ECEF_tripod_x = GLLinePlotItem(
            pos=np.column_stack(((0, ps_ECEF_tripod), (0, 0), (0, 0))),
            color="#ff000060", width=3, antialias=antialias)
        ECEF_tripod_y = GLLinePlotItem(
            pos=np.column_stack(((0, 0), (0, ps_ECEF_tripod), (0, 0))),
            color="#00ff0060", width=3, antialias=antialias)
        ECEF_tripod_z = GLLinePlotItem(
            pos=np.column_stack(((0, 0), (0, 0), (0, ps_ECEF_tripod))),
            color="#0000ff60", width=3, antialias=antialias)
        tripod_components = (ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z)
        for tripod_component in tripod_components:
            tripod_component.setDepthValue(10)
        return tripod_components

    def make_NED_tripod(self):
        # Add NED tripod
        antialias = self.data.config["orbit_use_antialiasing"]
        ps_NED_tripod = 0.25*self.ps

        point = np.array([
            self.points[0][self.data.i_satpos],
            self.points[1][self.data.i_satpos],
            self.points[2][self.data.i_satpos]])

        r, long, lat = conv_ECEF_geoc(point)

        point_t = conv_ECEF_NED(point, r, long, lat)

        NED_tripod_x = GLLinePlotItem(
            pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
                 conv_ECEF_NED(np.array([ps_NED_tripod, 0, 0]), r, long, lat)+point],
            color="#ff0000aa", width=3, antialias=antialias)
        NED_tripod_y = GLLinePlotItem(
            pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
                 conv_ECEF_NED(np.array([0, ps_NED_tripod, 0]), r, long, lat)+point],
            color="#00ff00aa", width=3, antialias=antialias)
        NED_tripod_z = GLLinePlotItem(
            pos=[conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
                 conv_ECEF_NED(np.array([0, 0, ps_NED_tripod]), r, long, lat)+point],
            color="#0000ffaa", width=3, antialias=antialias)
        tripod_components = (NED_tripod_x, NED_tripod_y, NED_tripod_z)
        for tripod_component in tripod_components:
            tripod_component.setDepthValue(10)
        return tripod_components

    def make_earth_meshitem(self, alpha=1.0):
        sr = self.data.config["orbit_earthmodel_resolution"]

        mesh = MeshData.sphere(rows=sr[0], cols=sr[1], radius=Earth().r)

        ec = self.data.config["orbit_earthmodel_colours"]

        # Pre-allocate empty array for storing colour data for each mesh triangle
        colours = np.ones((mesh.faceCount(), 4), dtype=float)

        # Add ocean base layer
        colours[:, 0:3] = self.hex2rgb(ec["ocean"])

        # Add polar ice
        pole_line = (int(0.15*sr[0])*sr[1]+1, (int(sr[0]*0.75)*sr[1])+1)
        colours[:pole_line[0], 0:3] = self.hex2rgb(ec["ice"])
        colours[pole_line[1]:, 0:3] = self.hex2rgb(ec["ice"])

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
                    colours[i_f, 0:3] = self.hex2rgb(ec["green2"])
                else:
                    colours[i_f, 0:3] = self.hex2rgb(ec["green1"])

        # Add cloud cover
        i_cloud = []
        for i_f in range(len(colours)):
            # Determine chance of cloud
            p_cloud = 0.1
            if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
                p_cloud += 0.3

            if np.random.random() <= p_cloud:
                i_cloud.append(i_f)
                colours[i_f, 0:3] = self.hex2rgb(ec["cloud"])

        # Apply alpha (does not work)
        colours[:, 3] = alpha

        # Apply the colour data to the mesh triangles
        mesh.setFaceColors(colours)

        # Embed the data into a GLMeshItem (that Qt can work with)
        meshitem = GLMeshItem(
            meshdata=mesh,
            smooth=self.data.config["orbit_earthmodel_smoothing"],
            computeNormals=True,
            shader="shaded",
        )

        meshitem.setDepthValue(-2)

        return meshitem


    def make_orbit_lineplot(self):
        # Depending on 'orbit_endpatching' setting, patch gap at pericentre
        if self.data.config["orbit_endpatching"]:
            points = [np.append(self.points[i], self.points[i][0]) for i in range(len(self.points))]
        else:
            points = self.points
        lineplot = GLLinePlotItem(
            pos=np.column_stack([points[0], points[1], points[2]]),
            color=self.c[self.data.config["orbit_preferred_colour"]],
            width=2,
            antialias=self.data.config["orbit_use_antialiasing"]
        )
        lineplot.setDepthValue(0)
        return lineplot


    def make_orbit_scatterplot(self):

        scatterplot = GLScatterPlotItem(
            pos=np.column_stack([self.points[0], self.points[1], self.points[2]]),
            color=self.hex2rgb(self.c[self.data.config["orbit_preferred_colour"]]),
            size=4,
            pxMode=True)
        scatterplot.setDepthValue(0)
        return scatterplot


    def make_orbit_helpers(self):
        # Add flat circle

        # Always patch this circle:
        points = [np.append(self.points[i], self.points[i][0]) for i in range(len(self.points))]
        flatcircle = GLLinePlotItem(
            pos=np.column_stack([points[0], points[1], np.zeros(len(points[0]))]),
            color=(1, 1, 1, 0.2),
            width=1,
            antialias=self.data.config["orbit_use_antialiasing"])
        flatcircle.setDepthValue(0)

        # Add vlines
        vlines = []
        for i in range(len(self.points[0])):
            points = np.column_stack([
                [self.points[0][i], self.points[0][i]],
                [self.points[1][i], self.points[1][i]],
                [0, self.points[2][i]],
            ])
            vline = GLLinePlotItem(
                pos=points,
                color=(1, 1, 1, 0.1),
                antialias=self.data.config["orbit_use_antialiasing"],
                width=1)
            vline.setDepthValue(0)
            vlines.append(vline)


        return flatcircle, vlines


    def make_satellite(self):
        # Draw satellite
        i_satpos = self.data.i_satpos
        sat = GLScatterPlotItem(
            pos=np.column_stack([
                self.points[0][i_satpos],
                self.points[1][i_satpos],
                self.points[2][i_satpos]]),
            color=self.hex2rgb(self.c[self.data.config["orbit_preferred_colour"]]),
            # color=(1.0, 1.0, 0.0, 1.0),
            size=8,
            pxMode=True)
        sat.setDepthValue(1)

        vline_sat = GLLinePlotItem(
            pos=np.array(np.column_stack([
                [self.points[0][i_satpos], self.points[0][i_satpos]],
                [self.points[1][i_satpos], self.points[1][i_satpos]],
                [0, self.points[2][i_satpos]]])),
            color=(1.0, 1.0, 1.0, 0.8),
            antialias=self.data.config["orbit_use_antialiasing"],
            width=1)

        vline_sat.setDepthValue(1)

        vdot_sat = GLScatterPlotItem(
            pos=np.column_stack([
                self.points[0][i_satpos],
                self.points[1][i_satpos],
                0]),
            color=(1.0, 1.0, 1.0, 0.8),
            size=3,
            pxMode=True)
        vdot_sat.setDepthValue(1)

        return sat, vline_sat, vdot_sat


    def make_vector_pos(self):
        point = np.array([
            self.points[0][self.data.i_satpos],
            self.points[1][self.data.i_satpos],
            self.points[2][self.data.i_satpos]])

        rlonglat = conv_ECEF_geoc(point)
        xcalc = rlonglat[0] * np.cos(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        ycalc = rlonglat[0] * np.sin(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        zcalc = rlonglat[0] * np.cos(np.pi / 2 - rlonglat[2])

        vector = GLLinePlotItem(
            pos=[np.array([0, 0, 0]), np.array([xcalc, ycalc, zcalc])],
            color=(1.0, 1.0, 0, 0.8),
            antialias=self.data.config["orbit_use_antialiasing"],
            width=1)
        vector.setDepthValue(0)
        return vector


    def satellite_update(self):
        do_anim = {
            "satellite": True,
            "satellite_helpers": True,
            "earthmodel": True,
            "earthframe": True,
            "NED_tripod": True,
        }

        x = self.points[0][self.data.i_satpos]
        y = self.points[1][self.data.i_satpos]
        z = self.points[2][self.data.i_satpos]

        if do_anim["satellite"]:
            self.satellite.setData(pos=np.column_stack([x, y, z]))

        if do_anim["satellite_helpers"]:
            self.vline_sat.setData(pos=np.column_stack([[x, x], [y, y], [0, z]]))
            self.vdot_sat.setData(pos=np.column_stack([x, y, 0]))


        # TODO: De-shittify
        rlonglat = conv_ECEF_geoc(np.array([x, y, z]))
        xcalc = rlonglat[0] * np.cos(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        ycalc = rlonglat[0] * np.sin(rlonglat[1]) * np.sin(np.pi / 2 - rlonglat[2])
        zcalc = rlonglat[0] * np.cos(np.pi / 2 - rlonglat[2])
        self.vector_pos.setData(pos=[np.array([0, 0, 0]),
                                     np.array([xcalc, ycalc, zcalc])])


        # TODO: De-shittify
        r, long, lat = rlonglat
        point = np.array([x, y, z])
        ps_NED_tripod = 0.25*self.ps
        self.NED_tripod_components[0].setData(pos=[
            conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
            conv_ECEF_NED(np.array([ps_NED_tripod, 0, 0]), r, long, lat)+point])
        self.NED_tripod_components[1].setData(pos=[
            conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
            conv_ECEF_NED(np.array([0, ps_NED_tripod, 0]), r, long, lat)+point])
        self.NED_tripod_components[2].setData(pos=[
            conv_ECEF_NED(np.array([0, 0, 0]), r, long, lat)+point,
            conv_ECEF_NED(np.array([0, 0, ps_NED_tripod]), r, long, lat)+point])

        # for item in (earth_meshitem, ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z):
        #     item.rotate(360/(24/1.5*subdivisions), 0, 0, 1, local=False)
        # for tripod_component in (ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z):

        self.data.i_satpos = (self.data.i_satpos + 1) % self.data.orbit_subs


#
# orbit3 = Orbit(earth, (earth.r + h)/(1-e), e, 20, 0, 0, 0)
# coords3 = orbit3.draw(subdivisions=subdivisions, spacing="isochronal")
#
# print(f"Period: {round(orbit3.period,0)} s (= {round(orbit3.period/60, 3)} min")


#
# def satellite_update():
#     global sat, vline_sat, vdot_sat, i_satpos, coords3
#     global earth_meshitem, ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z
#
#     x, y, z = coords3[0][i_satpos], coords3[1][i_satpos], coords3[2][i_satpos]
#
#     sat.setData(pos=[x, y, z])
#     vline_sat.setData(pos=np.column_stack([[x, x], [y, y], [0, z]]))
#     vdot_sat.setData(pos=[x, y, 0])
#     for item in (earth_meshitem, ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z):
#         item.rotate(360/(24/1.5*subdivisions), 0, 0, 1, local=False)
#     # for tripod_component in (ECEF_tripod_x, ECEF_tripod_y, ECEF_tripod_z):
#
#     i_satpos = (i_satpos + 1) % len(coords3[0])
#
#
# # Timer
# t = QtCore.QTimer()
# t.timeout.connect(satellite_update)
# t.start(40)
#
# #     w.addItem(gl.GLLinePlotItem(
# #         pos=np.column_stack([coord[0], coord[1], coord[2]]),
# #         color=plotcolors2[i],
# #         width=2,
# #         antialias=True
# #     ))
#
# # ball = gl.GLSurfacePlotItem(x=x_ball, y=y_ball, z=z_ball,
# #                             shader="shaded",
# #                             color="c")
# # w.addItem(ball)
#
# # w.addItem(plt2)
#
# if __name__ == '__main__':
#     pg.exec()
#     # Manual garbage collection:
#     for var in ["sat", "vline_sat", "vdot_sat", "i_satpos", "coords3",
#                 "earth_meshitem", "ECEF_tripod_x", "ECEF_tripod_y", "ECEF_tripod_z"]:
#         del globals()[var]