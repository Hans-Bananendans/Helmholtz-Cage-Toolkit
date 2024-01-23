import numpy as np
from numpy import (
    pi,
    array, ndarray,
    sin, cos, arccos,
    dot, zeros, eye, linspace, vstack, column_stack,
    empty, repeat,
)

import threading
import matplotlib.pyplot as plt
from time import time, sleep

from pyIGRF import igrf_value

import pyqtgraph as pg
from config import config

from ast import literal_eval
from PyQt5 import QtCore
from PyQt5.QtCore import (
    QDir,
    QSize,
    Qt,
    QRunnable,
    QThreadPool,
    QTimer,
    QRectF,
    QLineF,
)

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
    QPainter,
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



class DataPool:
    def __init__(self, config):
        self.config = config

        # Devices
        self.interface_board = None
        self.supplies = [None, None, None]
        self.magnetometer = None

        # Measurement
        self.adc_pollrate = self.config["adc_pollrate"]
        # TODO: Revert to 0. 0. 0.
        self.B_m = np.array([0., 1., 0.])   # B measured by magnetometer
        self.tBm = 0.0                      # Unix acquisition time of latest measurement


        self.schedule = np.zeros((6, 2))

    def get_schedule_duration(self):
        return self.schedule[2][-1]

    def get_schedule_steps(self):
        return len(self.schedule[0])


class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self, direction="YZ", bscale=1.0):
        super().__init__()

        self.direction = direction
        # self.bscale = bscale
        self.bscale = 10_000_000  # TODO

        self.plot_obj = self.addPlot(row=0, col=0, antialias=True)
        self.resize(360, 360)
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
            raise ValueError("Parameter 'direction' must be 'XY' or 'YZ'!")

        # self.arrow_length = 100 * 1.28  # Correcting for plot abnormalities

        self.arrow_pen = pg.mkPen("c", width=3)
        self.arrow_tail = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.arrow_tail.setPen(self.arrow_pen)

        self.arrow_tip = pg.ArrowItem(angle=90, headLen=20, tipAngle=30, tailLen=0, pen=None, brush='c', pxMode=True)

        self.plot_obj.addItem(self.arrow_tail)
        self.plot_obj.addItem(self.arrow_tip)


        # self.arrow = pg.ArrowItem(angle=0, headLen=20, tailLen=self.arrow_length(), pen=None, brush='y', pxMode=False)
        # self.plot_obj.addItem(self.arrow)
        # self.arrow.setPos(-1, 0)

    # def arrow_length(self, l=1.0):
    #     return 100*1.28*l/self.bscale - 20

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

    @staticmethod
    def draw_wall_element(plot_obj, aspect_ratio=0.05, stripes=20, direction="vertical", side="pos"):

        pen = pg.mkPen("w", width=2)
        length = 2
        midpos = [1, 0]

        if direction == "vertical":
            mainwall = QGraphicsLineItem(QLineF(midpos[0], -length/2, midpos[0], length/2))



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



