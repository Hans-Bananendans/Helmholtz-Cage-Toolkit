from time import time

from pyIGRF.calculate import igrf12syn
from scipy.special import jv
from pyqtgraph.opengl import (  # OpenGL extras on top of pyqtgraph import
    GLGridItem,
    GLLinePlotItem,
    GLMeshItem,
    GLScatterPlotItem,
    GLViewWidget,
    MeshData,
)

from helmholtz_cage_toolkit.pg3d import (
    RX, RY, RZ, R,
    PGPoint3D, PGVector3D, PGFrame3D,
    plotgrid, plotpoint, plotpoints, plotvector, plotframe,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
    sign, wrap, uv3d
)

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.orbit import Orbit, Earth
from helmholtz_cage_toolkit.datapool import DataPool
from helmholtz_cage_toolkit.config import config
from helmholtz_cage_toolkit.utilities import cross3d

t0full = time()

# Goals
# 1. Define full toolchain
# 2. Define all inputs and outputs
# 3. Define all i_step-dependent variables to save and pre-allocate space
# 4. Perform pre-calculations that can be done without propagating i_step
# 5. Propagate by looping over i_step
# ----------------------------------------------------

# 1. Done elsewhere on sketchpad
# 2. Inputs
#     2.1 Orbital elements from DataPool (h_p, e, i, RAAN, argp, ma0)
#     2.2 Earth properties from Earth (GM_E, r_E, axial_rate)
#     2.3 Simulation parameters from DataPool (n_orbit_subs, n_steps, time0_datum)


# data = DataPool(config) # Todo: to incorporate once function

# All internal angles defined in radians
h_p = 300E3                     # [m] Altitude of pericentre
e = 0.2                         # [-] Eccentricity
i = 0                           # [deg] Inclination
raan = 0                        # [deg] Right ascention of the ascending node
argp = 0                        # [deg] Argument of periapsis
ma0 = 0                         # [deg] Initial mean anomaly

year = 2020.0                   # [year] Date of orbit (expressed in year decimal)

n_orbit_subs = 16
orbit_spacing = "isochronal"

t0 = 0                  # Initial time shift TODO: Determine if useful
th_E0 = pi / 180 * 0    # Initial angle of Earth w.r.t. zero datum

n_step = 16+1                   # Total steps in simulation


# 3. Pregenerate ndarrays for all saveable data (length: n_step):
#     t(i_step)
#     mean(i_step)
#     trueanom(i_step)
#     xyz_ECI(i_step)
#     flightpathangle(i_step)
#     earth_angle(i_step)
#     ____
#     xyz_ECEF(i_step)
#     rlonglat_geoc(i_step)
#     B_NED(i_step)
#     B_I(i_step)
#     B_B(i_step)

# t = zeros(n_step)               # [s] Time
ma = empty(n_step)              # [rad] Mean anomaly
ta = zeros(n_step)              # [rad] True anomaly
gamma = zeros(n_step)           # [rad] Flight path angle
th_E = zeros(n_step)            # [rad] Earth axial angle

xyz_ECI = zeros((n_step, 3))         # [m, m, m] XYZ coordinates of point in ECI frame
xyz_ECEF = zeros((n_step, 3))        # [m, m, m] XYZ coordinates of point in ECEF frame
rlonglat_geoc = zeros((n_step, 3))   # [m, rad, rad] r, longitude, latitude in geocentric frame
B_NED = zeros(n_step)           # [T, T, T] Bx, By, Bz components in NED frame (returned by IGRF)
B_I = zeros(n_step)             # [T, T, T] Bx, By, Bz components in I frame
B_B = zeros(n_step)             # [T, T, T] Bx, By, Bz components in B frame


# 4. Pre-calculations
#     4.1 Orbit points
#     4.2 Orbit parameters: r_p, a, r_a, b, T_orbit
#     4.3 Time step and earth angle step
#     4.4 Pre-propagate time array t(i_step)
#     4.5 For single orbit, calculate:
#             gamma_orbit
#             v_xyz_orbit
#             R


# 4.1
orbit = Orbit(Earth(), h_p, e, i, raan, argp, ma0)

