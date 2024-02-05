from time import time

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config


class HHCPlotArrow:
    def __init__(self, color="w", width=3, enable_tip=True):
        self.pen = pg.mkPen(color, width=width)

        self.tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.tail.setPen(self.pen)

        self.plot_elements = [self.tail]

        # Can prevent ~70 us per arrow redraw by not drawing tips, so if high
        # plottings speed is desirable, disable the tips.
        self.enable_tip = enable_tip
        if enable_tip:
            self.tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0,
                                    pen=None, brush=color, pxMode=True)

            self.tail_clip = 0.91  # Shortens the tail to prevent clipping with tip
            self.plot_elements.append(self.tip)
        else:
            self.tip = None
            self.tail_clip = 1


    # def calc_angle(self, x, y):  # UNUSED
    #     if x == 0:
    #         if y == 0:
    #             return 0        # Angle undefined, just return 0
    #         elif y > 0:
    #             return 90       # 90 degrees for any positive y
    #         else:
    #             return 270      # 270 degrees for any negative y
    #     elif x >= 0:            # +X quadrants
    #         return 180/pi*arctan(y/x)
    #     else:                   # -X quadrants
    #         return 180+180/pi*arctan(y/x)


    def update(self, x, y, scale):
        """Updates the x, y position of the vector by:
         - drawing the tail line from (0, 0) to (x, y)
         - setting the (X, Y) location of the tip to (x, y)
         - rotating the arrow tip by using setStyle()

        On optimization, the first two steps typically take 1-5 us, the third
        step takes 60-70 us. This seems to be inherent to the workings of the
        setStyle() method, and not the computation of the angle through
        QGraphicsLineItem.line().angle(). Manually computing the angle with
        numpy.arctan() does not improve performance.

        If a cutting-edge plotting function is needed, just make an
        implementation of HHCPlot and HHCPlotArrow that do not use
        pyqtgraph.ArrowItem, as it seems quite bad for what it is. Either do
        not use an arrow tip at all, or find a quick way to draw one with
        QGraphicsLineItems.

        To aid with functions where speed is essential, you construct
        HHCPlotArrows without a tip by passing a special keyword argument:

            tipless_arrow = HHCPlotArrow(enable_tip = False)

        This reduces the update() call from ~70 us to 3 us.
        """


        # t0 = time()  # [TIMING]
        if x == 0. and y == 0.:
            # Hide arrow, by setting tail line to length 0, and tip headLen to 0
            self.tail.setLine(0., 0., 0., 0.)
            # t1 = time()  # [TIMING]
            if self.enable_tip:
                self.tip.setStyle(headLen=0)
            # t2 = time()  # [TIMING]
        else:
            self.tail.setLine(
                0., 0., self.tail_clip * x / scale, self.tail_clip * y / scale
            )
            # t1 = time()  # [TIMING]
            if self.enable_tip:
                self.tip.setPos(x / scale, y / scale)
            # t2 = time()  # [TIMING]
            if self.enable_tip:
                self.tip.setStyle(
                    headLen=20,
                    angle=self.tail.line().angle() - 180
                    # angle=self.calc_angle(x, y) - 180  # Does not seem to improve performance
                )

        # t3 = time()  # [TIMING]
        # print("[TIMING] update(): {} , {} , {} \u03bcs".format(
        #     round(1E6*(t1-t0), 2), round(1E6*(t2-t1), 2), round(1E6*(t3-t2), 2)))


