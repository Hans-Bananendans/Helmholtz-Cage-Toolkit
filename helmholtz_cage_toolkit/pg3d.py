import pyqtgraph.opengl as gl

from helmholtz_cage_toolkit import *


# ==== HEX to RGB functions
def hex2rgb(hexval: str) -> list:
    """Converts a hex colour string (e.g. '#3faa00') to [0, 1] rgb values"""
    hexval = hexval.lstrip("#")

    if len(hexval) == 8:
        rgb255 = list(int(hexval[i:i + 2], 16) for i in (0, 2, 4, 6))
    else:
        rgb255 = list(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
    return [c/255 for c in rgb255]

def hex2rgba(hex: str, alpha: float, mult=1) -> list:
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
    return [mult*i for i in rgb]


# ==== General purpose rotation matrices
def RX(a) -> ndarray:
    """Returns a general purpose R_X rotation matrix.

    Input 'a' is the rotation angle in rad.
    """
    s, c = sin(a), cos(a)  # Avoiding unnecessary np.sin, np.cos calls (7.4 us -> 5.8 us)
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


# ==== Elemental geometry classes
class PGPoint3D:
    def __init__(self, xyz: ndarray):
        self.xyz = array(xyz)

    def get_xyz(self) -> ndarray:
        return self.xyz

    def set_xyz(self, xyz_new):
        self.xyz = xyz_new

    def translate(self, d):
        self.xyz += d


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
        self.lxyz = dot(r, self.lxyz)


class PGFrame3D:
    def __init__(self, o: ndarray = None, r: ndarray = eye(3)):
        if o is None:
            self.o = array([0, 0, 0])
        else:
            self.o = o
        self.r = r

    def get_o(self):
        return self.o

    def get_r(self) -> ndarray:
        return self.r

    def set_o(self, o: ndarray):
        if len(o) == 3:
            self.o = o
        else:
            raise AssertionError(f"'o' must be an ndarray of length 3! (given: length {len(o)})")

    def set_r(self, R: ndarray):
        if R.shape == (3, 3):
            self.r = R
        else:
            raise AssertionError(f"'R' must be a 3x3 matrix! (given: {R.shape[0]}x{R.shape[1]})")

    def translate(self, d):
        self.o += d

    def transform(self, a, d):
        self.r = dot(R(a), self.r)
        self.translate(d)

    def transform_to(self, points):
        # TODO: Find way to optimize this (without intermediate assignment)
        # -> Fair warning: In-place op (i.e. points[i] = dot(R, points[i])
        # will open an ungodly can of worms, however.
        output = zeros((len(points), 3))
        for i in range(len(points)):
            output[i] = dot(self.r.transpose(), points[i]) + self.o
        return output

    def transform_from(self, points):
        # TODO: Find way to optimize this (without intermediate assignment)
        output = zeros((len(points), 3))
        for i in range(len(points)):
            output[i] = dot(self.r, points[i] - self.o)
            # points[i][:] = dot(self.r, points[i][:]) - self.o
        return output

# ==== OpenGL PyQtGraph plotting functions
def plotgrid(pgwindow, plotscale=1, gridspacing_div=10,
             hexcolour="ffffff", alpha=0.1, depth=20, antialias=True):
    grid_plotitem = gl.GLGridItem(
        # GLGridItem takes a 4-length list of [0, 255] values for colour
        color=hex2rgba(hexcolour, alpha, mult=255),
        antialias=antialias
        )

    # Set size to 2*`plotscale` so it extends for `plotscale` on both sides of
    # the origin
    grid_plotitem.setSize(x=2*plotscale,
                          y=2*plotscale)

    # Set gridspacing to a division of plotscale (10 by default)
    grid_plotitem.setSpacing(x=plotscale/gridspacing_div,
                             y=plotscale/gridspacing_div)

    grid_plotitem.setDepthValue(depth)

    pgwindow.addItem(grid_plotitem)
    return grid_plotitem

def plotpoint(point: PGPoint3D, pgwindow, depth=10, hexcolour="ffff00",
              alpha=1.0, size=6):
    point_plotitem = gl.GLScatterPlotItem(
        pos=[point.get_xyz()],
        color=hex2rgba(hexcolour, alpha),
        size=size, pxMode=True)

    point_plotitem.setDepthValue(depth)

    pgwindow.addItem(point_plotitem)
    return point_plotitem

def updatepoint(point_plotitem: gl.GLScatterPlotItem, points: [PGPoint3D],
                colour=None, alpha=None):
    if colour is None and alpha is None:
        for point in points:
            point_plotitem.setData(
                pos=[point.get_xyz()]
            )
    else:
        for point in points:
            point_plotitem.setData(
                pos=[point.get_xyz()],
                color=hex2rgba(colour, alpha)
            )


# TODO: Unify to PGPoint3D items? Or leave as ndarray?
def plotpoints(points: ndarray, pgwindow, depth=10, hexcolour="ffff00",
               alpha=1.0, size=6):
    points_plotitem = gl.GLScatterPlotItem(
        pos=points,
        color=hex2rgba(hexcolour, alpha),
        size=size, pxMode=True)

    points_plotitem.setDepthValue(depth)

    pgwindow.addItem(points_plotitem)
    return points_plotitem

# TODO: Unify to PGPoint3D items? Or leave as ndarray?
def updatepoints(points_plotitem: gl.GLScatterPlotItem, points: ndarray,
                 colour=None, alpha=None):
    if colour is None and alpha is None:
        points_plotitem.setData(
            pos=points
        )
    else:
        points_plotitem.setData(
            pos=points,
            color=hex2rgba(colour, alpha)
        )

def plotvector(vector: PGVector3D, pgwindow, hexcolour="ffff00",
               alpha=1.0, depth=10, width=4, antialias=True):
    vector_plotitem = gl.GLLinePlotItem(
        pos=[vector.get_o(), vector.get_o()+vector.get_lxyz()],
        color=hex2rgba(hexcolour, alpha),
        width=width, antialias=antialias)

    vector_plotitem.setDepthValue(depth)

    pgwindow.addItem(vector_plotitem)
    return vector_plotitem

def updatevector():
    pass
    # TODO: Implement

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

def updateframe(frame_plotitems, frame: PGFrame3D, plotscale=1, alpha=None):

    if alpha is None:  # Just update position without overhead of alpha edit
        for i, axis_plotitem in enumerate(frame_plotitems):
            axis_plotitem.setData(pos=[
                frame.get_o(),
                frame.get_o() + frame.get_r()[i] * plotscale])
    else:
        axis_colour = ("ff0000", "00ff00", "0000ff")
        for i, axis_plotitem in enumerate(frame_plotitems):
            axis_plotitem.setData(pos=[
                frame.get_o(),
                frame.get_o() + frame.get_r()[i] * plotscale],
                color=hex2rgba(axis_colour[i], alpha))


# ==== Specific transformation matrices ====

def conv_ECI_geoc(xyz_ECI, rd=6):
    """Converts (x, y, z)|ECI to (r, long, lat)|ECI

    Measures are taken to ensure that no ambiguity occurs at 90 degrees pitch,
    which corresponds to x,y=0, z!=0. In this case, the value for longitude is
    set to 0 degrees, and the latitude to +/- 90 degrees depending on the sign
    of the z-coordinate.

    The method by which this is done is simple and efficient, but introduces
    problems when the angles are 'effectively' zero, but not 'actually' zero
    due to floating point errors. This is subverted by rounding off at a
    certain order of magnitude which can be set by `rd`, with `rd=3` rounding
    to mm. This unfortunately increases evaluation time from 8 us to 16 us,
    and decreases precision in some places, but this is deemed acceptable in
    the application that this function is designed for.

    The case of x,y,z=0 is also singular, and is handled by raising an
    AssertionError, as the direction of a zero-length vector is not defined.
    """

    if len(xyz_ECI) != 3:
        raise AssertionError(f"xyz_ECI is length {len(xyz_ECI)} but must be length 3!")

    x, y, z = xyz_ECI[0], xyz_ECI[1], xyz_ECI[2]

    # Subvert the singularities at -90 and 90 degrees pitch
    if round(x, rd) == 0 and round(y, rd) == 0:
        if round(z, rd) == 0:
            raise ValueError("xyz_ECI has no defined direction, as its length is 0!")
        else:
            r = abs(z)
            longitude = 0
            latitude = sign(z)*pi/2

    else:
        r = (x**2 + y**2 + z**2)**0.5
        longitude = sign(y)*arccos(x/(x**2 + y**2)**0.5)
        latitude = pi/2-arccos(z/r)

    return array([r, longitude, latitude])

# def conv_ECEF_geoc(coor_ECEF, rd=6):
#     """Converts (x, y, z)|ECEF to (r, long, lat)|ECEF
#
#     Measures are taken to ensure that no ambiguity occurs at 90 degrees pitch,
#     which corresponds to x,y=0, z!=0. In this case, the value for longitude is
#     set to 0 degrees, and the latitude to +/- 90 degrees depending on the sign
#     of the z-coordinate.
#
#     The method by which this is done is simple and efficient, but introduces
#     problems when the angles are 'effectively' zero, but not 'actually' zero
#     due to floating point errors. This is subverted by rounding off at a
#     certain order of magnitude which can be set by `rd`, with `rd=3` rounding
#     to mm. This unfortunately increases evaluation time from 8 us to 16 us,
#     and decreases precision in some places, but this is deemed acceptable in
#     the application that this function is designed for.
#
#     The case of x,y,z=0 is also singular, and is handled by raising an
#     AssertionError, as the direction of a zero-length vector is not defined.
#     """
#
#     if len(coor_ECEF) != 3:
#         raise AssertionError(f"coor_ECEF is length {len(coor_ECEF)} but must be length 3!")
#
#     x, y, z = coor_ECEF[0], coor_ECEF[1], coor_ECEF[2]
#
#     # Subvert the singularities at -90 and 90 degrees pitch
#     if round(x, rd) == 0 and round(y, rd) == 0:
#         if round(z, rd) == 0:
#             raise ValueError("coor_ECEF has no defined direction, as its length is 0!")
#         else:
#             r = abs(z)
#             longitude = 0
#             latitude = sign(z)*pi/2
#
#     else:
#         r = (x**2 + y**2 + z**2)**0.5
#         longitude = sign(y)*arccos(x/(x**2 + y**2)**0.5)
#         latitude = pi/2-arccos(z/r)
#
#     return array([r, longitude, latitude])

def R_ECI_NED(long, lat):
    """Converts (x, y, z)|ECI to (x, y, z)|NED
    """
    # print(f"[DEBUG] R_NED_ECI(): long={round(long*180/pi, 1)} lat={round(lat*180/pi, 1)}")
    s_lat, c_lat = sin(lat), cos(lat)
    s_long, c_long = sin(long), cos(long)
    R = array([
        [-s_lat*c_long, -s_lat*s_long,  c_lat],
        [      -s_long,        c_long,      0],
        [-c_lat*c_long, -c_lat*s_long, -s_lat]])

    return R

def R_NED_ECI(long, lat):
    """Converts (x, y, z)|NED to (x, y, z)|ECI
    """
    return R_ECI_NED(long, lat).transpose()

# def R_ECEF_NED(long, lat):
#     """Converts (x, y, z)|ECEF to (x, y, z)|NED
#     """
#     # print(f"[DEBUG] R_NED_ECEF(): long={round(long*180/pi, 1)} lat={round(lat*180/pi, 1)}")
#     s_lat, c_lat = sin(lat), cos(lat)
#     s_long, c_long = sin(long), cos(long)
#     R = array([
#         [-s_lat*c_long, -s_lat*s_long,  c_lat],
#         [      -s_long,        c_long,      0],
#         [-c_lat*c_long, -c_lat*s_long, -s_lat]])
#
#     return R

# def R_NED_ECEF(long, lat):
#     """Converts (x, y, z)|NED to (x, y, z)|ECEF
#     """
#     return R_ECEF_NED(long, lat).transpose()

def R_SI_B(axyz):
    """Converts (x, y, z)|SI to (x, y, z)|B"""
    return R(array([axyz[0], axyz[1], axyz[2]]))

def R_B_SI(axyz):
    """Converts (x, y, z)|B to (x, y, z)|SI"""
    return R_SI_B(axyz).transpose()

def R_ECI_ECEF(th_E):
    """Converts (x, y, z)|ECI to (x, y, z)|ECEF
    """
    return RZ(th_E)

def R_ECEF_ECI(th_E):
    """Converts (x, y, z)|ECEF to (x, y, z)|ECI
    """
    return R_ECI_ECEF(th_E).transpose()

# ==== Miscellaneous utilities
def wrap(angle, angle_range):
    angle_wrapped = (angle + angle_range / 2) % angle_range - angle_range / 2
    if angle_wrapped == -angle:
        angle_wrapped = -angle_wrapped
    return angle_wrapped

def sign(number):
    if number == 0:
        return 1
    else:
        return number/abs(number)

def uv3d(vector: ndarray):
    """Efficiently transforms a 3D ndarray vector into its unit vector.
    Seems more than twice as efficient as vector/np.linalg.norm()
    """
    return vector / (vector[0]**2+vector[1]**2+vector[2]**2)**(1/2)

# print(R_ECEF_ECI(pi/4)@array([1,0,0]))  # TODO REMOVE