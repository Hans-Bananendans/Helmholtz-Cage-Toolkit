
import numpy as np
from numpy import pi, sin, cos, tan, arcsin, arccos, arctan, arctan2
import matplotlib.pyplot as plt
from time import time
from PyQt5 import QtCore
from scipy.special import jv

import pyqtgraph as pg
import pyqtgraph.opengl as gl

# Goal: define and describe an orbit fully from its six orbital elements:
# - Generalized OrbitVisualizer class that can:
#     - Be docked into existing PyQt5 Window
#     - Gather orbits
#     - Gather body
#     - Orbit patch function for drawing
#     - Generalized update class, that can be synchronized externally
# - Support for 5 coordinate systems:
#     - GI (General Inertial of Earth (ECI))
#     - EF (Earth Fixed (ECEF))
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
    def __init__(self, body, a, e, i, raan, argp, ta, invert_fix=False):
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

    def equation_of_the_center(self, M, e, order=6, method="A"):
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

    def draw(self, subdivisions=128, spacing="equidistant", order=12, method="B"):

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

        print(f"draw() time: {round((time()-t0)*1E6, 1)} ns")
        return x, y, z

    def calc(self, ):
        pass

    def plot_simple(self, coordinates):
        x, y, z = coordinates
        fig, ax = plt.subplots()
        ax.plot(x, y, "r")
        ax.set(aspect=1)
        plt.show()


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


earth = Earth()

h = 350E3
e = 0.5
a = h/(1-e)
subdivisions = 128


orbit_e = Orbit(earth, earth.r, 0, 0, 0, 0, 0)
coords_e = orbit_e.draw(subdivisions=128)
# orbit1.plot_simple([x, y, z])

orbit1 = Orbit(earth, earth.r + h, 0, 0, 0, 0, 0)
coords1 = orbit1.draw(subdivisions=subdivisions)

orbit2 = Orbit(earth, (earth.r + h)/(1-e), e, 30, 0, 0, 0)
coords2 = orbit2.draw(subdivisions=subdivisions)

orbit3 = Orbit(earth, (earth.r + h)/(1-e), e, 20, 0, 0, 0)
coords3 = orbit3.draw(subdivisions=subdivisions, spacing="isochronal")

print(f"Period: {round(orbit3.period,0)} s (= {round(orbit3.period/60, 3)} min")

o = 7
ang = 2*pi/60
t0 = time()
print(f"A: {180/pi*orbit3.equation_of_the_center(ang, e, order=o, method='A')}")
ta = time()
print(f"B: {180/pi*orbit3.equation_of_the_center(ang, e, order=o, method='B')}")
tb = time()
print(f"Time A vs. B: {round(1E6*(ta-t0))} ns / {round(1E6*(tb-ta))} ns")


# # ==== Evaluation of equation of the center method
# teval0 = time()
# eval_dummy_orbit = Orbit(earth, earth.r, 0, 0, 0, 0, 0)
# eval_method = "B"
# eval_o = 12
# eval_e = (0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.9)
# eval_subs = 1024
# eval_M = np.linspace(0, 2*pi, eval_subs)
# eval_f = np.zeros((len(eval_e), eval_subs))
# for i_e, ee in enumerate(eval_e):
#     for i_M, M in enumerate(eval_M):
#         eval_f[i_e][i_M] = eval_dummy_orbit.equation_of_the_center(
#             M, ee, order=eval_o, method=eval_method)
# teval1 = time()-teval0
#
# # ==== Evaluation plot
# fig, axe = plt.subplots()
#
# for i_e in range(len(eval_e)):
#     axe.plot(eval_M, eval_f[i_e], label=str(eval_e[i_e]))
# axe.legend()
# axe.set_xlabel("Mean anomaly M (rad)")
# axe.set_ylabel("True anomaly f (rad)")
# axe.set_title(f"Evaluation of equation of the center for order {eval_o} (method {eval_method})\n Evaluation time: {round(teval1*1000,3)} ms")
#
# plt.show()


# ==== General plot settings
coords = (coords1, coords2, coords3)
plotcolors = ("b", "g", "r", "purple", "gray", "cyan", "magenta")
plotcolors2 = ("#ff00ff", "#FF8000", "#00FFFF", "#FFFF00", "#00FF00")
# plotcolors2 = ("magenta", "orange", "cyan", "yellow", "green")