class CyclicsPlot(pg.GraphicsLayoutWidget):
    def __init__(self, datapool):
        super().__init__()

        self.datapool = datapool

        # self.bscale = 10_000_000  # TODO

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        # self.plot_obj.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-9)


        self.vline = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen("c", width=2),)
        self.vline.setZValue(10)
        self.plot_obj.addItem(self.vline, ignoreBounds=True)

        self.generate_2D_plots()


    @staticmethod
    def detect_predelay(x):
        if 0.99 * (x[1] - x[0]) > x[3] - x[2] and abs(x[2] - x[1]) < 1E-6:
            return x[1] - x[0]
        else:
            return 0.0

    @staticmethod
    def detect_postdelay(x):
        if 0.99 * (x[-1] - x[-2]) > x[-4] - x[-3] and abs(x[-2] - x[-3]) < 1E-6:
            return x[-1] - x[-2]
        else:
            return 0.0

    def generate_2D_plots(self, show_actual=True, show_points=False):

        t = self.datapool.schedule[2]
        B = array([self.datapool.schedule[3],
                   self.datapool.schedule[4],
                   self.datapool.schedule[5]])

        colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]

        # Detect predelay and postdelay, for more accurate staggered plots
        # Detection algorithms are not guaranteed to catch predelays
        predelay = False
        postdelay = False
        push = [0, -1]
        if self.detect_predelay(t) > 0.0:
            predelay = True
            push[0] = 2
        if self.detect_postdelay(t) > 0.0:
            postdelay = True
            push[1] = -2

        # Generate dataset by
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
                        repeat(B[1, push[0]:push[1]], 2)[:-1],
                        repeat(B[2, push[0]:push[1]], 2)[:-1])
                       )

        for i in range(3):
            if show_actual:
                # Staggered line
                self.plot_obj.plot(t_stag, B_stag[i], pen=colours[i])
                # Line patches for predelay
                if predelay:
                    self.plot_obj.plot([t[0], t[1], t_stag[0]],
                                       [B[i, 0], B[i, 1], B_stag[i, 0]],
                                       pen=colours[i])
                # Line patches for postdelay
                if postdelay:
                    self.plot_obj.plot([t_stag[-1], t[-2], t[-1]],
                                       [B_stag[i, -1], B[i, -2], B[i, -1]],
                                       pen=colours[i])
            else:
                self.plot_obj.plot(t, B[i], pen=colours[i])

            if show_points:
                self.plot_obj.plot(t, B[i],
                                   pen=(0, 0, 0, 0),
                                   symbolBrush=(0, 0, 0, 0),
                                   symbolPen=colours[i],
                                   symbol="o",
                                   symbolSize=6)

        # plot_main.plot(t_interp, y_interp,
        #                pen=(255, 0, 0, 0),
        #                symbolBrush=(0, 0, 0, 0),
        #                symbolPen=(255, 120, 120, 200),
        #                symbol="o",
        #                symbolSize=6)



class SchedulePlayer:
    def __init__(self, datapool, march_interval=10, maxskips=10):

        # External variables: self.datapool.get_schedule_steps()
        self.datapool = datapool

        self.maxskips = maxskips
        self.step = 0
        self.t = 0.0
        self.t_next = 0.0
        self.march_mult = 1
        self.march_interval = march_interval    # [ms] event loop frequency
        self.timer = QTimer()
        self.timer.timeout.connect(self.march)

    def start(self):
        self.timer.start(self.march_interval)

    def stop(self):
        self.timer.stop()

    def reset(self):
        self.step = 0
        self.t = 0.0
        self.t_next = 0.0
        self.update()

    def set_march_mult(self, march_mult):
        self.march_mult = march_mult

    def march(self):
        """ Marches using self.timer

        General idea:
         - Keep it low overhead for cases where number of timer loops is large
            between each call of self.update()
         - Make timer able to recognise when timestep of timer was so large
            that multiple steps have to be skipped.
         - Make timer able to recognise when current step exceeds total number
            of steps, and handle this case correctly.

        Setup:
        1. Find out whether t is larger than t_next. If not, increment by dt,
            where dt is current time [s] plus ( time interval per march [ms]
            times march multiplier [ms] ) divided by 1000 [ms->s]
        2. Define d=1 as the number of steps it is going to skip
        3. Loop over the next maxskips step and check whether t is also larger
            than any of them.
        4. Keep incrementing d each time you check.
        5. Once loop ends, check whether schedule end was reached
          - If it has, set self.step to 0 and self.t to 0.0
          - If not, increment self.step by d, calculate t_text, and call
            self.update()

        Un-optimized overhead:
        ~42 us of overhead for if
        ~11 us of overhead for else
        This includes 4 time() calls, and excludes the update() call
        """
        # t0 = time()  # [TIMING]

        # print(f"[DEBUG] t.= {round(self.t, 1)}/{round(self.datapool.get_schedule_duration(), 1)}", end=" ")
        # print(f"tnext.= {round(self.t_next, 1)}", end=" ")
        # print(f"step.= {self.step}/{self.datapool.get_schedule_steps()}", end=" ")
        if self.t >= self.t_next:
            for d in range(1, self.maxskips+1):
                if self.t >= self.datapool.schedule[2][
                    (self.step + d + 1) % self.datapool.get_schedule_steps()]:
                    pass
                else:
                    break

            # print(f"d. = {d}")

            # Check for end-of-schedule
            # TODO Using -2 instead of -1 to fix a bug that prevents the if
            # TODO from triggering for high playback speeds.
            # TODO This is a stupid fix and introduces other bugs (schedules
            # TODO of length 1!), but for now it works
            # if self.step + d >= self.datapool.get_schedule_steps()-1:
            if self.step + d >= self.datapool.get_schedule_steps()-2:
                # print("[DEBUG] END OF SCHEDULE")
                self.t = 0.0
                self.step = 0
            else:
                self.t = (self.t + self.march_mult * self.march_interval / 1000) \
                         % self.datapool.get_schedule_duration()
                self.step += d

            # t1 = time()  # [TIMING]
            self.update()
            # t2 = time()  # [TIMING]

            self.t_next = self.datapool.schedule[2][
                (self.step + 1) % self.datapool.get_schedule_steps()]

        else:
            # t1 = time()  # [TIMING]
            # t2 = time()  # [TIMING]
            self.t = (self.t + self.march_mult*self.march_interval/1000)
            # print(f"")

        # print("Time: ", round((time()-t0 - (t2-t1))*1E6), "us")  # [TIMING]

    def update(self):
        """Method to overload."""
        pass


