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
    return array([v1[1]*v2[2] - v1[2]*v2[1],
                  v1[2]*v2[0] - v1[0]*v2[2],
                  v1[0]*v2[1] - v1[1]*v2[0]])