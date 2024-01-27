import numpy as np
from numpy import (
    pi,
    array, ndarray,
    sin, cos, arccos,
    dot, zeros, eye, linspace, vstack, column_stack,
    empty
)

import threading
import matplotlib.pyplot as plt
from time import time, sleep

from pyIGRF import igrf_value

import pyqtgraph as pg
from config import config

from ast import literal_eval
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, QSize, Qt, QRunnable, QThreadPool, QTimer, QRectF, QLineF
from PyQt5.QtGui import (
    # QAction,
    # QActionGroup,
    QFont,
    QIcon,
    QImage,
    QKeySequence,
    QPixmap,
    QPalette,
    QColor,
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFileDialog,
    QGraphicsView,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


# layout0.addWidget(QLabel("Front view (YZ)"), 0, 0)
# layout0.addWidget(hhcplot_yz, 1, 0)
#
# layout0.addWidget(QLabel("Top view (XY)"), 0, 1)
# layout0.addWidget(hhcplot_xy, 1, 1)
# # layout0.addWidget(QLabel("Layout2dPlots"))

# setLayout(layout0)



def read_bsch_file(filename):
    # TODO: Should headerless files be supported? Seems like a lot of hassle
    # for little gain.
    #
    header_length = 10
    with open(filename, 'r') as bsch_file:
        flag = (bsch_file.readline()).strip("\n")
        schedule_name = (bsch_file.readline()).strip("\n")
        generator = bsch_file.readline().strip("\n").split("=")[-1]
        generation_parameters = literal_eval(bsch_file.readline())
        for i in range(5):
            bsch_file.readline()
        end_of_header = (bsch_file.readline()).strip("\n")

        # for i, item in enumerate((flag, schedule_name, generator, generation_parameters, end_of_header)):
        #     print(i, ":", item, type(item))

        # Checks
        if flag != "!BSCH":
            raise AssertionError(f"While loading '{filename}', header flag !BSCH not found. Are you sure it is a valid .bsch file?")

        if end_of_header != "#"*32:
            raise AssertionError(f"While loading '{filename}', could not find end of header. Are you sure it is a valid .bsch file?")

        recognised_generators = ("cyclics", "orbital")
        if generator not in recognised_generators:
            raise AssertionError(f"While loading '{filename}', encountered unknown generator name {generator}. Currently supported generators: {recognised_generators}")

        raw_schedule = bsch_file.readlines()
        n = len(raw_schedule)
        # print(raw_schedule, type(raw_schedule), len(raw_schedule))

        t = empty(n)
        B = empty((n, 3))
        for i, line in enumerate(raw_schedule):
            stringvals = line.strip("\n").split(",")
            t[i] = stringvals[2]
            B[i, :] = array((stringvals[3], stringvals[4], stringvals[5]))
        B = column_stack(B)

    bsch_file.close()

    return t, B, schedule_name, generator, generation_parameters




class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self, direction="YZ", bscale=1.0):
        super().__init__()

        self.direction = direction
        self.bscale = bscale
        self.plot = self.addPlot(row=0, col=0)
        self.resize(360, 360)
        self.plot.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot.showGrid(x=True, y=True)
        self.plot.showAxis('bottom', True)
        self.plot.showAxis('left', True)

        if direction == "YZ":
            self.plot_hhc_elements_yz()
        elif direction == "XY":
            self.plot_hhc_elements_xy()
        else:
            raise ValueError("Parameter 'direction' must be 'XY' or 'YZ'!")

        # self.arrow_length = 100 * 1.28  # Correcting for plot abnormalities

        self.arrow = pg.ArrowItem(angle=0, headLen=20, tailLen=self.arrow_length(), pen=None, brush='y')
        self.plot.addItem(self.arrow)
        self.arrow.setPos(-1, 0)

        self.testarrow = pg.ArrowItem(angle=0, headLen=20, tailLen=300, pen="c", brush='g')
        self.plot.addItem(self.testarrow)

    def arrow_length(self, l=1.0):
        # return 100*1.28*l/self.bscale - 20
        return l

    def plot_hhc_elements_xy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot.addItem(coils[i])

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot.addItem(item)

    def plot_hhc_elements_yz(self):
        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#0F0F", "#22FF", "#F00F")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot.addItem(coils[i])

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.05, 2 * 0.25, 1 * 0.05)),
            QGraphicsRectItem(QRectF(-0.15, -1, 0.05, 0.95)),
            QGraphicsRectItem(QRectF(0.1, -1, 0.05, 0.95)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot.addItem(item)





# ============================================================================

app = pg.mkQApp("Plotting Example")

win = QWidget()
win.resize(1600, 780)
layout1 = QHBoxLayout()
win.setLayout(layout1)

#
#
# pg.addWidget(hhcplot_object)
# pg.setConfigOptions(antialias=True)

# win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
bscale = 1

hhcplot_yz = HHCPlot(direction="YZ", bscale=bscale)
hhcplot_xy = HHCPlot(direction="XY", bscale=bscale)

layout1.addWidget(hhcplot_yz)
layout1.addWidget(hhcplot_xy)

win.show()


def update_bvector(bx, by, bz):
    print("update_bvector()")
    # step = 0
    # bx, by, bz = BX[step], BY[step], BZ[step]
    xy = np.array([bx, by])
    yz = np.array([by, bz])
    b = np.array([1, 0])

    if by != 0:
        sign_y = by / np.abs(by)
    else:
        sign_y = 1
    # angle_xy = 0
    angle_xy = sign_y * (180 / np.pi * (np.arccos(np.dot(xy, b) / (np.linalg.norm(xy) * np.linalg.norm(b)))))
    abslen_xy = np.linalg.norm(xy)
    print("abslen_xy =", abslen_xy)

    if bz != 0:
        sign_z = bz / np.abs(bz)
    else:
        sign_z = 1
    # angle_yz = 0
    angle_yz = sign_z * (180 / np.pi * (np.arccos(np.dot(yz, b) / (np.linalg.norm(yz) * np.linalg.norm(b)))))
    abslen_yz = np.linalg.norm(yz)
    print("abslen_yz =", abslen_yz)
    # plot_correction = 100*1.28

    # hhcplot_xy.arrow.setStyle(angle=-angle_xy + 180, tailLen=hhcplot_xy.arrow_length(abslen_xy))
    # hhcplot_xy.arrow.setStyle(angle=-angle_xy + 180, tailLen=abslen_xy)
    hhcplot_xy.arrow.setStyle(angle=-angle_xy + 180, tailLen=1)
    # hhcplot_xy.arrow.setPos(1, 1)
    hhcplot_xy.arrow.setPos(bx / bscale, by / bscale)

    # hhcplot_yz.arrow.setStyle(angle=-angle_yz + 180, tailLen=hhcplot_yz.arrow_length(abslen_yz))
    hhcplot_yz.arrow.setStyle(angle=-angle_yz + 180, tailLen=abslen_yz)
    # hhcplot_yz.arrow.setPos(0, 0)
    hhcplot_yz.arrow.setPos(by / bscale, bz / bscale)

# win.setWindowTitle('pyqtgraph example: Plotting')


filename = "myschedule2.bsch"
t, B, _, _, _ = read_bsch_file(filename)


# global BX, BY, BZ, step, n_steps
#
# BX, BY, BZ = B
# step = 0,
# n_steps = len(BX)


# bscale = config["visualizer_bscale"]

#
# print(hhcplot_yz, type(hhcplot_yz))
# win.addPlot(hhcplot_yz)
# win.addPlot(hhcplot_xy)


do_plot = True
def toggle_do_plot():
    do_plot = True

timer = threading.Timer(1.0, toggle_do_plot)

step = 0

update_bvector(0.5, -0.5, 0.5)

# while True:
#     try:
#         if do_plot:
#             print("Hi")
#             update_bvector(B[0][step], B[1][step], B[2][step])
#             step += 1
#             do_plot = False
#             timer.start()
#
#
#     except KeyboardInterrupt:
#         break

# timer1 = QTimer()
# timer1.timeout.connect(update_bvector)
# timer1.start(int(1000 / 30))

if __name__ == '__main__':
    pg.exec()