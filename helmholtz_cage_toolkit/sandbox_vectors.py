import numpy as np
from time import time
import pyqtgraph as pg
import pyqtgraph.opengl as gl


from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.pg3d import (
    RX, RY, RZ, R,
    PGPoint3D, PGVector3D, PGFrame3D,
    plotgrid, plotpoint, plotpoints, plotvector, plotframe,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
)


# ==== Other functions
def wrap(angle, angle_range):
    angle_wrapped = (angle + angle_range / 2) % angle_range - angle_range / 2
    if angle_wrapped == -angle:
        angle_wrapped = -angle_wrapped
    return angle_wrapped

def conv_ECEF_NED(coor, r, long, lat):
    # long = -long
    # lat = -lat
    # long = wrap(long+pi/2, 2*pi)
    # lat = wrap(lat-pi/2, pi)
    print("EFFECTIVE VALUES:")
    print(f"[DEBUG] long: {round(180/pi*long,1)} deg")
    print(f"[DEBUG] lat:  {round(180/pi*lat,1)} deg")
    print("")

    # R_NED_ENU = array([[0, 1, 0], [1, 0, 0], [0, 0, -1]])
    R_NED_ENU = array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # TODO: REMOVE
    # return np.dot(R_X, np.dot(R_Z, np.dot(R_NED_ENU, coor)))
    # return np.dot(R_X, np.dot(R_Z, coor))
    coor = dot(RZ(pi/2), coor)    # First rotate 90 deg around Z
    coor = dot(RY(pi/2), coor)    # First rotate 90 deg around X

    # coor = np.dot(RX(0*pi/2), np.dot(RZ(pi/2), coor))
    # coor = np.dot(np.dot(RX(0*pi/2), RZ(pi/2)), coor)
    coor = dot(RZ(long), coor)
    return coor

def transform(xyz, a, d):
    # Optimizations:
    # Pre-calculating sine and cosine terms:
    # Result: 27.8 us -> 18.3 us  (-34%)
    # Using numpy rasterization during sin(), cos() calls:
    # Result: 18.3 us -> 13.3 us  (-27%)
    # Unifying function return in a single term (minimal scoped assignment):
    # Result: 13.3 us -> 13.0 us  (-2.2%)

    s, c = sin(a), cos(a)

    return dot(
        array([
            [c[1]*c[2], c[1]*s[2], -s[1]],
            [-c[0]*s[2]+s[0]*s[1]*c[2], c[0]*c[2]+s[0]*s[1]*s[2], s[0]*c[1]],
            [s[0]*s[2]+c[0]*s[1]*c[2], -s[0]*c[2]+c[0]*s[1]*s[2], c[0]*c[1]]]),
        xyz+d)

def transform2(xyz, R, d, cor=array([0, 0, 0])):
    # Optimizations:
    # Pre-calculating sine and cosine terms:
    # Result: 27.8 us -> 18.3 us  (-34%)
    # Using numpy rasterization during sin(), cos() calls:
    # Result: 18.3 us -> 13.3 us  (-27%)
    # Unifying function return in a single term (minimal scoped assignment):
    # Result: 13.3 us -> 13.0 us  (-2.2%)

    return dot(R, xyz+d)

def rotate(xyz, R, cor=array([0, 0, 0])):
    # Optimizations:
    # Pre-calculating sine and cosine terms:
    # Result: 27.8 us -> 18.3 us  (-34%)
    # Using numpy rasterization during sin(), cos() calls:
    # Result: 18.3 us -> 13.3 us  (-27%)
    # Unifying function return in a single term (minimal scoped assignment):
    # Result: 13.3 us -> 13.0 us  (-2.2%)

    return dot(R, xyz-cor)+cor


# ==== PyQtGraph 3D plot
app = pg.mkQApp("3D Sandbox - Visualizer")

ps = 2    # Plot scale

w = gl.GLViewWidget()
w.show()
w.setWindowTitle("Visualizer Window")
w.setCameraPosition(distance=3*ps)

# Draw default grid
grid_major_plotitem = plotgrid(w, plotscale=ps, alpha=0.12, gridspacing_div=2)
grid_minor_plotitem = plotgrid(w, plotscale=ps, alpha=0.06)

# Draw base XYZ tripod
tripod_base_plotitem = plotframe(PGFrame3D(), w,
                                 plotscale=ps, alpha=0.5, width=2)


# ==== START OF SANDBOX =====================================================


X1 = array([1, 1, 0])
X1 = X1/np.linalg.norm(X1)
Y1 = array([-1, 1, 0])
Y1 = Y1/np.linalg.norm(Y1)