xyz_orbit, ma_orbit, ta_orbit, gamma_orbit, H_unit_vector, v_xyz_orbit = orbit.draw(
    subdivisions=n_orbit_subs,
    spacing=orbit_spacing,
    order=12
)

# 4.2
r_p = orbit.get_r_p()
r_a = orbit.get_r_a()
a = orbit.get_a()
b = orbit.get_b()
T_orbit = orbit.get_period()

# 4.3
dt = T_orbit/n_orbit_subs  # Note: only valid if "orbit_spacing" is set to "isochronal"
dth_E = Earth().axial_rate * dt

# 4.4
t = arange(0., n_step*dt, dt)    # [rad] Earth angle from datum

# 4.5
# gamma_orbit = empty(n_orbit_subs)
# v_xyz_orbit = empty((n_orbit_subs, 3))
#
Rta_ECI_SI = empty((n_orbit_subs, 3, 3))


for i in range(n_orbit_subs):
    # TODO: Optimize later (currently 19 ms for 256 items)
    #  -> Update 27-01-2024: replaced np.cross() with cross3d -> BENCHMARK AGAIN

    # gamma_orbit[i] = arctan((e * sin(ta_orbit[i])) / (1 + e * cos(ta_orbit[i])))

    # Pre-calculate R_ECI_SI (precalculate to save on np.cross() calls later)
    Rta_ECI_SI[i, :, :] = vstack([
        uv3d(v_xyz_orbit[i]),
        H_unit_vector,
        cross3d(uv3d(v_xyz_orbit[i]), H_unit_vector)])


# 5. Loop over i_step and calculate properties
#
#     5.2 Populate orbit property data
#             xyz_ECI(i_step)
#             ma(i_step)
#             ta(i_step)
#             gamma(i_step)
#     5.2 Calculate velocity vectors
#             v_xyz_ECI(i_step)
#     5.3 Propagate Earth axial angle:
#             th_E(i_step)
#     5.4 Calculate ECEF coordinates:
#             xyz_ECEF(i_step)

for i_step in range(n_step):

    # 5.1

    gamma[i_step] = arctan((e*sin(ta[i_step]))/(1+e*cos(ta[i_step])))
    th_E[i_step] = (th_E0 + i_step*dth_E) % (2*pi)


    # 5.3
    xyz_ECI[i_step, :] = xyz_orbit[i_step % n_orbit_subs]
    ma[i_step] = ma_orbit[i_step % n_orbit_subs]
    ta[i_step] = ta_orbit[i_step % n_orbit_subs]

    # 5.4
    R_ECI_ECEF = RZ(th_E[i_step])
    xyz_ECEF[i_step] = dot(R_ECI_ECEF, xyz_ECI[i_step])


# ============================================================================
# [DEBUG]
# print(type(xyz_orbit), type(ma_orbit), type(ta_orbit))
# print(len(xyz_orbit), len(ma_orbit), len(ta_orbit))


# print(f"xyz_orbit: {xyz_orbit}")
# print(f"ma_orbit: {ma_orbit*180/pi}")
# print(f"ma: {ma*180/pi}")
# print(f"gamma: {(gamma*180/pi).round()}")
# print(f"gamma2: {(gamma2*180/pi).round()}")
# print(f"ta_orbit: {ta_orbit*180/pi}")
print(f"t: [{t[0]}, {round(t[-1])}] s")
print(f"t: [{t[0]}, {round(t[-1]/3600, 2)}] hour")
print(th_E*180/pi)
print(t)


print("==== Orbit properties: ====")
print(f"T_orbit {round(T_orbit)} s ({round(T_orbit/3600, 2)} hour)")
print("r_p", r_p, "m")
print("r_a", r_a, "m")
print("a", a, "m")
print("===========================")

print(f"GM earth: {orbit.body.gm}")

# print(xyz_orbit)
# print("")
# print(xyz_ECI)
# print(xyz_ECEF)

# import matplotlib.pyplot as plt
#
# # plt.plot(ma, ta-ma)
# # plt.plot(linspace(0, 2*pi, 100), 0.4*sin(linspace(0, 2*pi, 100)))
# plt.plot(ta*180/pi, gamma*180/pi)
# plt.show()


t1full = time()
print(f"Total time: {round((t1full-t0full)*1E6)} us")