# # ==== Triple 2D plot
# fig, (ax0, ax1, ax2) = plt.subplots(nrows=1, ncols=3, figsize=(12, 4),
#                                     subplot_kw={"aspect": "equal"})
#
# for i, ax in enumerate((ax0, ax1, ax2)):
#     ax.set_title(("YZ", "XZ", "XY")[i])
#     # ax.set(aspect=1)
#     p = ((1, 2), (0, 2), (0, 1))[i]
#
#     # Plot Earth
#     # ax.plot(coords_e[0], coords_e[1], "k")
#     ax.fill(coords_e[0], coords_e[1], edgecolor="k", facecolor="c", alpha=0.3)
#
#     # Plot orbit
#     for j, coord in enumerate(coords):
#         ax.plot(coord[p[0]], coord[p[1]], plotcolors[j])
#     # ax.plot(coords1[p[0]], coords1[p[1]], "b")
#     # ax.plot(coords2[p[0]], coords2[p[1]], "g")
#     # ax.plot(coords3[p[0]], coords3[p[1]], "r")
#
# # plt.show()


# ==== 3D Plot
ax3d = plt.figure().add_subplot(projection="3d")

# Plot tripod
l = 1E7
ax3d.plot((0, l), (0, 0), (0, 0), "r")
ax3d.plot((0, 0), (0, l), (0, 0), "g")
ax3d.plot((0, 0), (0, 0), (0, l), "b")

# Draw ball
r_ball = earth.r
subs = 20
u = np.linspace(0, 2*np.pi, subs)
v = np.linspace(0, np.pi, subs)
x_ball = r_ball * np.outer(np.cos(u), np.sin(v))
y_ball = r_ball * np.outer(np.sin(u), np.sin(v))
z_ball = r_ball * np.outer(np.ones(np.size(u)), np.cos(v))
ax3d.plot_surface(x_ball, y_ball, z_ball, color="c", alpha=0.25)

# Draw orbits
for i, coord in enumerate(coords):
    ax3d.plot(coord[0], coord[1], coord[2], plotcolors[i], label=f"orbit{i+1}")

ax3d.set_aspect("equal")
ax3d.legend()
# plt.show()


# ==== PyQtGraph 3D plot
app = pg.mkQApp("Orbit Visualizer")
w = gl.GLViewWidget()
w.show()
w.setWindowTitle("Orbit Visualizer (window title)")

ps = 1E7    # Plot scale

w.setCameraPosition(distance=3*ps)

# Add horizontal grid
grid = gl.GLGridItem()
grid.setColor((255, 255, 255, 24))
grid.setSpacing(x=ps/4, y=ps/4)  # Comment out this line at your peril...
grid.setSize(x=3*ps, y=3*ps)
grid.setDepthValue(20)
w.addItem(grid)

# Add tripod
ps_GI_tripod = 1.5*ps
GI_tripod_x = gl.GLLinePlotItem(
    pos=np.column_stack(((0, ps_GI_tripod), (0, 0), (0, 0))),
    color="r", width=2, antialias=True)
GI_tripod_y = gl.GLLinePlotItem(
    pos=np.column_stack(((0, 0), (0, ps_GI_tripod), (0, 0))),
    color="g", width=2, antialias=True)
GI_tripod_z = gl.GLLinePlotItem(
    pos=np.column_stack(((0, 0), (0, 0), (0, ps_GI_tripod))),
    color="b", width=2, antialias=True)
for tripod_component in (GI_tripod_x, GI_tripod_y, GI_tripod_z):
    tripod_component.setDepthValue(10)
    w.addItem(tripod_component)

# Add Earth-fixed tripod
ps_EF_tripod = 0.6378*ps
EF_tripod_x = gl.GLLinePlotItem(
    pos=np.column_stack(((0, ps_EF_tripod), (0, 0), (0, 0))),
    color="#ff000060", width=3, antialias=True)
EF_tripod_y = gl.GLLinePlotItem(
    pos=np.column_stack(((0, 0), (0, ps_EF_tripod), (0, 0))),
    color="#00ff0060", width=3, antialias=True)
