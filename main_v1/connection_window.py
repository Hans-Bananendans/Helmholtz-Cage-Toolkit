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
from PyQt5.QtNetwork import QTcpSocket, QHostAddress, QAbstractSocket

import os
import time
import pyqtgraph as pg
import numpy as np
import socket
import sys
from time import sleep, time
from threading import Thread

from codec.scc2 import SCC
from client_functions import *
from config import config


class ConnectionWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool

        # Load relevant parameters from config file
        self.server_address = config["server_address"]
        self.server_port = config["server_port"]
        self.buffer_size = config["buffer_size"]
        self.connect_on_startup = config["connect_on_startup"]

        self.socket = QTcpSocket(self)
        # self.socket.readyRead.connect(self.read_socket)
        self.socket.disconnected.connect(self.print_disconnected)
        # self.socket.errorOccurred.connect(self.display_error)

        layout0 = QGridLayout()

        self.datapool.status_bar.showMessage("Disconnected")

        # label_connection = QLabel("Connection status:")
        # self.label_connection_status = QLabel("DISCONNECTED")

        # self.packet_counter = 0

        # layout0.addWidget(label_connection, 1, 1)
        # layout0.addWidget(self.label_connection_status, 1, 2)


        connect_button = QPushButton("CONNECT")
        connect_button.clicked.connect(self.connect_socket)

        disconnect_button = QPushButton("DISCONNECT")
        disconnect_button.clicked.connect(self.disconnect_socket)

        layout0.addWidget(connect_button, 1, 1)
        layout0.addWidget(disconnect_button, 2, 1)

        self.setLayout(layout0)

    def connect_socket(self):
        self.socket.connectToHost(self.server_address, self.server_port)

        # Try to connect for 3 s before giving up
        if self.socket.waitForConnected(3000):
            self.datapool.status_bar.showMessage(
                f"Connected to server at {self.server_address}:{self.server_port}"
            )
        else:
            print(f"Error in connect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                self.socket.close()

    def disconnect_socket(self):
        self.socket.disconnectFromHost()

        # Try to connect for 3 s before giving up
        if self.socket.state() == QAbstractSocket.UnconnectedState or \
                socket.waitForDisconnected(3000):
            self.datapool.status_bar.showMessage("Disconnected")
        else:
            print(f"Error in disconnect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                self.socket.close()

    def print_disconnected(self):
        print("Signal: disconnected()")

    # def status_show(self, message: str):
    #     self.datapool.status_bar.showMessage(message)

    # def ping(self):
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #
    #         try:
    #             s.connect((self.server_address, self.server_port))
    #             print(f"Connection to {self.server_address}:{self.server_port} established.")
    #             print(f"Accessing from {s.getsockname()[0]}:{s.getsockname()[1]}.")
    #         except:  # noqa
    #             print("Connection failed!")
    #
    #
    #         # self.loop = True
    #         #
    #         # def break_loop():
    #         #     self.loop = False
    #         #
    #         # timer_breakloop = QTimer()
    #         # timer_breakloop.timeout.connect(break_loop)
    #
    #         sleep(0.1)
    #
    #         print(message(s, "Hello server!"))
    #         print(echo(s, "Echo!"))
    #
    #         sleep(0.1)
    #
    #
    #         # while self.loop:
    #         #     pass
    #
    #
    #
    #
    #
    #         # Shutting down connection from client side
    #         print("Terminating...")
    #         # s.shutdown(1)
    #         s.close()
    #         print("Connection terminated.")


    # def log(self, verbosity_level, string):
    #     """Prints string to console when verbosity is above a certain level"""
    #     if verbosity_level <= self.data.config["verbosity"]:
    #         print(string)
    


