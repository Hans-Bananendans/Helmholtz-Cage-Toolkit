import numpy as np
from numpy import (
    pi,
    array, ndarray,
    sin, cos, arccos,
    dot, zeros, ones, eye, linspace, vstack, column_stack,
    empty, repeat,
)
import os
import threading
import matplotlib.pyplot as plt
from time import time, sleep

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
    QAbstractButton,
    QAction,
    QActionGroup,
    QDialog,
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
    QMessageBox,
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
    # TODO  Should headerless files be supported? Seems like a lot of hassle
    # TODO  for little gain.
    #
    header_length = 10
    with open(filename, 'r') as bsch_file:
        flag = (bsch_file.readline()).strip("\n")
        schedule_name = (bsch_file.readline()).strip("\n")
        generator = bsch_file.readline().strip("\n").split("=")[-1]
        generation_parameters = literal_eval(bsch_file.readline())
        interpolation_parameters = literal_eval(bsch_file.readline())
        for i in range(4):
            bsch_file.readline()
        end_of_header = (bsch_file.readline()).strip("\n")

        # for i, item in enumerate((flag, schedule_name, generator, generation_parameters, end_of_header)):
        #     print(i, ":", item, type(item))

        # Checks
        if flag != "!BSCH":
            raise AssertionError(f"While loading '{filename}', header flag !BSCH not found. Are you sure it is a valid .bsch file?")

        if end_of_header != "#"*32:
            raise AssertionError(f"While loading '{filename}', could not find end of header. Are you sure it is a valid .bsch file?")

        recognised_generators = ("cyclics", "orbital", "none")
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

    return t, B, schedule_name, generator, generation_parameters, interpolation_parameters




def write_bsch_file(filename, schedule):

    # if generator == "cyclics":
    #     genparams = self.datapool.generation_parameters_cyclics
    #     header = generate_header(filename, generator, genparams)

    with open(filename, 'a') as output_file:
        for segment in schedule:
            output_file.write(",".join(str(val) for val in segment))
            output_file.write("\n")
    output_file.close()
    return 0


def initialize_bsch_file(filename, header, overwrite=False):
    # Test if file already exists
    try:
        with open(filename, 'x') as output_file:
            pass
    except FileExistsError:
        if overwrite is False:
            print("File already exists! Creation cancelled")
            return -1
        else:
            pass
    with open(filename, 'w') as output_file:
        output_file.write(header)
    output_file.close()
    return 0


def generate_header(filename, generator,
                    generation_parameters,
                    interpolation_parameters):
    filename_with_ext = filename.split(os.sep)[-1]
    filename = filename_with_ext.strip("." + filename_with_ext.split(".")[-1])
    print(f"filename with ext: {filename_with_ext}")
    print(f"filename: {filename}")
    return "!BSCH\n{}\n{}\n{}\n{}\n\n\n\n\n{}\n".format(
        filename,
        "generator={}".format(generator),
        str(generation_parameters),
        str(interpolation_parameters),
        "#" * 32
    )

def makeschedule(t, B):
    n = len(t)
    return array((
        linspace(0, n-1, n, dtype=int),
        ones(n)*n,
        t,
        B[0],
        B[1],
        B[2]
    ))


class GenParamDialog(QDialog):
    def __init__(self, datapool):
        super().__init__()

        self.setWindowTitle("Generation Parameters")

        # self.setFixedSize(128, 256)

        text1 = "The B-schedule file can store the\n"
        text2 = "generation parameters of the\n"
        text3 = "schedule, but only one set can be\n"
        text4 = "included.\n \n"
        text5 = "Which parameters would you like\nto include?"

        button_cyclics = QPushButton("Cyclics")
        button_cyclics.clicked.connect(self.choose_cyclics)

        button_orbital = QPushButton("Orbital")
        button_orbital.clicked.connect(self.choose_orbital)

        button_none = QPushButton("None")
        button_none.clicked.connect(self.choose_none)

        layout0 = QVBoxLayout()
        layout0.addWidget(QLabel(text1+text2+text3+text4+text5))
        layout0.addWidget(button_cyclics)
        layout0.addWidget(button_orbital)
        layout0.addWidget(button_none)

        self.setLayout(layout0)

        self.exec()

    def choose_cyclics(self):
        print("Chose 'Cyclics'!")
        self.done(0)

    def choose_orbital(self):
        print("Chose 'Orbital'!")
        self.done(1)

    def choose_none(self):
        print("Chose 'None'!")
        self.done(2)


def generate_schedule_segments(datapool):
    n = datapool.get_schedule_steps()
    schedule = [[0, 0, 0., 0., 0., 0.], ]*n
    for i in range(n):
        schedule[i] = [i,
                       n,
                       round(datapool.schedule[2][i], 6),
                       round(datapool.schedule[3][i], 3),
                       round(datapool.schedule[4][i], 3),
                       round(datapool.schedule[5][i], 3),
                       ]
    return schedule



