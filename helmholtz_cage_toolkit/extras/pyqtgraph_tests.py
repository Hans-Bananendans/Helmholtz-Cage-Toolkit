import numpy as np

import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore

## Create a GL View widget to display data
app = pg.mkQApp("GLSurfacePlot Example")
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('pyqtgraph example: GLSurfacePlot')
w.setCameraPosition(distance=10)

## Add a grid to the view
g = gl.GLGridItem()
g.scale(2, 2, 1)
g.setDepthValue(10)  # draw grid after surfaces since they may be translucent
w.addItem(g)

## Simple surface plot example
## x, y values are not specified, so assumed to be 0:50
# s = 4
# data = np.random.normal(size=(s, s))
# # print(data)
# z = pg.gaussianFilter(data, (1, 1))
# # print(z)
# p1 = gl.GLSurfacePlotItem(z=data, shader='shaded', color=(0.5, 0.5, 1, 1))
# p1.scale(16. / s-1, 16. / s-1, 1.0)
# # p1.translate(-18, 2, 0)
# w.addItem(p1)

def generate_earth_mesh(resolution=(16, 16)):
    sr = resolution  # Sphere resolution
    mesh = gl.MeshData.sphere(rows=sr[0], cols=sr[1])

    earth_colours = {
        "ocean": "#002bff",
        "ice": "#eff1ff",
        "cloud": "#dddddd",
        "green1": "#1b5c0f",
        "green2": "#093800",
        "green3": "#20c700",
        "test": "#ff0000",
    }

    def hex2rgb(hex: str):
        """Converts a hex colour string (e.g. '#3faa00') to [0, 1] rgb values"""
        hex = hex.lstrip("#")
        rgb255 = list(int(hex[i:i + 2], 16) for i in (0, 2, 4))
        return [c/255 for c in rgb255]


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

    mesh.setFaceColors(colours)
    return mesh


# colours[::2, 0:3] = cconv(earth_colours["ocean"])

# colours[::2,0:3] = 0


# colors[:,1] = np.linspace(0, 1, colors.shape[0])
# md.setFaceColors(colours)
earth_meshitem = gl.GLMeshItem(
    meshdata=generate_earth_mesh(resolution=(16, 24)),
    smooth=True,
    computeNormals=True,
    shader='shaded')

w.addItem(earth_meshitem)

# md.setFaceColors(colours)
# m3.meshDataChanged()




if __name__ == '__main__':
    pg.exec()