class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self,
                 datapool,
                 arrows: [HHCPlotArrow],
                 direction="YZ",
                 size=(360, 360)
                 ):
        super().__init__()

        self.datapool = datapool

        self.direction = direction

        self.bscale = datapool.config["visualizer_bscale"]


        self.plot_obj = self.addPlot(row=0, col=0, antialias=True)
        self.setAntialiasing(True)  # TODO benchmark effect on draw time
        self.resize(size[0], size[1])  # Probably does not do anything, judging by source code
        self.setAspectLocked(True)  # Also seems to do jack shit

        self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot_obj.showGrid(x=True, y=True)
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


        self.arrows = tuple(arrows)
        for arrow in self.arrows:
            for plot_element in arrow.plot_elements:
                self.plot_obj.addItem(plot_element)


        self.bvals_prev = [[0., 0., 0.], ]*len(self.arrows)

        # self.arrow_pen = pg.mkPen("c", width=3)
        # self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        # self.arrow_tail.setPen(self.arrow_pen)

        # self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)
        #
        # self.plot_obj.addItem(self.arrow_tail)
        # self.plot_obj.addItem(self.arrow_tip)

    # def create_arrows(self):
    #     # Intended to be overloaded
    #     arrows = []
    #
    #     # arrow_Bm = HHCPlotArrow(color=self.datapool.config["plotcolor_Bm"])
    #     # arrows.append(arrow_Bm)
    #
    #     return arrows


    def plot_hhc_elements_mxy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1, -1-ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#04FF")):
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
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#04F8", "#04F8")):
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
        for i, c in enumerate(("#F00F", "#0F0F", "#04FF")):
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
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#04F8", "#04F8")):
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
        for i, c in enumerate(("#0F0F", "#04FF", "#F00F")):
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
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#04F8", "#04F8")):
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

    def plot_ghosts(self, schedule, color=(255, 255, 255, 64)):
        """Plots hazy, dotted paths indicating the magnetic field vector
        movement during the schedule.
        """
        # TODO Make ghost_pen inherit properties from somewhere else (Bc?)
        ghost_pen = pg.mkPen(color, width=1, style=Qt.DotLine)

        if self.direction == "XY":
            self.plot_obj.plot(
                array(schedule[3])/self.bscale,    # X
                array(schedule[4])/self.bscale,    # Y
                pen=ghost_pen
            )

        elif self.direction == "mXY":
            self.plot_obj.plot(
                array(schedule[4])/self.bscale,    # Y
                -array(schedule[3])/self.bscale,   # -X
                pen=ghost_pen
            )

        elif self.direction == "YZ":
            self.plot_obj.plot(
                array(schedule[4])/self.bscale,    # Y
                array(schedule[5])/self.bscale,    # Z
                pen=ghost_pen
            )

        # elif self.direction == ...   # TODO Generalize to all orientations
        # Could achieve this with a mapping dict to transform value routings:
        # routing_map = {
        #     "XY": [3, 4, 1, 1],
        #     "mXY": [4, 3, 1, -1],
        #     "YZ": [4, 5, 1, 1],
        #     etc...
        # }

    def update_arrows_unoptimized(self, bvals):
        if len(bvals) != len(self.arrows):
            raise AssertionError(
                "Gave update_arrows() more bvals ({}) than it has arrows ({})".format(
                    len(bvals), len(self.arrows)))

        # t0 = time()

        for i, arrow in enumerate(self.arrows):
            if self.direction == "YZ":
                arrow.update(bvals[i][1], bvals[i][2],
                             self.bscale)
            elif self.direction == "XY":
                arrow.update(bvals[i][0], bvals[i][1],
                             self.bscale)
            elif self.direction == "mXY":
                arrow.update(bvals[i][1], -bvals[i][0],
                             self.bscale)

        # t1 = time()

        # print("[TIMING] update_arrows() UNOPT:", round(1E6*(t1-t0)), "us")


    def update_arrows(self, bvals):
        """

        Optimizations: Ensures that:
         - If for arrow i in self.arrows, given bvals[i] did not change
            compared to the previous value (tracked by self.bvals_prev[i], it
            will skip the plotting of that arrow.
            Effect: ~14 us -> ~1 us for non-changing arrows

        """
        if len(bvals) != len(self.arrows):
            raise AssertionError(
                "Gave update_arrows() more bvals ({}) than it has arrows ({})".format(
                    len(bvals), len(self.arrows)))

        # tt = []   # [TIMING]
        for i, arrow in enumerate(self.arrows):
            # t0 = time()   # [TIMING]

            # Skip if value did not change:
            if bvals[i] == self.bvals_prev[i]:
                pass
            else:
                if self.direction == "YZ":
                    arrow.update(bvals[i][1], bvals[i][2],
                                 self.bscale)
                elif self.direction == "XY":
                    arrow.update(bvals[i][0], bvals[i][1],
                                 self.bscale)
                elif self.direction == "mXY":
                    arrow.update(bvals[i][1], -bvals[i][0],
                                 self.bscale)

            # tt.append(time()-t0)    # [TIMING]

        self.bvals_prev = bvals

        # print("[TIMING] update_arrows()      :", [round(1E6*t) for t in tt], "\u03bcs")  # [TIMING]

    def update_arrow(self, i_arrow, b):
        """
        Implementation of update_arrows that updates only a single arrow, which
        requires the user specifying the index of the arrow in self.arrows

        Optimizations: Ensures that:
         - If for arrow i in self.arrows, given bvals[i] did not change
            compared to the previous value (tracked by self.bvals_prev[i], it
            will skip the plotting of that arrow.
            Effect: ~14 us -> ~1 us for non-changing arrows

        """

        print(f"[DEBUG] update_arrow({i_arrow}, {b})")
        if len(b) != 3:
            raise AssertionError(
                "Given `b` longer ({}) than it should be (3)".format(len(b))
            )

        arrow = self.arrows[i_arrow]

        print(f"[DEBUG] Updating arrow {i_arrow}: {arrow}")

        # Skip if value did not change:
        if b == self.bvals_prev[i_arrow]:
            pass
        else:
            if self.direction == "YZ":
                arrow.update(b[1], b[2], self.bscale)
            elif self.direction == "XY":
                arrow.update(b[0], b[1], self.bscale)
            elif self.direction == "mXY":
                arrow.update(b[1], -b[0], self.bscale)

        self.bvals_prev[i_arrow] = b
