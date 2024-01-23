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

from datapool import DataPool

import os
import time
import pyqtgraph as pg
import numpy as np

from orbit_visualizer import OrbitVisualizer

class OrbitDesignWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        # TODO REPLACE WITH GENERIC DATAPOOL
        self.data = DataPool(self, config)  # Generic datapool object data

        layout0 = QHBoxLayout()
        

        # self.data.log(4, "ControlWindow - Setting up hardware...")

    
        # Generate groups
        # Note: these subwindows access config indirectly through the datapool
        group_orbit_control = GroupOrbitControl(self.data)
        # group_orbit_visualizer = OrbitVisualizer(self.data)


        layout0.addWidget(group_orbit_control)
        layout0.addWidget(OrbitVisualizer(self.data))
        self.setLayout(layout0)
    

    # def log(self, verbosity_level, string):
    #     """Prints string to console when verbosity is above a certain level"""
    #     if verbosity_level <= self.data.config["verbosity"]:
    #         print(string)
    



class GroupOrbitControl(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Orbit Controls")

        # self.setMinimumSize(QSize(480, 360))
        self.setMaximumWidth(200)  # TODO: Properly address this
        
        self.data = datapool

        layout0 = QGridLayout()

        layout0.addWidget(QLabel("This is Orbit Control"), 0, 0)

        self.setLayout(layout0)



    # @Slot()
    def submit(self):
        pass
        # axis = ("X", "Y", "Z")
        # for i in range(3):
        #     self.data.B_c[i] = float(self.input_b[i].text())
        #     self.data.I_c[i] = TF_B_Ic(self.data.B_c[i], axis=axis[i])
        #     self.data.V_cc[i] = TF_Ic_Vc(self.data.I_c[i])
        #
        # self.data.log(4, "B_c:  {self.data.B_c}")
        # self.data.log(4, "I_c:  {self.data.I_c}")
        # self.data.log(4, "V_cc: {self.data.V_cc}")
        #
        # self.data.supplies[0].set_current_out(self.data.I_c[0])
        #
        # self.redraw_values()
    



