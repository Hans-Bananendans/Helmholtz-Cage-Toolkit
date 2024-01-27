import numpy as np
from numpy import pi, array, sin, cos, arccos, ndarray
from time import time
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from copy import deepcopy

# ==== PyQtGraph 3D plot
app = pg.mkQApp("Orbit Visualizer")
w = gl.GLViewWidget()
w.show()
w.setWindowTitle("Orbit Visualizer (window title)")

ps = 10    # Plot scale

def hex2rgb(hexval: str) -> list:
    """Converts a hex colour string (e.g. '#3faa00') to [0, 1] rgb values"""
    hexval = hexval.lstrip("#")

    if len(hexval) == 8:
        rgb255 = list(int(hexval[i:i + 2], 16) for i in (0, 2, 4, 6))
    else:
        rgb255 = list(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
    return [c/255 for c in rgb255]

def hex2rgba(hex: str, alpha: float) -> list:
    """Edit/attach a [0, 1.0] alpha value to athe rgb value by
     specifying a 'attachalpha'.
     """
    rgb = hex2rgb(hex)

    if len(rgb) == 3:
        rgb.append(alpha)
    elif len(rgb) == 4:
        rgb[-1] = alpha
    else:
        raise AssertionError(f"RGB value {rgb} is the wrong length ({len(rgb)})!")
    return rgb


w.setCameraPosition(distance=3*ps)

# Add horizontal grid
grid = gl.GLGridItem()
grid.setColor((255, 255, 255, 24))
grid.setSpacing(x=ps/5, y=ps/5)  # Comment out this line at your peril...
grid.setSize(x=2*ps, y=2*ps)
grid.setDepthValue(20)
w.addItem(grid)

# Add tripod
ps_GI_tripod = 1*ps
GI_tripod_x = gl.GLLinePlotItem(
    pos=[array([0, 0, 0]), array([ps_GI_tripod, 0, 0])],
    color=hex2rgb("ff000088"), width=2, antialias=True)
GI_tripod_y = gl.GLLinePlotItem(
    pos=[array([0, 0, 0]), array([0, ps_GI_tripod, 0])],
    color=hex2rgb("00ff0088"), width=2, antialias=True)
GI_tripod_z = gl.GLLinePlotItem(
    pos=[array([0, 0, 0]), array([0, 0, ps_GI_tripod])],
    color=hex2rgb("0000ff88"), width=2, antialias=True)
for tripod_component in (GI_tripod_x, GI_tripod_y, GI_tripod_z):
    tripod_component.setDepthValue(10)
    w.addItem(tripod_component)

#
# # Add vlines
# for i in range(len(coords3[0])):
#     pts = np.column_stack([
#         [coords3[0][i], coords3[0][i]],
#         [coords3[1][i], coords3[1][i]],
#         [coords3[2][i], 0],
#     ])
#     vline = gl.GLLinePlotItem(pos=pts,
#                               color=(1, 1, 1, 0.1),
#                               antialias=True,
#                               width=1)
#     vline.setDepthValue(1)
#     w.addItem(vline)
#
# # Add drawn scatter points
# orbit_scatter = gl.GLScatterPlotItem(
#     pos=np.column_stack([coords3[0], coords3[1], coords3[2]]),
#     color=tuple(list(hex2rgb(plotcolors2[1]+"FF"))),
#     # color=(1.0, 1.0, 0.0, 1.0),
#     size=4,
#     pxMode=True)
# orbit_scatter.setDepthValue(1)
# w.addItem(orbit_scatter)
#
#
# # test = [[1, 1], [2, 2], [3, 3]]
# # print(type(np.column_stack(test)))
# # print(np.column_stack(test))
#
# # Draw satellite
# i_satpos = 0
# sat = gl.GLScatterPlotItem(
#     pos=np.column_stack([
#         coords3[0][i_satpos],
#         coords3[1][i_satpos],
#         coords3[2][i_satpos]]),
#     color=tuple(list(hex2rgb(plotcolors2[1]+"FF"))),
#     # color=(1.0, 1.0, 0.0, 1.0),
#     size=8,
#     pxMode=True)
#
# w.addItem(sat)
#
# vline_sat = gl.GLLinePlotItem(
#     pos=array(np.column_stack([
#         [coords3[0][i], coords3[0][i]],
#         [coords3[1][i], coords3[1][i]],
#         [coords3[2][i], 0]])),
#     color=(1.0, 1.0, 1.0, 0.8),
#     antialias=True,
#     width=1)
#
# vline_sat.setDepthValue(1)
# w.addItem(vline_sat)
#
# vdot_sat = gl.GLScatterPlotItem(
#     pos=np.column_stack([
#         coords3[0][i_satpos],
#         coords3[1][i_satpos],
#         0]),
#     color=(1.0, 1.0, 1.0, 0.8),
#     size=3,
#     pxMode=True)
# vdot_sat.setDepthValue(1)
# w.addItem(vdot_sat)


# def satellite_update():
#     global sat, vline_sat, vdot_sat, i_satpos, coords3
#     global earth_meshitem, EF_tripod_x, EF_tripod_y, EF_tripod_z
#
#     x, y, z = coords3[0][i_satpos], coords3[1][i_satpos], coords3[2][i_satpos]
#
#     sat.setData(pos=[x, y, z])
#     vline_sat.setData(pos=np.column_stack([[x, x], [y, y], [0, z]]))
#     vdot_sat.setData(pos=[x, y, 0])
#     for item in (earth_meshitem, EF_tripod_x, EF_tripod_y, EF_tripod_z):
#         item.rotate(360/(24/1.5*subdivisions), 0, 0, 1, local=False)
#     # for tripod_component in (EF_tripod_x, EF_tripod_y, EF_tripod_z):
#
#     i_satpos = (i_satpos + 1) % len(coords3[0])


# # Timer
# t = QtCore.QTimer()
# t.timeout.connect(satellite_update)
# t.start(40)


# =====================================================================

def RX(a) -> ndarray:
    """Returns a general purpose R_X rotation matrix.

    Input 'a' is the rotation angle in rad.
    """
    s, c = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls (7.4 ns -> 5.8 ns)
    return array([[1, 0, 0], [0, c, -s], [0, s, c]])

def RY(a) -> ndarray:
    """Returns a general purpose R_Y rotation matrix.

    Input 'a' is the rotation angle in rad.
    """
    s, c = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls
    return array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def RZ(a) -> ndarray:
    """Returns a general purpose R_Z rotation matrix.

    Input 'a' is the rotation angle in rad.
    """
    s, c = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls
    return array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def R(a: ndarray) -> ndarray:
    """Returns a general purpose 3-2-1 rotation matrix.

    Input 'a' is a Numpy ndarray with the rotation angles around x, y, z
     respectively in rad.
    """
    s, c = sin(a), cos(a)
    return array([
        [c[1]*c[2], c[1]*s[2], -s[1]],
        [-c[0]*s[2]+s[0]*s[1]*c[2], c[0]*c[2]+s[0]*s[1]*s[2], s[0]*c[1]],
        [s[0]*s[2]+c[0]*s[1]*c[2], -s[0]*c[2]+c[0]*s[1]*s[2], c[0]*c[1]]])

# class PGVector3D:
#     def __init__(self, base, mag):
#         self.base = array(base)
#         self.mag = array(mag)
# 
#     def get_base(self):
#         return self.base
# 
#     def get_mag(self):
#         return self.mag
# 
#     def unit(self):
#         return array(self.mag) / (self.mag[0] ** 2 + self.mag[1] ** 2 + self.mag[2] ** 2) ** (1/2)
# 
#     def translate(self, d):
#         self.base += d
# 
#     def rotate(self, ang, cor=None):
#         if cor is None:
#             self.mag = np.dot(RX(ang[0]), np.dot(RY(ang[1]), np.dot(RZ(ang[2]), self.mag)))
# 
#         else:
#             self.translate(-cor)
#             self.mag = np.dot(RX(ang[0]), np.dot(RY(ang[1]), np.dot(RZ(ang[2]), self.mag)))
#             self.translate(cor)

class PGPoint3D:
    def __init__(self, xyz: ndarray):
        self.xyz = array(xyz)

    def get_xyz(self) -> ndarray:
        return self.xyz

    def set_xyz(self, xyz_new):
        self.xyz = xyz_new

    def translate(self, d):
        self.xyz += d


# class PGVector3D:
#     def __init__(self, o, lxyz):
#         self.o = PGPoint3D(origin)
#         self.lxyz = np.array(lxyz)
#
#     def get_o(self):
#         return self.o
#
#     def set_o(self, o_new: PGPoint3D):
#         self.o = o_new
#
#     def get_lxyz(self):
#         return self.lxyz
#
#     def set_lxyz(self, lxyz_new):
#         self.lxyz = lxyz_new
#
#     def scale(self, f):
#         self.lxyz *= f
#
#     def get_l(self):
#         return (lxyz[0]**2 + lxyz[1]**2 + lxyz[2]**2)**(1/2)
#
#     def get_unit(self):
#         return self.lxyz / self.get_l
#
#     def translate(self, d):
#         self.base += d
#
#     def transform(self, a, d):
#         R = R(a)
#         self.o =

# class PGVector3D:
#     def __init__(self, o, p):
#         # Simple vector function that has origin 'o' and points to point 'p'
#         self.o = np.array(o)
#         self.p = np.array(p)
#
#     def get_o(self):
#         return self.o
#
#     def get_p(self):
#         return self.p
#
#     def set_o(self, o_new: PGPoint3D):
#         self.o = o_new
#
#     def get_lxyz(self):
#         return self.p-self.o
#
#     # def scale(self, f):
#     #     self.lxyz *= f
#
#     def get_l(self):
#         lxyz = self.get_lxyz()
#         return (lxyz[0]**2 + lxyz[1]**2 + lxyz[2]**2)**(1/2)
#
#     def get_unit(self):
#         return self.get_lxyz() / self.get_l()
#
#     def set_unit(self):
#         self.p = self.get_lxyz() / self.get_l() - self.o
#
#     def translate(self, d):
#         self.o += d
#         self.p += d
#
#     def transform(self, a, d):
#         r = R(a).transpose()
#         self.o = np.dot(r, self.o + d)
#         self.p = np.dot(r, self.p + d)

class PGVector3D:
    def __init__(self, lxyz: ndarray, o: ndarray = array([0, 0, 0])):
        # Simple vector function that has origin 'o' and points to point 'lxyz'
        self.o = o
        self.lxyz = lxyz

    def get_o(self):
        return self.o

    def set_o(self, o_new: ndarray):
        self.o = o_new

    def get_lxyz(self):
        return self.lxyz

    def scale(self, f):
        self.lxyz *= f

    def get_l(self):
        return (self.lxyz[0]**2 + self.lxyz[1]**2 + self.lxyz[2]**2)**(1/2)

    def get_unit(self):
        return self.get_lxyz() / self.get_l()

    def set_unit(self):
        self.lxyz = self.get_lxyz() / self.get_l()

    def translate(self, d):
        self.o += d

    def transform(self, a, d):
        r = R(a).transpose()
        self.translate(d)
        self.lxyz = np.dot(r, self.lxyz)

# class PGFrame3D:
#     def __init__(self, xyz):
#         self.xyz = array(xyz)
#         self.xyzdir = array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
#         self.dcm = None
#         self.recalculate_dcm()
#
#     def recalculate_dcm(self):
#         """Computes the direction cosine matrix (DCM) for conversion between
#            the frame's local coordinates and the global frame.
#
#            Returns: dcm (3-by-3 numpy.ndarray)
#            """
#         gx = array([1, 0, 0])
#         gy = array([0, 1, 0])
#         gz = array([0, 0, 1])
#         self.dcm = array([
#             [np.dot(gx, self.xyzdir[0]),
#              np.dot(gx, self.xyzdir[1]),
#              np.dot(gx, self.xyzdir[2])],
#
#             [np.dot(gy, self.xyzdir[0]),
#              np.dot(gy, self.xyzdir[1]),
#              np.dot(gy, self.xyzdir[2])],
#
#             [np.dot(gz, self.xyzdir[0]),
#              np.dot(gz, self.xyzdir[1]),
#              np.dot(gz, self.xyzdir[2])]])
#
#     def get_xyz(self):
#         return self.xyz
#
#     def get_xyzdir(self):
#         return self.xyzdir
#
#     def translate(self, d):
#         self.xyz += d
#
#     def rotate(self, a, cor=None, seq="321"):
#         for axis in reversed(seq):
#
#             # If no Centre of Rotation (cor) is given, take frame origin.
#             # If not, subtract coordinates of cor first before applying
#             # the rotation, and then reverse this afterwards.
#             temp = deepcopy(self.xyz)
#
#             rx, ry, rz = RX(a[0]), RY(a[1]), RZ(a[2])
#
#             if cor is not None:
#                 print(f"Translate to cor ({self.xyz})")
#                 self.translate(-cor)
#                 print(f"   after:        ({self.xyz})")
#
#             if axis == '1':
#                 self.xyzdir[0] = np.dot(rx, self.xyzdir[0])
#                 self.xyzdir[1] = np.dot(rx, self.xyzdir[1])
#                 self.xyzdir[2] = np.dot(rx, self.xyzdir[2])
#             if axis == '2':
#                 self.xyzdir[0] = np.dot(ry, self.xyzdir[0])
#                 self.xyzdir[1] = np.dot(ry, self.xyzdir[1])
#                 self.xyzdir[2] = np.dot(ry, self.xyzdir[2])
#
#             if axis == '3':
#                 self.xyzdir[0] = np.dot(rz, self.xyzdir[0])
#                 self.xyzdir[1] = np.dot(rz, self.xyzdir[1])
#                 self.xyzdir[2] = np.dot(rz, self.xyzdir[2])
#
#             # Reverse temporary translation.
#             if cor is not None:
#                 print(f"Translate back from cor ({self.xyz})")
#                 self.translate(cor)
#                 print(f"   after:               ({self.xyz})")
#
#         self.recalculate_dcm()
#
#     # if cor is None:
#     #     self.mag = np.dot(RX(ang[0]), np.dot(RY(ang[1]), np.dot(RZ(ang[2]), self.mag)))
#     #
#     # else:
#     #     self.translate(-cor)
#     #     self.mag = np.dot(RX(ang[0]), np.dot(RY(ang[1]), np.dot(RZ(ang[2]), self.mag)))
#     #     self.translate(cor)
#
#     def transform(self):
#         pass

# class PGFrame3D:
#     def __init__(self, o: ndarray = None):
#         if o is None:
#             self.o = array([0, 0, 0])
#         else:
#             self.o = o
#         self.uxyz = [
#             array([1, 0, 0]),
#             array([0, 1, 0]),
#             array([0, 0, 1])]
#         self.r = np.eye(3)
#
#     def get_o(self):
#         return self.o
#
#     def get_uxyz(self) -> list:
#         return self.uxyz
#
#     def get_r(self) -> ndarray:
#         return self.r
#
#     # def translate(self, d):
#     #     for property in (self.o, self.uxyz[0], self.uxyz[1], self.uxyz[2]):
#     #         property += d
#
#     def translate(self, d):
#         self.o += d
#
#     def transform(self, a, d):
#         self.r = np.dot(R(a).transpose(), self.r)
#
#         print(f"transform(): r: \n{self.r[0].round(12)}\n{self.r[1].round(12)}\n{self.r[2].round(12)}")
#
#         for i in range(3):
#             self.uxyz[i] = np.dot(self.r, self.uxyz[i])
#
#         print(f"transform(): uxyz: \n{self.uxyz[0].round(12)}\n{self.uxyz[1].round(12)}\n{self.uxyz[2].round(12)}")
#         # print(f"transform(): {self.uxyz}")
#         self.translate(d)
#         # self.o += d
#         # for i in range(3):
#         #     self.uxyz[i] = np.dot(self.r, self.uxyz[i] - d)

class PGFrame3D:
    def __init__(self, o: ndarray = None):
        if o is None:
            self.o = array([0, 0, 0])
        else:
            self.o = o
        self.r = np.eye(3)

    def get_o(self):
        return self.o

    def get_r(self) -> ndarray:
        return self.r

    def translate(self, d):
        self.o += d

    def transform(self, a, d):
        self.r = np.dot(R(a), self.r)
        self.translate(d)



def wrap(angle, angle_range):
    angle_wrapped = (angle + angle_range / 2) % angle_range - angle_range / 2
    if angle_wrapped == -angle:
        angle_wrapped = -angle_wrapped
    # print(f"[DEBUG] wrap({180/pi*angle}, {180/pi*angle_range}) = {180/pi*angle_wrapped} deg")
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
    coor = np.dot(RZ(pi/2), coor)    # First rotate 90 deg around Z
    coor = np.dot(RY(pi/2), coor)    # First rotate 90 deg around X

    # coor = np.dot(RX(0*pi/2), np.dot(RZ(pi/2), coor))
    # coor = np.dot(np.dot(RX(0*pi/2), RZ(pi/2)), coor)
    coor = np.dot(RZ(long), coor)
    return coor

def plotpoint(point: PGPoint3D, pgwindow, depth=10, hexcolour="ffff00",
              alpha=1.0, size=6):
    point_plotitem = gl.GLScatterPlotItem(
        pos=[point.get_xyz()],
        color=hex2rgba(hexcolour, alpha),
        size=size, pxMode=True)

    point_plotitem.setDepthValue(depth)

    pgwindow.addItem(point_plotitem)
    return point_plotitem

# def plotvector(vector: PGVector3D, pgwindow, depth=10,
#                hexcolour="FFFF00FF", width=4, antialias=True):
#     vector_plotitem = gl.GLLinePlotItem(
#         pos=[vector.get_base(), vector.get_base()+vector.get_mag()],
#         color=hex2rgb(hexcolour), width=width, antialias=antialias)
#
#     vector_plotitem.setDepthValue(depth)
#
#     pgwindow.addItem(vector_plotitem)
#     return vector_plotitem

def plotvector(vector: PGVector3D, pgwindow, hexcolour="ffff00",
               alpha=1.0, depth=10, width=4, antialias=True):
    vector_plotitem = gl.GLLinePlotItem(
        pos=[vector.get_o(), vector.get_o()+vector.get_lxyz()],
        color=hex2rgba(hexcolour, alpha),
        width=width, antialias=antialias)

    vector_plotitem.setDepthValue(depth)

    pgwindow.addItem(vector_plotitem)
    return vector_plotitem

# def plotframe(frame: PGFrame3D, pgwindow, plotscale=3E6, depth=10,
#               width=3, antialias=True):
#     xaxis_plotitem = gl.GLLinePlotItem(
#         pos=[frame.xyz, frame.xyz+frame.xyzdir[0]*plotscale],
#         color=hex2rgb("FF0000FF"), width=width, antialias=antialias)
#     yaxis_plotitem = gl.GLLinePlotItem(
#         pos=[frame.xyz, frame.xyz+frame.xyzdir[1]*plotscale],
#         color=hex2rgb("00FF00FF"), width=width, antialias=antialias)
#     zaxis_plotitem = gl.GLLinePlotItem(
#         pos=[frame.xyz, frame.xyz+frame.xyzdir[2]*plotscale],
#         color=hex2rgb("0000FFFF"), width=width, antialias=antialias)
#
#     frame_plotitems = (xaxis_plotitem, yaxis_plotitem, zaxis_plotitem)
#
#     for plotitem in frame_plotitems:
#         plotitem.setDepthValue(depth)
#         pgwindow.addItem(plotitem)
#     return frame_plotitems

# TODO: REWRITE THIS

def plotframe(frame: PGFrame3D, pgwindow, plotscale=1,
              alpha=1.0, depth=10, width=3, antialias=True):

    frame_plotitems = []

    for i, axis_colour in enumerate(("ff0000", "00ff00", "0000ff")):
        axis_plotitem = gl.GLLinePlotItem(
            pos=[frame.get_o(), frame.get_o()+frame.get_r()[i]*plotscale],
            color=hex2rgba(axis_colour, alpha),
            width=width, antialias=antialias
        )
        axis_plotitem.setDepthValue(depth)
        pgwindow.addItem(axis_plotitem)
        frame_plotitems.append(axis_plotitem)

    return frame_plotitems


p1 = PGPoint3D(array([4, 0, 0]))
print("p1:", p1.get_xyz())
p1.translate(array([0, 4, 0]))
print("p1:", p1.get_xyz())

plotpoint(p1, w)


d = array([4, 5, 0])
a = array([0, pi/2, pi/2])


f1 = PGFrame3D(array([0, 0, 0]))
# print(f"f1.o:    {f1.o.round(3)}")
# print(f"f1.uxyz: {f1.uxyz}")
f1.transform(a, d)
# f1.transform(a, np.array([0, 0, 0]))
# print(f"f1.o:    {f1.o.round(3)}")
# print(f"f1.uxyz: {f1.uxyz}")

plotframe(f1, w, alpha=1.0, plotscale=int(ps/3))

v1 = PGVector3D(array([1, 1, 1]))
plotvector(v1, w)

v2 = PGVector3D(array([1, 1, 1]))
v2.transform(a, d)

plotvector(v2, w)

# def transform1(point: PGPoint3D, a, d):
#
#     xyz = point.get_xyz()
#     rotmatrix = np.dot(RX(-a[0]), np.dot(RY(-a[1]), RZ(-a[2])))
#
#     return np.dot(rotmatrix, xyz-d)
#
#
# def transform2(point: PGPoint3D, a, d):
#
#     xyz = point.get_xyz()
#
#     # Minimizing the number of np.sin(), np.cos() calls to speed up computation
#     # Result: 27.7 us -> 18.2 us  (-34% time)
#
#     c1, c2, c3 = np.cos(a[0]), np.cos(a[1]), np.cos(a[2])
#     s1, s2, s3 = np.sin(a[0]), np.sin(a[1]), np.sin(a[2])
#
#     rotmatrix = array([
#         [s2*c3, c2*s3, -s2],
#         [-c1*s3+s1*s2*c3, c1*c3+s1*s2*s3, s1*c2],
#         [s1*s3+c1*s2*c3, -s1*c3+c1*s2*s3, c1*c2]])
#
#     result = np.dot(rotmatrix, xyz-d)
#
#     return result
#
# def transform3(point: PGPoint3D, a, d):
#
#     xyz = point.get_xyz()
#
#     # Optimizations:
#     # Pre-calculating sine and cosine terms:
#     # Result: 27.7 us -> 18.3 us  (-34% time)
#     # Also calling them in rasterized form:
#     # Result: 18.3 us -> 13.4 us  (-27%)
#
#     c = np.cos(a)
#     s = np.sin(a)
#
#     rotmatrix = array([
#         [s[1]*c[2], c[1]*s[2], -s[1]],
#         [-c[0]*s[2]+s[0]*s[1]*c[2], c[0]*c[2]+s[0]*s[1]*s[2], s[0]*c[1]],
#         [s[0]*s[2]+c[0]*s[1]*c[2], -s[0]*c[2]+c[0]*s[1]*s[2], c[0]*c[1]]])
#
#     result = np.dot(rotmatrix, xyz-d)
#
#     return result
#
#
# def transform4(point: PGPoint3D, a, d):
#
#     xyz = point.get_xyz()
#
#     # Optimizations:
#     # Pre-calculating sine and cosine terms:
#     # Result: 27.8 us -> 18.3 us  (-34% time)
#     # Using numpy rasterization during sin(), cos() calls:
#     # Result: 18.3 us -> 13.3 us  (-27%)
#     # Unifying function return in a single term (minimal scoped assignment):
#     # Result: 13.3 us -> 13.0 us  (-2.2%)
#
#     c = np.cos(a)
#     s = np.sin(a)
#
#     return np.dot(
#         array([
#             [s[1]*c[2], c[1]*s[2], -s[1]],
#             [-c[0]*s[2]+s[0]*s[1]*c[2], c[0]*c[2]+s[0]*s[1]*s[2], s[0]*c[1]],
#             [s[0]*s[2]+c[0]*s[1]*c[2], -s[0]*c[2]+c[0]*s[1]*s[2], c[0]*c[1]]]
#         ), xyz-d)

# print("Coordinates of point in other frame:")
#
# nreps = 1000000
# t1rec, t2rec, t3rec, t4rec = np.zeros(nreps), np.zeros(nreps), np.zeros(nreps), np.zeros(nreps)
#
# for i in range(nreps):
#     t0 = time()
#     tf1 = transform1(p1, a, d)
#     t1 = time()
#     tf2 = transform2(p1, a, d)
#     t2 = time()
#     tf3 = transform3(p1, a, d)
#     t3 = time()
#     tf4 = transform4(p1, a, d)
#     t4 = time()
#     t1rec[i] = t1-t0
#     t2rec[i] = t2-t1
#     t3rec[i] = t3-t2
#     t4rec[i] = t4-t3
#
# print(f"Average time: {round(sum(t1rec)/len(t1rec)*1E6, 1)} us")
# print(f"Average time: {round(sum(t2rec)/len(t2rec)*1E6, 1)} us")
# print(f"Average time: {round(sum(t3rec)/len(t3rec)*1E6, 1)} us")
# print(f"Average time: {round(sum(t4rec)/len(t4rec)*1E6, 1)} us")

def transform(point: PGPoint3D, a, d):
    # Optimizations:
    # Pre-calculating sine and cosine terms:
    # Result: 27.8 us -> 18.3 us  (-34%)
    # Using numpy rasterization during sin(), cos() calls:
    # Result: 18.3 us -> 13.3 us  (-27%)
    # Unifying function return in a single term (minimal scoped assignment):
    # Result: 13.3 us -> 13.0 us  (-2.2%)

    xyz = point.get_xyz()

    c = np.cos(a)
    s = np.sin(a)

    return np.dot(
        array([
            [c[1]*c[2], c[1]*s[2], -s[1]],
            [-c[0]*s[2]+s[0]*s[1]*c[2], c[0]*c[2]+s[0]*s[1]*s[2], s[0]*c[1]],
            [s[0]*s[2]+c[0]*s[1]*c[2], -s[0]*c[2]+c[0]*s[1]*s[2], c[0]*c[1]]]),
        xyz-d)


print("Coordinates of point in other frame:")
tf = transform(p1, a, d)
print(tf.round(12))

#
# f1.rotate([0, 0, pi/2], cor=array([0, 5E6, 0]))
# # f1.rotate([0, 0, pi/2])
#
# print(f1.xyz)
# print(f1.xyzdir)
# print(f1.dcm)
#
# f1_plotitems = plotframe(f1, w)


# v1 = PGVector3D([10E6, 0, 0], [5E6, 0, 0])
# v1_plotitem = plotvector(v1, w)
# # v1.rotate(array([0, 0, pi/2]), cor=-v1.get_base())
# v1.rotate(array([0, 0, pi/2]), cor=array([-10E6, 0, 0]))
#
# v1_plotitem2 = plotvector(v1, w)


if __name__ == '__main__':
    pg.exec()
    # Manual garbage collection:
    for var in []:
        del globals()[var]