EF_tripod_z = gl.GLLinePlotItem(
    pos=np.column_stack(((0, 0), (0, 0), (0, ps_EF_tripod))),
    color="#0000ff60", width=3, antialias=True)
for tripod_component in (EF_tripod_x, EF_tripod_y, EF_tripod_z):
    tripod_component.setDepthValue(10)
    w.addItem(tripod_component)

def hex2rgb(hex: str):
    """Converts a hex colour string (e.g. '#3faa00') to [0, 1] rgb values"""
    hex = hex.lstrip("#")
    if len(hex) == 8:
        rgb255 = list(int(hex[i:i + 2], 16) for i in (0, 2, 4, 6))
    else:
        rgb255 = list(int(hex[i:i + 2], 16) for i in (0, 2, 4))
    return [c/255 for c in rgb255]


def generate_earth_mesh(resolution=(16, 16), radius=6.378E6, alpha=0.5):
    sr = resolution  # Sphere resolution
    mesh = gl.MeshData.sphere(rows=sr[0], cols=sr[1], radius=radius)

    earth_colours = {
        "ocean": "#002bff",
        "ice": "#eff1ff",
        "cloud": "#dddddd",
        "green1": "#1b5c0f",
        "green2": "#093800",
        "green3": "#20c700",
        "test": "#ff0000",
    }

    colours = np.ones((mesh.faceCount(), 4), dtype=float)

    # Add ocean base layer
    colours[:, 0:3] = hex2rgb(earth_colours["ocean"])

    # Add polar ice
    pole_line = (int(0.15*sr[0])*sr[1]+1, (int(sr[0]*0.75)*sr[1])+1)
    colours[:pole_line[0], 0:3] = hex2rgb(earth_colours["ice"])
    colours[pole_line[1]:, 0:3] = hex2rgb(earth_colours["ice"])

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
                colours[i_f, 0:3] = hex2rgb(earth_colours["green2"])
            else:
                colours[i_f, 0:3] = hex2rgb(earth_colours["green1"])

    # Add cloud cover
    i_cloud = []
    for i_f in range(len(colours)):
        # Determine chance of cloud
        p_cloud = 0.1
        if i_f-sr[0] in i_land or i_f+sr[0] in i_land:
            p_cloud += 0.3

        if np.random.random() <= p_cloud:
            i_cloud.append(i_f)
            colours[i_f, 0:3] = hex2rgb(earth_colours["cloud"])

    # Apply alpha
    colours[:, 3] = alpha

    mesh.setFaceColors(colours)
    return mesh


# Add Earth mesh
earth_meshitem = gl.GLMeshItem(
    meshdata=generate_earth_mesh(resolution=(16, 24)),
    smooth=True,
    computeNormals=True,
    shader="shaded",
    # setGLOptions="translucent"
)
# earth_meshitem.setDepthValue(10)

w.addItem(earth_meshitem)


# # Add orbit
# orbit1 = gl.GLLinePlotItem(pos=np.column_stack([coords1[0], coords1[1], coords1[2]]),
#                          color=plotcolors[2],
#                          width=2,
#                          antialias=True)
# # orbit1.setDepthValue(10)
# w.addItem(orbit1)


def patch_orbitdata(orbitdata):
    if type(orbitdata) == np.ndarray:
        return np.append(orbitdata, orbitdata[0])
    elif type(orbitdata) == list:
        return orbitdata.append(orbitdata[0])
    else:
        raise TypeError(f"Please fix patch_orbitdata() to handle '{type(orbitdata)}' inputs.")

# Add orbits
for i, coord in enumerate([coords3]):
    w.addItem(gl.GLLinePlotItem(
        pos=np.column_stack([coord[0], coord[1], coord[2]]),
        # pos=np.column_stack([
        #     patch_orbitdata(coord[0]),
        #     patch_orbitdata(coord[1]),
        #     patch_orbitdata(coord[2])]),
        color=plotcolors2[1],
        width=2,
        antialias=True
    ))


# print(len(coords3))
# print(type(coords3))
# print("")
# print(len(coords3[0]))
# print(type(coords3[0]))
# print("")
# print(len(np.zeros(len(coords3[0]))))