def load_filedialog(parent):
    # file_filter = 'B-schedule file (*.bsch);; All files (*.*)'
    out = QFileDialog.getOpenFileName(
        parent=parent,
        caption="Select a B-schedule file",
        directory=os.getcwd(),
        filter="B-schedule file (*.bsch);; All files (*.*)",
        initialFilter="B-schedule file (*.bsch)"
    )
    print(out)
    return out[0]


def save_filedialog(parent, generator="None"):
    out = QFileDialog.getSaveFileName(
        parent=parent,
        caption=f"Select a B-schedule file (genparams: {generator})",
        directory=os.getcwd(),
        filter="B-schedule file (*.bsch);; All files (*.*)",
        initialFilter="B-schedule file (*.bsch)"
    )
    print(out)
    return out[0]


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
        self.schedule_name = ""
        self.generator = "None"
        self.generation_parameters_cyclics = {}
        self.generation_parameters_orbital = {}
        self.interpolation_parameters = {}


    def get_schedule_duration(self):
        return self.schedule[2][-1]

    def get_schedule_steps(self):
        return len(self.schedule[0])


class DummyGroupbox(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__()
        self.datapool = datapool

        self.window_title_base = "Window Title"  # TODO DUMMY
        self.software_version = "0.0.1"  # TODO Dummy
        self.set_window_title()

        windowsize = (384, 96)
        self.setMinimumSize(QSize(windowsize[0], windowsize[1]))

        layout0 = QVBoxLayout()


        self.button_load = QPushButton("Load...")
        self.button_load.clicked.connect(self.load_file)

        self.button_save = QPushButton("Save as...")
        self.button_save.clicked.connect(self.save_file)

        self.button_print = QPushButton("Print stuff!")
        self.button_print.clicked.connect(self.print_stuff)

        layout0.addWidget(self.button_load)
        layout0.addWidget(self.button_save)
        layout0.addWidget(self.button_print)

        self.setLayout(layout0)

    def print_stuff(self):
        print(f"datapool.schedule_name: {self.datapool.schedule_name}")
        print(f"datapool.generator: {self.datapool.generator}")
        print(f"datapool.generation_parameters_cyclics: "
              f"{self.datapool.generation_parameters_cyclics}")
        print(f"datapool.generation_parameters_orbital: "
              f"{self.datapool.generation_parameters_orbital}")
        print(f"datapool.interpolation_parameters: "
              f"{self.datapool.interpolation_parameters}")
        print(f"datapool.schedule: {self.datapool.schedule}")


    def set_window_title(self, suffix: str = ""):
        if suffix != "":
            suffix = " - " + suffix.split(os.sep)[-1]
        self.setWindowTitle(
            self.window_title_base + " " + self.software_version + suffix
        )

    def save_file(self):
        dialog = GenParamDialog(self.datapool)

        if dialog.result() == 0:
            generator = "cyclics"
            generation_parameters = self.datapool.generation_parameters_cyclics
        elif dialog.result() == 1:
            generator = "orbital"
            generation_parameters = self.datapool.generation_parameters_orbital
        else:
            generator = "none"
            generation_parameters = {}

        filename = save_filedialog(self)

        # Initialize file
        header_string = generate_header(
            filename,
            generator,
            generation_parameters,
            self.datapool.interpolation_parameters
        )

        initialize_bsch_file(filename, header_string, overwrite=True)

        write_bsch_file(filename, generate_schedule_segments(self.datapool))

        print(f"File '{filename}' saved succesfully!")


    def load_file(self):
        filename = load_filedialog(self)

        try:
            t, B, schedule_name, generator, generation_parameters, interpolation_parameters \
                = read_bsch_file(filename)
        except FileNotFoundError:
            print(f"File '{filename}' not found!")
            return
        # except:  # noqa
        #     print(f"Something went wrong opening '{filename}'!")
        #     return

        self.datapool.schedule_name = schedule_name
        self.datapool.generator = generator
        if generator == "cyclics":
            self.datapool.generation_parameters_cyclics = generation_parameters
        elif generator == "orbital":
            self.datapool.generation_parameters_orbital = generation_parameters
        self.datapool.interpolation_parameters = interpolation_parameters
        self.datapool.schedule = makeschedule(t, B)

        self.set_window_title(suffix=filename)
        # print(f": {}")

        # self.timer1.start(int(1000/self.data.config["visualizer_updaterate"]))
        # self.timer1.start(self.march_interval)  # TODO




# ============================================================================



app = pg.mkQApp()
datapool = DataPool(config)

win = DummyGroupbox(datapool)
win.show()

# filename = "myschedule2.bsch"
# t, B, _, _, _ = read_bsch_file(filename)
#
# npts = 4
# t = np.linspace(0, npts-1, npts)*2
# B = np.array([[1, 1, -1, -1], [1, -1, -1, 1], [0, 0, 0, 0]])


# n = len(t)
# t = np.linspace(0, n-1, n, dtype=int)




# schedule = [np.linspace(0, n-1, n, dtype=int), np.ones(n), t, B[0], B[1], B[2]]
#
# datapool.schedule = schedule














if __name__ == '__main__':
    pg.exec()