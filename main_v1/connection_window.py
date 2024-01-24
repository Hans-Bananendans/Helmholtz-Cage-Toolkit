from PyQt5.QtCore import (
    QDataStream,
    QDir,
    QLineF,
    QRectF,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    QTimer,
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

from codec.scc2q import SCC
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
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.read_socket)
        # self.socket.errorOccurred.connect(self.display_error)

        layout0 = QGridLayout()

        self.datapool.status_bar.showMessage("Disconnected")


        button_connect = QPushButton("CONNECT")
        button_connect.clicked.connect(self.connect_socket)

        button_disconnect = QPushButton("DISCONNECT")
        button_disconnect.clicked.connect(self.disconnect_socket)



        button_ping = QPushButton("PING")
        button_ping.clicked.connect(self.do_ping)
        self.label_ping = QLabel()

        button_get_bm = QPushButton("Get Bm")
        button_get_bm.clicked.connect(self.do_get_Bm)
        self.label_get_bm = QLabel()


        # Disable widgets in widgets_to_enable group until connection is made
        self.widgets_to_enable = (
            button_ping,
            button_get_bm,
        )
        for widget in self.widgets_to_enable:
            widget.setEnabled(False)


        layout0.addWidget(button_connect, 1, 1)
        layout0.addWidget(button_disconnect, 2, 1)
        layout0.addWidget(button_ping, 3, 1)
        layout0.addWidget(self.label_ping, 3, 2)
        layout0.addWidget(button_get_bm, 4, 1)
        layout0.addWidget(self.label_get_bm, 4, 2)

        self.setLayout(layout0)




    def connect_socket(self):
        self.socket.connectToHost(self.server_address, self.server_port)

        # Try to connect for 3 s before giving up
        if self.socket.waitForConnected(3000):
            self.datapool.status_bar.showMessage(
                f"Connected to server at {self.server_address}:{self.server_port}"
            )
        else:
            self.datapool.status_bar.showMessage(
                f"Connection error: {self.socket.errorString()}"
            )

            print(f"Error in connect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                print("connect_socket(): socket closed manually")
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
                print("disconnect_socket(): socket closed manually")
                self.socket.close()

            self.datapool.status_bar.showMessage("Disconnected")

    def read_socket(self):
        print("Signal: read_socket()")

    def on_connected(self):
        print("Signal: connected()")
        for widget in self.widgets_to_enable:
            widget.setEnabled(True)

    def on_disconnected(self):
        print("Signal: disconnected()")
        for widget in self.widgets_to_enable:
            widget.setEnabled(False)


    def do_ping(self):  # TODO ECHO
        t0 = time()
        socket_stream = QDataStream(self.socket)
        packet_out = SCC.encode_epacket("")

        socket_stream.writeRawData(packet_out)

        if self.socket.waitForReadyRead(100):
            inc = socket_stream.readRawData(SCC.buffer_size)
            print(inc)
            print(f"decode: `{SCC.decode_epacket(inc)}`")
            if SCC.decode_epacket(inc) != "whatever":
                t = time()-t0
                self.label_ping.setText(f"ping(): {int(t * 1E6)} \u03bcs")
            else:
                print("ping() failed (-1)!")
                self.label_ping.setText("ping(): -1")


    def do_get_Bm(self):
        t0 = time()
        socket_stream = QDataStream(self.socket)
        packet_out = SCC.encode_bpacket([0.] * 4)
        print(packet_out)
        socket_stream.writeRawData(packet_out)

        if self.socket.waitForReadyRead(100):
            inc = socket_stream.readRawData(SCC.buffer_size)
            print(inc)
            r = SCC.decode_bpacket(inc)
            print(f"Time: {time()-t0}")
            print(r)
            bx, by, bz = round(r[1]*1E-3, 3), round(r[2]*1E-3, 3), round(r[3]*1E-3, 3)
            self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT")

        # r = get_Bm(self.socket) # Returns B_m
        # bx, by, bz = round(r[1]*1E3, 3), round(r[2]*1E3, 3), round(r[3]*1E3, 3)
        # self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT")

    # def do_ping(self):  # TODO ECHO
    #
    #     socket_stream = QDataStream(self.socket)
    #     packet_out = SCC.encode_epacket(str("Echo!"))
    #
    #     socket_stream.writeRawData(packet_out)
    #
    #     if self.socket.waitForReadyRead(100):
    #         r = socket_stream.readRawData(SCC.buffer_size)
    #         print(r)
    #         print(SCC.decode_epacket(r))


    # def do_ping(self):
    #     r = ping(self.socket)  # Returns ping response time in [s], or -1 if failure
    #     if r == -1:
    #         print("ping() failed (-1)!")
    #     else:
    #         self.label_ping.setText(f"ping(): {int(r*1E6)} \u03bcs")

    # def do_get_Bm(self):
    #     r = get_Bm(self.socket) # Returns B_m
    #     bx, by, bz = round(r[1]*1E3, 3), round(r[2]*1E3, 3), round(r[3]*1E3, 3)
    #     self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT")

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
    