class SchedulePlayerCyclics(SchedulePlayer):
    def __init__(self, hhcplot_xy, hhcplot_yz, widget_cyclicsplot, bscale,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # External variables: self.datapool.get_schedule_steps()
        self.hhcplot_xy = hhcplot_xy
        self.hhcplot_yz = hhcplot_yz
        self.widget_cyclicsplot = widget_cyclicsplot
        self.bscale = bscale

    def update(self):
        # t0 = time()  # [TIMING] ~4 us
        bx = self.datapool.schedule[3][self.step]
        by = self.datapool.schedule[4][self.step]
        bz = self.datapool.schedule[5][self.step]

        tail_clip = 0.9

        # t1 = time()  # [TIMING] 32 us
        self.hhcplot_xy.arrow_tail.setLine(
            0., 0., tail_clip * by / self.bscale, -tail_clip * bx / self.bscale
        )
        # t2 = time()  # [TIMING] 11 us
        self.hhcplot_xy.arrow_tip.setPos(by / self.bscale, -bx / self.bscale)
        # t3 = time()  # [TIMING] ~300 us
        self.hhcplot_xy.arrow_tip.setStyle(
            angle=self.hhcplot_xy.arrow_tail.line().angle() - 180
        )

        # t4 = time()  # [TIMING]
        self.hhcplot_yz.arrow_tail.setLine(
            0., 0., tail_clip * by / self.bscale, tail_clip * bz / self.bscale)
        self.hhcplot_yz.arrow_tip.setPos(by / self.bscale, bz / self.bscale)
        self.hhcplot_yz.arrow_tip.setStyle(
            angle=self.hhcplot_yz.arrow_tail.line().angle() - 180
        )

        # t5 = time()  # [TIMING] ~210 us

        self.widget_cyclicsplot.vline.setPos(self.t)

        # t6 = time()  # [TIMING] total ~700 us

        # print(f"[TIMING]", end=" ")
        # print(f"{round((t1-t0)*1E6)} us", end=" ")
        # print(f"{round((t2-t1)*1E6)} us", end=" ")
        # print(f"{round((t3-t2)*1E6)} us", end=" ")
        # print(f"{round((t4-t3)*1E6)} us", end=" ")
        # print(f"{round((t5-t4)*1E6)} us", end=" ")
        # print(f"{round((t6-t5)*1E6)} us", end=" ")
        # print(f"T: {round((t6-t0)*1E6)} us")


# TODO: In main group, put play controls in a class instance
# TODO Instantiate once
# TODO Then connect this object to both looper functions and play controls
class PlayerControls(QGroupBox):
    def __init__(self, datapool, scheduleplayer, label_update_interval=25) -> None:
        super().__init__()

        self.datapool = datapool
        self.scheduleplayer = scheduleplayer

        self.label_update_interval = label_update_interval
        self.label_update_timer = QTimer()
        self.label_update_timer.timeout.connect(self.update_labels)

        self.str_step_prev = 0
        self.str_duration = "/"+str(round(self.datapool.get_schedule_duration(), 3))
        self.str_steps = "/"+str(self.datapool.get_schedule_steps())

        layout0 = QHBoxLayout()

        self.button_play = QPushButton()
        self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))
        self.button_play.toggled.connect(self.toggle_play)
        self.button_play.setCheckable(True)

        self.button_reset = QPushButton()
        self.button_reset.setIcon(QIcon("./assets/icons/feather/rotate-ccw.svg"))
        self.button_reset.clicked.connect(self.toggle_reset)

        self.button_mult10 = QPushButton()
        self.button_mult10.setIcon(QIcon("./assets/icons/x10.svg"))
        self.button_mult10.toggled.connect(self.toggle_mult10)
        self.button_mult10.setCheckable(True)

        self.button_mult100 = QPushButton()
        self.button_mult100.setIcon(QIcon("./assets/icons/x100.svg"))
        self.button_mult100.toggled.connect(self.toggle_mult100)
        self.button_mult100.setCheckable(True)

        self.button_mult1000 = QPushButton()
        self.button_mult1000.setIcon(QIcon("./assets/icons/x1000.svg"))
        self.button_mult1000.toggled.connect(self.toggle_mult1000)
        self.button_mult1000.setCheckable(True)

        self.buttons_playback = (
            self.button_play,
            self.button_reset,
        )
        self.buttons_mult = (
            self.button_mult10,
            self.button_mult100,
            self.button_mult1000,
        )

        for button in self.buttons_playback+self.buttons_mult:
            layout0.addWidget(button)

        # Labels
        self.label_t_text = QLabel("Time: ")
        self.label_t = QLabel(str(0.0))
        self.label_t_unit = QLabel("s")

        self.label_step_text = QLabel("Step: ")
        self.label_step = QLabel(str("0/0"))

        self.update_labels()

        layout_labels = QGridLayout()
        for i, l in enumerate((self.label_t_text, self.label_t, self.label_t_unit)):
            layout_labels.addWidget(l, 0, i)
        for i, l in enumerate((self.label_step_text, self.label_step,)):
            layout_labels.addWidget(l, 1, i)
        layout0.addLayout(layout_labels)

        self.setLayout(layout0)

    def uncheck_buttons(self, buttons_group):
        for button in buttons_group:
            button.setChecked(False)

    def toggle_play(self):
        button = self.button_play
        # print(f"toggle_play() -> checked: {button.isChecked()}")
        if button.isChecked():
            button.setIcon(QIcon("./assets/icons/feather/pause.svg"))
            # print("DO PLAY")
            self.scheduleplayer.start()
            self.label_update_timer.start(self.label_update_interval)

            # self.timer1.start(self.march_interval)
        else:
            button.setIcon(QIcon("./assets/icons/feather/play.svg"))
            # print("DO PAUSE")
            self.scheduleplayer.stop()
            self.label_update_timer.stop()

    def toggle_reset(self):
        # print("DO RESET")
        self.scheduleplayer.reset()


    def set_mult(self, mult):
        # print(f"set_mult({mult})")
        self.scheduleplayer.set_march_mult(mult)

    def toggle_mult10(self):
        # print(f"toggle_mult10() -> checked: {self.button_mult10.isChecked()}")
        if self.button_mult10.isChecked():
            self.button_mult100.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(mult=10)
        else:
            self.set_mult(mult=1)


    def toggle_mult100(self):
        # print(f"toggle_mult100() -> checked: {self.button_mult100.isChecked()}")
        if self.button_mult100.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(mult=100)
        else:
            self.set_mult(mult=1)


    def toggle_mult1000(self):
        # print(f"toggle_mult1000() -> checked: {self.button_mult1000.isChecked()}")
        if self.button_mult1000.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult100.setChecked(False)
            self.set_mult(mult=1000)
        else:
            self.set_mult(mult=1)

    def update_labels(self):
        """ Updates the time and step label.

        Optimizations:
         - Pre-generate the string with total steps and duration, so they do
            not have to be calculated in the loop.
         - Replace the only instance of round with a custom 3-digit round that
            has ~30 us less overhead.
         - Save ~10 us of overhead per cycle by not updating steps label when
            step was not updated internally.
        Total improvement from ~150 us to ~50 us
        """
        # t0 = time()  # [TIMING]
        label_t_str = str((self.scheduleplayer.t * 2001) // 2 / 1000) + self.str_duration
        # t1 = time())  # [TIMING]
        self.label_t.setText(label_t_str)

        # self.label_t.setText(
        #     str(round(self.scheduleplayer.t, 3))
        #     + "/"
        #     + str(round(self.datapool.get_schedule_duration(), 3))
        # )

        # t2 = time())  # [TIMING]

        if self.scheduleplayer.step != self.str_step_prev:
            self.label_step.setText(
                str(self.scheduleplayer.step) + self.str_steps
            )
            self.str_step_prev = self.scheduleplayer.step

        # self.label_step.setText(
        #     str(self.scheduleplayer.step)
        #     + "/"
        #     + str(self.datapool.get_schedule_steps())
        # )

        # print(f"[TIMING] update_labels(): {round((t1-t0)*1E6)} us  {round((t2-t1)*1E6)} us  {round((time()-t2)*1E6)} us")  # [TIMING]


class VisualizerCyclics(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Visualizations")
        self.datapool = datapool


        # windowsize = (self.data.config["plotwindow_windowsize"][0],
        #               self.data.config["plotwindow_windowsize"][1])
        # self.setMinimumSize(QSize(windowsize[0], windowsize[1]))
        # self.setMaximumSize(QSize(windowsize[0], windowsize[1]))
        windowsize = (760, 820)
        self.setMinimumSize(QSize(windowsize[0], windowsize[1]))
        self.setMaximumSize(QSize(windowsize[0], windowsize[1]))


        layout0 = QVBoxLayout()


        self.widget_cyclicsplot = CyclicsPlot(self.datapool)


        layout_hhcplot = QGridLayout()

        self.bscale = self.datapool.config["plotwindow_bscale"]  # TODO
        self.bscale = 100_000
        self.hhcplot_yz = HHCPlot(direction="YZ", bscale=self.bscale)
        self.hhcplot_mxy = HHCPlot(direction="mXY", bscale=self.bscale)
        self.plot_ghosts()

        layout_hhcplot.addWidget(QLabel("Front view (YZ)"), 0, 0)
        layout_hhcplot.addWidget(self.hhcplot_yz, 1, 0)

        layout_hhcplot.addWidget(QLabel("Top view (-XY)"), 0, 1)
        layout_hhcplot.addWidget(self.hhcplot_mxy, 1, 1)
        # layout0.addWidget(QLabel("Layout2dPlots"))


        self.scheduleplayer = SchedulePlayerCyclics(
            self.hhcplot_mxy, self.hhcplot_yz, self.widget_cyclicsplot,
            self.bscale, self.datapool)
        # self.march_interval: int = int(10)
        # self.t = 0.0
        # self.t_next = 0.0
        # self.timer1 = QTimer()
        # self.timer1.timeout.connect(self.march)
        self.mult = 1

        self.group_playcontrols = PlayerControls(
            self.datapool, self.scheduleplayer
        )

        layout0.addWidget(self.widget_cyclicsplot)
        layout0.addWidget(self.group_playcontrols)
        layout0.addLayout(layout_hhcplot)

        self.setLayout(layout0)

        # self.timer1.start(int(1000/self.data.config["plotwindow_updaterate"]))
        # self.timer1.start(self.march_interval)  # TODO


    def plot_ghosts(self):
        ghost_pen = pg.mkPen((0, 255, 255, 64), width=1, style=Qt.DotLine)
        # self.hhcplot_xy.plot_obj.plot(self.data.schedule[3]/self.bscale,  # X
        #                               self.data.schedule[4]/self.bscale,  # Y
        #                               pen=ghost_pen)

        self.hhcplot_mxy.plot_obj.plot(
            self.datapool.schedule[4]/self.bscale,      # X
            -self.datapool.schedule[3]/self.bscale,     # Y
            pen=ghost_pen
        )
        self.hhcplot_yz.plot_obj.plot(
            self.datapool.schedule[4]/self.bscale,          # Y
            self.datapool.schedule[5]/self.bscale,          # Z
            pen=ghost_pen
        )

    # def march(self):
    #     # print("[DEBUG] t =", self.t, "  t_next =", self.t_next)
    #     # self.group_playcontrols.ttext.setText(str(round(self.t, 3)))
    #
    #     if self.t >= self.t_next:
    #         # print(f"[DEBUG] Update step {self.data.schedule_istep}")
    #         self.update()
    #
    #         istep_next = (self.data.schedule_istep + 1) % len(self.data.schedule[0])
    #         self.t_next = self.data.schedule[2][istep_next]
    #         self.data.schedule_istep = istep_next
    #         self.t = (self.t + self.march_interval/1000) % self.data.schedule[2][-1]
    #
    #     else:
    #         self.t = (self.t + self.mult*self.march_interval/1000)




    # def update_bvector(self):
    #     bx, by, bz = self.data.schedule[self.data.schedule_istep][3:6]
    #     xy = np.array([bx, by])
    #     yz = np.array([by, bz])
    #     b = np.array([1, 0])
    #
    #     if by != 0:
    #         sign_y = by/np.abs(by)
    #     else:
    #         sign_y = 1
    #     angle_xy = sign_y * (180/np.pi*(np.arccos(np.dot(xy, b) / (np.linalg.norm(xy) * np.linalg.norm(b)))))
    #     abslen_xy = np.linalg.norm(xy)
    #
    #
    #     if bz != 0:
    #         sign_z = bz/np.abs(bz)
    #     else:
    #         sign_z = 1
    #     angle_yz = sign_z * (180/np.pi*(np.arccos(np.dot(yz, b) / (np.linalg.norm(yz) * np.linalg.norm(b)))))
    #     abslen_yz = np.linalg.norm(yz)
    #
    #     # plot_correction = 100*1.28
    #
    #     self.hhcplot_xy.arrow.setStyle(angle=-angle_xy+180, tailLen=self.hhcplot_xy.arrow_length(abslen_xy))
    #     self.hhcplot_xy.arrow.setPos(bx/self.bscale, by/self.bscale)
    #
    #     self.hhcplot_yz.arrow.setStyle(angle=-angle_yz+180, tailLen=self.hhcplot_yz.arrow_length(abslen_yz))
    #     self.hhcplot_yz.arrow.setPos(by/self.bscale, bz/self.bscale)

# ============================================================================



app = pg.mkQApp("Plotting Example")
pg.setConfigOptions(antialias=True)
datapool = DataPool(config)


filename = "myschedule2.bsch"
t, B, _, _, _ = read_bsch_file(filename)
#
# npts = 4
# t = np.linspace(0, npts-1, npts)*2
# B = np.array([[1, 1, -1, -1], [1, -1, -1, 1], [0, 0, 0, 0]])


n = len(t)
# t = np.linspace(0, n-1, n, dtype=int)




schedule = [np.linspace(0, n-1, n, dtype=int), np.ones(n), t, B[0], B[1], B[2]]

datapool.schedule = schedule





win = VisualizerCyclics(datapool)
win.show()








if __name__ == '__main__':
    pg.exec()