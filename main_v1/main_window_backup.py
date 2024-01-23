from PyQt5.QtCore import QDir, QSize, Qt
from PyQt5.QtGui import (
    QFont,
    QIcon,
    QImage,
    QKeySequence,
    QPixmap,
    QPalette,
    QColor,
)
from PyQt5.QtWidgets import (
    QGraphicsView,
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
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg
import numpy as np

from control_window import ControlWindow

# # TODO: REMOVE
# class Color(QWidget):
#
#     def __init__(self, color):
#         super(Color, self).__init__()
#         self.setAutoFillBackground(True)
#
#         palette = self.palette()
#         palette.setColor(QPalette.Window, QColor(color))
#         self.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self, config) -> None:
        super().__init__()


        self.main_window = QMainWindow()

        self.resize(config["default_windowsize"][0], 
                    config["default_windowsize"][1])  # Default w x h dimensions
        self.setWindowTitle("Test window")

        widget = ControlWindow(config)
        self.setCentralWidget(widget)