tt = 0
n = 1
for i in range(n):
    t0 = time()
    Z1 = np.cross(X1, Y1)
    t1 = time()
    tt += (t1-t0)

print(f"t_avg = {round((tt/n)*1E6,1)} us.")

X1_plotitem = gl.GLLinePlotItem(pos=[array([0, 0, 0]), X1], color=(1, 0, 0, 1))
w.addItem(X1_plotitem)
Y1_plotitem = gl.GLLinePlotItem(pos=[array([0, 0, 0]), Y1], color=(0, 1, 0, 1))
w.addItem(Y1_plotitem)
Z1_plotitem = gl.GLLinePlotItem(pos=[array([0, 0, 0]), Z1], color=(0, 0, 1, 1))
w.addItem(Z1_plotitem)

# GREEN point - Original point
p1 = array([1, 1, 1])
p1_plotitem = plotpoint(PGPoint3D(p1), w, hexcolour="00ff00")

R = vstack([X1, Y1, Z1])

# CYAN point - Transform axis system, where point "rotates" BACKWARDS
p1_t1 = R@p1
p1_t1_plotitem = plotpoint(PGPoint3D(p1_t1), w, hexcolour="00ffff")

# MAGENTA point - Transform axis system and point "together"
p1_t2 = R.transpose()@p1
p1_t2_plotitem = plotpoint(PGPoint3D(p1_t2), w, hexcolour="ff00ff")

print("R =", R)

# t0 = time()
# p1 = PGPoint3D(array([4, 0, 0]))
# t1 = time()
# p1_plotitem = plotpoint(p1, w)
#
# t2 = time()
# p1.translate(array([0, 4, 0]))
# t3 = time()
# updatepoint(p1_plotitem, p1, colour="ff0000", alpha=1)
# t4 = time()

# a = array([0, 0, 0])
# a = array([0, -pi/2, -pi/4])
# d = array([1, 2, 1])*2
# cor = array([0, 1, 0])
#
#
# f1 = PGFrame3D()
# f1.transform(a, d)
# f1_plotitem = plotframe(f1, w, width=3)
#
# p3 = array([[0., 0., 0.],
#             [1., 0., 0.],
#             [0., 1., 0.],
#             [0., 0., 1.],
#             [3., -2., -1.]])
#
# p3_backup = p3
#
# # Verify transform_to() / transform_from stack:
# print("")
# plotpoints(p3, w, hexcolour="ff0000", size=3)
# print(f"p3 before rotation: \n{p3}")
# p3 = f1.transform_to(p3)
#
# print(f"p3_backup {p3_backup}")
#
# plotpoints(p3, w, hexcolour="00ff00")
# print(f"p3 after rotation : \n{p3.round(6)}")
# p3 = f1.transform_from(p3)
# print(f"p3 reverted:        \n{p3.round(6)}")
# plotpoints(p3, w, hexcolour="00ffff")
#
# if p3.all() == p3.all():
#     print("Check passed: Pre-transformation EQUALS post-reversion!")



# t0 = time()
# ps = np.random.random((1000, 3))*2
# print(ps)
#
# t1 = time()
# r = R(a)
#
# t2 = time()
# for i in range(len(ps)):
#     ps[i] = rotate(ps[i], r.transpose(), cor=f1.get_o())
#
# t3 = time()
# print(ps)
# ps_plotitem = plotpoints(ps, w, size=1)
#
# t4 = time()
# updatepoints(ps_plotitem, ps, colour="ffff00", alpha=1)
#
# t5 = time()
#
# print(f"1: {round(1E6*(t1-t0), 2)}")
# print(f"2: {round(1E6*(t2-t1), 2)}")
# print(f"3: {round(1E6*(t3-t2), 2)}")
# print(f"4: {round(1E6*(t4-t3), 2)}")
# print(f"5: {round(1E6*(t5-t4), 2)}")



# d = array([4, 5, 0])
# a = array([0, pi/2, pi/2])
#
#
# f1 = PGFrame3D(array([0, 0, 0]))
# f1.transform(a, d)
#
#
# f1_plotitem = plotframe(f1, w, alpha=1.0, plotscale=int(ps/3))
#
# v1 = PGVector3D(array([1, 1, 1]))
# v1_plotitem = plotvector(v1, w)
#
# v2 = PGVector3D(array([1, 1, 1]))
# v2.transform(a, d)
#
# v2_plotitem = plotvector(v2, w)
#
#
# v1 = PGVector3D(array([1, 1, 1]))
#
# print("Coordinates of point in other frame:")
# tf = transform(p1, a, d)
# print(tf.round(12))



# === END OF SANDBOX ========================================================
if __name__ == '__main__':
    pg.exec()