# Add flat circle
flatcircle = gl.GLLinePlotItem(
    pos=np.column_stack([coords3[0], coords3[1], np.zeros(len(coords3[0]))]),
    color=(1, 1, 1, 0.2),
    width=1,
    antialias=True)
flatcircle.setDepthValue(1)
w.addItem(flatcircle)

# Add vlines
for i in range(len(coords3[0])):
    pts = np.column_stack([
        [coords3[0][i], coords3[0][i]],
        [coords3[1][i], coords3[1][i]],
        [coords3[2][i], 0],
    ])
    vline = gl.GLLinePlotItem(pos=pts,
                              color=(1, 1, 1, 0.1),
                              antialias=True,
                              width=1)
    vline.setDepthValue(1)
    w.addItem(vline)

# Add drawn scatter points
orbit_scatter = gl.GLScatterPlotItem(
    pos=np.column_stack([coords3[0], coords3[1], coords3[2]]),
    color=tuple(list(hex2rgb(plotcolors2[1]+"FF"))),
    # color=(1.0, 1.0, 0.0, 1.0),
    size=4,
    pxMode=True)
orbit_scatter.setDepthValue(1)
w.addItem(orbit_scatter)


# test = [[1, 1], [2, 2], [3, 3]]
# print(type(np.column_stack(test)))
# print(np.column_stack(test))

# Draw satellite
i_satpos = 0
sat = gl.GLScatterPlotItem(
    pos=np.column_stack([
        coords3[0][i_satpos],
        coords3[1][i_satpos],
        coords3[2][i_satpos]]),
    color=tuple(list(hex2rgb(plotcolors2[1]+"FF"))),
    # color=(1.0, 1.0, 0.0, 1.0),
    size=8,
    pxMode=True)

w.addItem(sat)

vline_sat = gl.GLLinePlotItem(
    pos=np.array(np.column_stack([
        [coords3[0][i], coords3[0][i]],
        [coords3[1][i], coords3[1][i]],
        [coords3[2][i], 0]])),
    color=(1.0, 1.0, 1.0, 0.8),
    antialias=True,
    width=1)

vline_sat.setDepthValue(1)
w.addItem(vline_sat)

vdot_sat = gl.GLScatterPlotItem(
    pos=np.column_stack([
        coords3[0][i_satpos],
        coords3[1][i_satpos],
        0]),
    color=(1.0, 1.0, 1.0, 0.8),
    size=3,
    pxMode=True)
vdot_sat.setDepthValue(1)
w.addItem(vdot_sat)


def satellite_update():
    global sat, vline_sat, vdot_sat, i_satpos, coords3
    global earth_meshitem, EF_tripod_x, EF_tripod_y, EF_tripod_z

    x, y, z = coords3[0][i_satpos], coords3[1][i_satpos], coords3[2][i_satpos]

    sat.setData(pos=[x, y, z])
    vline_sat.setData(pos=np.column_stack([[x, x], [y, y], [0, z]]))
    vdot_sat.setData(pos=[x, y, 0])
    for item in (earth_meshitem, EF_tripod_x, EF_tripod_y, EF_tripod_z):
        item.rotate(360/(24/1.5*subdivisions), 0, 0, 1, local=False)
    # for tripod_component in (EF_tripod_x, EF_tripod_y, EF_tripod_z):

    i_satpos = (i_satpos + 1) % len(coords3[0])


# Timer
t = QtCore.QTimer()
t.timeout.connect(satellite_update)
t.start(40)

#     w.addItem(gl.GLLinePlotItem(
#         pos=np.column_stack([coord[0], coord[1], coord[2]]),
#         color=plotcolors2[i],
#         width=2,
#         antialias=True
#     ))

# ball = gl.GLSurfacePlotItem(x=x_ball, y=y_ball, z=z_ball,
#                             shader="shaded",
#                             color="c")
# w.addItem(ball)

# w.addItem(plt2)

if __name__ == '__main__':
    pg.exec()
    # Manual garbage collection:
    for var in ["sat", "vline_sat", "vdot_sat", "i_satpos", "coords3",
                "earth_meshitem", "EF_tripod_x", "EF_tripod_y", "EF_tripod_z"]:
        del globals()[var]