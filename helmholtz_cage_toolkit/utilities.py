from numpy import array, ones, linspace

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
    return array([V1[1]*V2[2] - V1[2]*V2[1],
                  V1[2]*V2[0] - V1[0]*V2[2],
                  V1[0]*V2[1] - V1[1]*V2[0]])