from time import time

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config


class HHCPlotArrow:
    def __init__(self, color="w", width=3):
        self.pen = pg.mkPen(color, width=width)

        self.tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.tail.setPen(self.pen)
        self.tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0,
                                pen=None, brush=color, pxMode=True)

        self.tail_clip = 0.9  # TODO Tune this better

    def update(self, x, y, scale):
        if x == 0. and y == 0.:
            # Hide arrow
            self.tail.setLine(0., 0., 0., 0.)
            self.tip.setStyle(headLen=0)
        else:
            self.tail.setLine(
                0., 0., self.tail_clip * y / scale, -self.tail_clip * x / scale
            )
            self.tip.setPos(x / scale, x / scale)

            self.tip.setStyle(
                headLen=20,
                angle=self.tail.line().angle() - 180
            )


class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self, datapool, direction="YZ", size=(360, 360)):
        super().__init__()

        self.direction = direction

        self.bscale = datapool.config["visualizer_bscale"]

        self.plot_obj = self.addPlot(row=0, col=0, antialias=True)
        self.resize(size[0], size[1])
        self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot_obj.showGrid(x=True, y=True)
        # self.plot_obj.setData(antialias=True)
        self.plot_obj.showAxis("bottom", True)
        self.plot_obj.showAxis("left", True)
        self.plot_obj.getAxis("bottom").setStyle(showValues=False)
        self.plot_obj.getAxis("left").setStyle(showValues=False)

        if direction == "YZ":
            self.plot_hhc_elements_yz()
        elif direction == "XY":
            self.plot_hhc_elements_xy()
        elif direction == "mXY":
            self.plot_hhc_elements_mxy()
        else:
            raise ValueError("'direction' must be 'XY', 'mXY', or 'YZ'!")


        self.arrows = self.create_arrows()
        for arrow in self.arrows:
            self.plot_obj.addItem(arrow.tail)
            self.plot_obj.addItem(arrow.tip)

        self.bvals_prev = [[0., 0., 0.], ]*len(self.arrows)

        # self.arrow_pen = pg.mkPen("c", width=3)
        # self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        # self.arrow_tail.setPen(self.arrow_pen)

        self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)

        self.plot_obj.addItem(self.arrow_tail)
        self.plot_obj.addItem(self.arrow_tip)

    def create_arrows(self):
        # Intended to be overloaded
        arrows = []

        arrow_Bm = HHCPlotArrow(color=self.datapool.config["plotcolor_Bm"])
        arrows.append(arrow_Bm)

        return arrows


    def plot_hhc_elements_mxy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1, -1-ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95, 0.75, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(coils[i])


        walls = (
            QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
            QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
        )
        for wall in walls:
            wall.setPen(pg.mkPen("#FFF6"))
            wall.setBrush(pg.mkBrush("#FFF1"))
            self.plot_obj.addItem(wall)


        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )
        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)

    def plot_hhc_elements_xy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

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
            self.plot_obj.addItem(coils[i])

        # walls = (
        #     QGraphicsRectItem(QRectF(-1.0, 1.0, 2 * 1.0, 0.05)),
        #     QGraphicsRectItem(QRectF(-1.0, -1.0, 0.05, 2 * 1.0)),
        # )
        # for wall in walls:
        #     wall.setPen(pg.mkPen("#FFF6"))
        #     wall.setBrush(pg.mkBrush("#FFF1"))
        #     self.plot_obj.addItem(wall)

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )
        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)

    def plot_hhc_elements_yz(self):
        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#0F0F", "#22FF", "#F00F")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot_obj.addItem(tripod[i])

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
            self.plot_obj.addItem(coils[i])

        walls = (
            QGraphicsRectItem(QRectF(1.0, -1.0, 0.05, 2 * 1.0)),
        )
        for wall in walls:
            wall.setPen(pg.mkPen("#FFF6"))
            wall.setBrush(pg.mkBrush("#FFF1"))
            self.plot_obj.addItem(wall)

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.05, 2 * 0.25, 1 * 0.05)),
            QGraphicsRectItem(QRectF(-0.15, -1, 0.05, 0.95)),
            QGraphicsRectItem(QRectF(0.1, -1, 0.05, 0.95)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot_obj.addItem(item)

    def plot_ghosts(self, schedule):
        """Plots hazy, dotted paths indicating the magnetic field vector
        movement during the schedule.
        """
        # TODO Make ghost_pen inherit properties from somewhere else (Bc?)
        ghost_pen = pg.mkPen((0, 255, 255, 64), width=1, style=Qt.DotLine)

        if self.direction == "XY":
            self.plot_obj.plot(
                schedule[3]/self.bscale,    # X
                schedule[4]/self.bscale,    # Y
                pen=ghost_pen
            )

        elif self.direction == "mXY":
            self.plot_obj.plot(
                schedule[4]/self.bscale,    # Y
                -schedule[3]/self.bscale,   # -X
                pen=ghost_pen
            )

        elif self.direction == "YZ":
            self.plot_obj.plot(
                schedule[4]/self.bscale,    # Y
                schedule[5]/self.bscale,    # Z
                pen=ghost_pen
            )

        # elif self.direction == ...   # TODO Generalize to all orientations

    def update_arrows(self, bvals):
        if len(bvals) != len(self.arrows):
            raise AssertionError(
                "Gave update_arrows() more bvals ({}) than it has arrows ({})".format(
                    len(bvals), len(self.arrows)))

        t0 = time()

        for i, arrow in enumerate(self.arrows):
            # Skip if value did not change:
            if bvals[i] == self.bvals_prev[i]:
                pass
            else:
                arrow.update(bvals[i][0], bvals[i][1], bvals[i][2], self.bscale)

        t1 = time()

        arrow.update(bvals[i][0], bvals[i][1], bvals[i][2], self.bscale)

        t2 = time()

        print("[TIMING] update_arrows()   opt:", round(1E6*(t1-t0)), "us")
        print("[TIMING] update_arrows() unopt:", round(1E6*(t2-t1)), "us")

        self.bvals_prev = bvals

