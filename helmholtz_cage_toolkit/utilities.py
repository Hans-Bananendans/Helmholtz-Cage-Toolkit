from datetime import date
from numpy import array, ones, linspace, cos, sin
from pyIGRF import igrf_value

# from helmholtz_cage_toolkit import *

def tB_to_schedule(t, B):
    n = len(t)
    return array([
        linspace(0, n-1, n, dtype=int),
        n*ones(n),
        t,
        B[0],
        B[1],
        B[2]
    ])

def cross3d(v1, v2):
    """Efficient cross product for 3D vectors to use instead of the much slower
    numpy.cross()
    """
    return array([v1[1]*v2[2] - v1[2]*v2[1],
                  v1[2]*v2[0] - v1[0]*v2[2],
                  v1[0]*v2[1] - v1[1]*v2[0]])


def IGRF_from_UNIX(lat, long, alt_km, t_unix, rotation_matrix=None):
    # First calculate current day from unix epoch, expressed as decimal year.
    # For example: 1707115918.0833216 -> 05-02-2024 -> 2024.0959
    today = date.fromtimestamp(t_unix)
    year_decimal = today.year + (today - date(today.year, 1, 1)).days / 365

    print("IGRF_from_UNIX() year =", year_decimal)

    # Calculate magnetic field vector
    _, _, _, bx, by, bz, _ = igrf_value(lat, long, alt_km, year_decimal)

    B_NED = [bx, by, bz]

    # Rotate to ENU
    B_ENU = array([B_NED[1], B_NED[0], -B_NED[2]])

    # Rotate by provided rotation matrix
    if rotation_matrix:
        B_rotated = array(rotation_matrix)@B_ENU
    else:
        B_rotated = B_ENU

    return [B_rotated[0], B_rotated[1], B_rotated[2]]
