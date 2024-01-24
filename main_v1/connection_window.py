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

import codec.scc2q as scc
from client_functions import *
from config import config


class ConnectionWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool

        # Load relevant parameters from config file
        self.server_address = config["server_address"]
        self.server_port = config["server_port"]
        # self.codec = SCC()
        # print(self.codec)
        # self.buffer_size = self.codec.packet_size()
        # print(f"CONFIGURED BUFFER: {self.buffer_size}")
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

        self.timer_get_bm = QTimer()
        self.timer_get_bm.timeout.connect(self.do_get_Bm)
        self.timer_get_bm_ms = 50

        self.timer_ping = QTimer()
        self.timer_ping.timeout.connect(self.do_ping)
        self.timer_ping_ms = 1000

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
        # print("Signal: read_socket()")
        pass

    def on_connected(self):
        print("Signal: connected()")
        for widget in self.widgets_to_enable:
            widget.setEnabled(True)
        self.timer_get_bm.start(self.timer_get_bm_ms)
        self.timer_ping.start(self.timer_ping_ms)


    def on_disconnected(self):
        print("Signal: disconnected()")
        self.timer_get_bm.stop()
        self.timer_ping.stop()

        for widget in self.widgets_to_enable:
            widget.setEnabled(False)

    # @staticmethod
    # def decode_epacket(e_packet):  # Q Compatible
    #     """ Encodes an e_packet, which has the following anatomy:
    #     e (1 B)    msg (n B)
    #     """
    #     # return e_packet.decode()[1:].rstrip(SCC.padding)
    #     print(f"[DEBUG] decode_epacket({e_packet})")
    #     e_packet_decoded = e_packet.decode()
    #     print(f"[DEBUG] decode_epacket(): e_packet_decoded {e_packet_decoded}")
    #     print(f"[DEBUG] decode_epacket(): e_packet.decode() {e_packet.decode()}")
    #     e_packet_parsed = e_packet_decoded[1:e_packet_decoded.find('#')]
    #     print(f"[DEBUG] decode_epacket(): e_packet_parsed {e_packet_parsed}")
    #     print(f"[DEBUG] decode_epacket(): i_find: {e_packet_decoded.find('#')}")
    #     print(f"[DEBUG] decode_epacket(): e_packet.parsed {e_packet_decoded[1:e_packet_decoded.find('#')]}")
    #     # return e_packet_decoded[1:e_packet_decoded.find('#')]
    #     return e_packet_parsed


    def do_ping(self):  # TODO ECHO
        t0 = time()
        socket_stream = QDataStream(self.socket)
        packet_out = scc.encode_epacket("")

        socket_stream.writeRawData(packet_out)

        if self.socket.waitForReadyRead(100):
            if scc.decode_epacket(socket_stream.readRawData(scc.packet_size)) == "":
                t = time()-t0
                self.label_ping.setText(f"ping(): {int(t * 1E6)} \u03bcs")
            else:
                print("ping() failed (-1)!")
                self.label_ping.setText("ping(): -1")

    # def do_ping(self):  # TODO ECHO
    #     t0 = time()
    #     socket_stream = QDataStream(self.socket)
    #     packet_out = scc.encode_epacket("")
    #
    #     socket_stream.writeRawData(packet_out)
    #
    #     if self.socket.waitForReadyRead(100):
    #         inc = socket_stream.readRawData(scc.packet_size)
    #         print(inc)
    #         e_packet_decoded = scc.decode_epacket(inc)
    #         print(f"decode: `{e_packet_decoded}`")
    #         if e_packet_decoded == "":
    #             t = time()-t0
    #             self.label_ping.setText(f"ping(): {int(t * 1E6)} \u03bcs")
    #         else:
    #             print("ping() failed (-1)!")
    #             self.label_ping.setText("ping(): -1")


    def do_get_Bm(self):
        t0 = time()
        socket_stream = QDataStream(self.socket)
        packet_out = scc.encode_bpacket([0.] * 4)
        # print(packet_out)
        socket_stream.writeRawData(packet_out)

        if self.socket.waitForReadyRead(100):
            inc = socket_stream.readRawData(scc.packet_size)
            r = scc.decode_bpacket(inc)

            bx, by, bz = round(r[1]*1E-3, 3), round(r[2]*1E-3, 3), round(r[3]*1E-3, 3)
            tt = time()-t0
            self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT  ({int(tt*1E6)} \u03bcs)")

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
    


