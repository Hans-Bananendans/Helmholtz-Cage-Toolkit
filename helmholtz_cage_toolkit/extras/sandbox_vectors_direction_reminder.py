import numpy as np
from numpy import pi, array, sin, cos, arccos, ndarray, dot, eye
from time import time
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from pg3d import (
    RX, RY, RZ, R,
    PGPoint3D, PGVector3D, PGFrame3D,
    plotgrid, plotpoint, plotpoints, plotvector, plotframe,
    updatepoint, updatepoints, updatevector, updateframe,
    hex2rgb, hex2rgba,
)


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

R = np.vstack([X1, Y1, Z1])

# CYAN point - Transform axis system, where point "rotates" BACKWARDS
p1_t1 = R@p1
p1_t1_plotitem = plotpoint(PGPoint3D(p1_t1), w, hexcolour="00ffff")

# MAGENTA point - Transform axis system and point "together"
p1_t2 = R.transpose()@p1
p1_t2_plotitem = plotpoint(PGPoint3D(p1_t2), w, hexcolour="ff00ff")

print("R =", R)

# === END OF SANDBOX ========================================================
if __name__ == '__main__':
    pg.exec()
