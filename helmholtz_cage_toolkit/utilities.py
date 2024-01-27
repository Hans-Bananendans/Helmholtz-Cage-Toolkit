from numpy import array, ones, linspace

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