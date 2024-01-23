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

# TODO: Generalize imports!



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
    return "!BSCH\n{}\n{}\n{}\n{}\n\n\n\n\n{}\n".format(
        filename,
        "generator={}".format(generator),
        str(generation_parameters),
        str(interpolation_parameters),
        "#" * 32
    )


class GenParamDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Generation Parameters")

        text1 = "The B-schedule file can store the\n"
        text2 = "generation parameters of the\n"
        text3 = "schedule, but only one set can be\n"
        text4 = "included.\n \n"
        text5 = "Which generation parameters would\nyou like to include?"

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
        print("[DEBUG] Chose 'Cyclics'!")
        self.done(0)

    def choose_orbital(self):
        print("[DEBUG] Chose 'Orbital'!")
        self.done(1)

    def choose_none(self):
        print("[DEBUG] Chose 'None'!")
        self.done(2)


class NewFileDialog(QMessageBox):
    def __init__(self):
        super().__init__()

        self.setIcon(QMessageBox.Question)
        self.setText("Start with an empty file?")
        self.setWindowTitle("Start new file")
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    def run(self):
        returnValue = self.exec()

        if returnValue == QMessageBox.Ok:
            return 1
        else:
            return 0

def load_filedialog(parent=None):
    out = QFileDialog.getOpenFileName(
        parent=parent,
        caption="Select a B-schedule file",
        directory=os.getcwd(),
        filter="B-schedule file (*.bsch);; All files (*.*)",
        initialFilter="B-schedule file (*.bsch)"
    )
    print(out)
    return out[0]


def save_filedialog(parent=None, generator="none"):
    out = QFileDialog.getSaveFileName(
        parent=parent,
        caption=f"Select a B-schedule file (genparams: {generator})",
        directory=os.getcwd(),
        filter="B-schedule file (*.bsch);; All files (*.*)",
        initialFilter="B-schedule file (*.bsch)"
    )
    print(out)
    return out[0]

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


def save_file(datapool):
    dialog = GenParamDialog()

    if dialog.result() == 0:
        generator = "cyclics"
        generation_parameters = datapool.generation_parameters_cyclics
    elif dialog.result() == 1:
        generator = "orbital"
        generation_parameters = datapool.generation_parameters_orbital
    else:
        generator = "none"
        generation_parameters = {}

    filename = save_filedialog(generator=generator)

    t0 = time()

    # Initialize file
    header_string = generate_header(
        filename,
        generator,
        generation_parameters,
        datapool.interpolation_parameters
    )

    initialize_bsch_file(filename, header_string, overwrite=True)

    write_bsch_file(filename, generate_schedule_segments(datapool))

    datapool.set_window_title(suffix=filename)

    print(f"File '{filename}' saved succesfully!")
    print(f"[DEBUG] Saved file in {int((time() - t0) * 1000)} ms")



def load_file(datapool):
    filename = load_filedialog()

    t0 = time()
    if filename == "":
        print(f"No file selected!")
        return

    try:
        t, B, schedule_name, generator, generation_parameters, interpolation_parameters \
            = read_bsch_file(filename)
    except FileNotFoundError:
        print(f"File '{filename}' not found!")
        return
    # except:  # noqa
    #     print(f"Something went wrong opening '{filename}'!")
    #     return

    datapool.schedule_name = schedule_name
    datapool.generator = generator
    if generator == "cyclics":
        datapool.generation_parameters_cyclics = generation_parameters
    elif generator == "orbital":
        datapool.generation_parameters_orbital = generation_parameters
    datapool.interpolation_parameters = interpolation_parameters
    datapool.schedule = make_schedule(t, B)

    datapool.set_window_title(suffix=filename)

    print(f"[DEBUG] Loaded file in {int((time() - t0) * 1000)} ms")
    # print(f": {}")

    # self.timer1.start(int(1000/self.data.config["plotwindow_updaterate"]))
    # self.timer1.start(self.march_interval)  # TODO



def make_schedule(t, B):
    n = len(t)
    return array((
        linspace(0, n-1, n, dtype=int),
        ones(n)*n,
        t,
        B[0],
        B[1],
        B[2]
    ))