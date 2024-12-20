import os
import sys
import socket
from time import sleep, time

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
import helmholtz_cage_toolkit.scc.scc4 as codec
import helmholtz_cage_toolkit.client_functions as cf


# from helmholtz_cage_toolkit.datapool import DataPool
#
#
# class ConnectionWindowDummy(QGroupBox):
#     def __init__(self, config, datapool):
#         super().__init__()
#
#
#         self.datapool = datapool
#
#         # Load relevant parameters from config file
#         self.server_address = config["server_address"]
#         self.server_port = config["server_port"]
#
#         self.socket_uptime = 0.0
#         self.server_uptime = 0.0
#
#         self.socket = QTcpSocket(self)
#         self.socket.connected.connect(self.on_connected)
#         self.socket.disconnected.connect(self.on_disconnected)
#         self.socket.readyRead.connect(self.on_read_socket)
#         # self.socket.errorOccurred.connect(self.display_error)
#
#         # self.datapool.status_bar.showMessage("Disconnected")
#
#
#         # ==== CONNECTBOX
#         layout_connectbox1 = QHBoxLayout()
#
#         self.button_connect = QPushButton(
#             QIcon("./assets/icons/feather/phone-call.svg"), "CONNECT"
#         )
#         self.button_connect.clicked.connect(self.connect_socket)
#
#         self.button_disconnect = QPushButton(
#             QIcon("./assets/icons/feather/phone-off.svg"), "DISCONNECT")
#         self.button_disconnect.clicked.connect(self.disconnect_socket)
#
#         layout_connectbox1.addWidget(self.button_connect)
#         layout_connectbox1.addWidget(self.button_disconnect)
#
#         # layout_connectbox2 = QHBoxLayout()
#
#         # layout_connectbox2.addWidget(QLabel("Address:"))
#         #
#         # self.le_address = QLineEdit()
#         # self.le_address.setPlaceholderText("<server address>")
#         # self.le_address.setText(self.datapool.config["server_address"])
#         # layout_connectbox2.addWidget(self.le_address)
#         #
#         # layout_connectbox2.addWidget(QLabel("Port:"))
#         #
#         # self.le_port = QLineEdit()
#         # self.le_port.setPlaceholderText("<port>")
#         # self.le_port.setText(str(self.datapool.config["server_port"]))
#         # layout_connectbox2.addWidget(self.le_port)
#
#         layout_connectbox = QVBoxLayout()
#
#         layout_connectbox.addLayout(layout_connectbox1)
#         # layout_connectbox.addLayout(layout_connectbox2)
#
#         group_connectbox = QGroupBox()
#         group_connectbox.setStyleSheet(
#             self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         )
#         group_connectbox.setLayout(layout_connectbox)
#
#
#         # # ==== STATUS BOX
#         # layout_statusbox = QGridLayout()
#         #
#         #
#         # layout_statusbox.addWidget(QLabel("Status:"), 0, 0)
#         # self.label_status = QLabel("OFFLINE")
#         # self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")
#         # layout_statusbox.addWidget(self.label_status, 0, 1)
#         #
#         # layout_statusbox.addWidget(QLabel("Host:"), 1, 0)
#         # self.label_host = QLabel("<host>")
#         # layout_statusbox.addWidget(self.label_host, 1, 1)
#         #
#         # layout_statusbox.addWidget(QLabel("Client (you):"), 2, 0)
#         # self.label_client = QLabel("<client>")
#         # layout_statusbox.addWidget(self.label_client, 2, 1)
#         #
#         # layout_statusbox.addWidget(QLabel("Host uptime:"), 3, 0)
#         # self.label_host_uptime = QLabel(f"{int(self.server_uptime)} s")
#         # layout_statusbox.addWidget(self.label_host_uptime, 3, 1)
#         #
#         # layout_statusbox.addWidget(QLabel("Socket uptime:"), 4, 0)
#         # self.label_socket_uptime = QLabel(f"{int(self.socket_uptime)} s")
#         # layout_statusbox.addWidget(self.label_socket_uptime, 4, 1)
#         #
#         # layout_statusbox.addWidget(QLabel("Response time"), 5, 0)
#         # self.label_ping_avg = QLabel()
#         # layout_statusbox.addWidget(self.label_ping_avg, 5, 1)
#         # self.button_ping_avg = QPushButton("test")
#         # self.button_ping_avg.clicked.connect(self.do_ping_avg)
#         # layout_statusbox.addWidget(self.button_ping_avg, 5, 2)
#         #
#         #
#         # group_statusbox = QGroupBox()
#         # group_statusbox.setStyleSheet(
#         #     self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         # )
#         # group_statusbox.setLayout(layout_statusbox)
#
#
#         # # ==== HHC BOX
#         # layout_hhcbox = QGridLayout()
#         #
#         #
#         # layout_hhcbox.addWidget(QLabel("HHC mode:"), 0, 0)
#         # self.label_hhcmode = QLabel("")
#         # layout_statusbox.addWidget(self.label_hhcmode, 0, 1)
#         #
#         # layout_hhcbox.addWidget(QLabel("HHC status:"), 1, 0)
#         # self.label_hhcstatus = QLabel("")
#         # layout_statusbox.addWidget(self.label_hhcstatus, 1, 1)
#         #
#         # layout_hhcbox.addWidget(QLabel("Schedule name:"), 2, 0)
#         # self.label_schedule_name = QLabel("")
#         # layout_statusbox.addWidget(self.label_schedule_name, 2, 1)
#         #
#         # layout_hhcbox.addWidget(QLabel("Segments:"), 3, 0)
#         # self.label_schedule_length = QLabel("")
#         # layout_statusbox.addWidget(self.label_schedule_length, 3, 1)
#         #
#         # layout_hhcbox.addWidget(QLabel("Duration:"), 4, 0)
#         # self.label_schedule_duration = QLabel("")
#         # layout_statusbox.addWidget(self.label_schedule_duration, 4, 1)
#         #
#         #
#         # group_hhcbox = QGroupBox()
#         # group_hhcbox.setStyleSheet(
#         #     self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         # )
#         # group_hhcbox.setLayout(layout_hhcbox)
#
#
#         # # ==== TRANSFER BOX
#         # self.button_transfer_schedule = QPushButton(
#         #     QIcon("./assets/icons/feather/upload.svg"), "TRANSFER TO HHC"
#         # )
#         # self.button_transfer_schedule.clicked.connect(self.transfer_schedule)
#         # self.button_transfer_schedule.setMinimumWidth(320)
#         #
#         # self.button_clear_schedule = QPushButton(
#         #     QIcon("./assets/icons/feather/trash.svg"), "CLEAR"
#         # )
#         # self.button_clear_schedule.clicked.connect(self.clear_schedule)
#         #
#         #
#         # layout_transferbox = QHBoxLayout()
#         #
#         # layout_transferbox.addWidget(self.button_transfer_schedule)
#         # layout_transferbox.addWidget(self.button_clear_schedule)
#         #
#         # group_transferbox = QGroupBox()
#         # group_transferbox.setStyleSheet(
#         #     self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         # )
#         # group_transferbox.setLayout(layout_transferbox)
#
#
#
#         # ==== Widgets to enable/disable on connection
#
#         # # Disable widgets in widgets_to_enable group until connection is made
#         self.widgets_to_enable = (
#             self.button_disconnect,
#
#             # self.label_host,
#             # self.label_client,
#             # self.label_host_uptime,
#             # self.label_socket_uptime,
#             # self.label_ping_avg,
#             # self.button_ping_avg,
#             #
#             # self.label_hhcmode,
#             # self.label_hhcstatus,
#             # self.label_schedule_name,
#             # self.label_schedule_length,
#             # self.label_schedule_duration,
#             #
#             # self.button_transfer_schedule,
#             # self.button_clear_schedule,
#         )
#
#
#         # ==== MAIN LAYERS
#
#         for widget in self.widgets_to_enable:
#             widget.setEnabled(False)
#
#
#
#         layout1 = QVBoxLayout()
#         layout1.addWidget(group_connectbox)
#         # layout1.addWidget(group_statusbox)
#         # layout1.addWidget(group_hhcbox)
#         # layout1.addWidget(group_transferbox)
#
#
#         group1 = QGroupBox()
#         group1.setMaximumWidth(500)
#         group1.setAlignment(Qt.AlignLeft)
#         group1.setStyleSheet(
#             self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
#         )
#
#         group1.setLayout(layout1)
#
#         layout0 = QHBoxLayout()
#
#         layout0.addWidget(group1)
#         layout0.addWidget(QWidget())
#
#         self.setLayout(layout0)
#
#
#         # ==== TIMERS
#         # if self.datapool.config["connect_on_startup"]:
#         #     self.timer_connect_on_startup = Qtimer()
#         #     self.timer_connect_on_startup.timeout.connect(
#         #         self.connect_on_startup
#         #     )
#         #     self.timer_connect_on_startup.start(
#         #         self.datapool.config["connect_on_startup_delay"]
#         #     )
#
#         # self.timer_update_time_labels = QTimer()
#         # self.timer_update_time_labels.timeout.connect(self.update_time_labels)
#         #
#         # self.timer_correct_time = QTimer()
#         # self.timer_correct_time.timeout.connect(self.correct_time)
#         #
#         # self.timer_update_general_labels = QTimer()
#         # self.timer_update_general_labels.timeout.connect(
#         #     self.update_general_labels)
#
#
#         # Since all TCP communication is implemented using blocking, only
#         # one request should ever be active at a time. As a result, a single
#         # QDataStream instance should suffice.
#
#         self.ds = QDataStream(self.socket)
#
#
#
#     def connect_socket(self, timeout=3000):
#         self.socket.connectToHost(self.server_address, self.server_port)
#
#
#         # Try to connect for `timeout` ms before giving up
#         if self.socket.waitForConnected(timeout):
#             print(f"Connected to server at {self.server_address}:{self.server_port}")
#         else:
#             print(f"Connection error: {self.socket.errorString()}")
#
#
#             print(f"Error in connect_socket(): {self.socket.errorString()}")
#             if self.socket.isOpen():
#                 print("connect_socket(): socket closed manually")
#                 self.socket.close()
#
#
#     def disconnect_socket(self, timeout=3000):
#         self.socket.disconnectFromHost()
#
#         # Try to connect for `timeout` ms before giving up
#         if self.socket.state() == QAbstractSocket.UnconnectedState or \
#                 socket.waitForDisconnected(timeout):
#             print("Disconnected (if)")
#         else:
#             print(f"Error in disconnect_socket(): {self.socket.errorString()}")
#             if self.socket.isOpen():
#                 print("disconnect_socket(): socket closed manually")
#                 self.socket.close()
#
#             print("Disconnected (else)")
#
#
#     def on_read_socket(self):
#         print("Signal: read_socket()")
#
#
#     def on_connected(self):
#         print("Signal: connected()")
#         for widget in self.widgets_to_enable:
#             widget.setEnabled(True)
#         self.timer_get_bm.start(self.timer_get_bm_ms)
#         self.timer_ping.start(self.timer_ping_ms)
#
#
#     def on_disconnected(self):
#         print("Signal: disconnected()")
#         self.timer_get_bm.stop()
#         self.timer_ping.stop()
#
#         for widget in self.widgets_to_enable:
#             widget.setEnabled(False)
#
#
#
#
#     # def connect_on_startup(self):
#     #     """Slot for the one-off `timer_connect_on_startup`.
#     #
#     #     Stops the timer, and attempt to connect to host.
#     #     """
#     #     self.timer_connect_on_startup.stop()
#     #     self.connect_socket()
#
#
#     # def connect_socket(self, timeout=3000):
#     #     """Tries to make a connection between self.socket and the host. Will
#     #     handle failed attempts. Will update the status_bar.
#     #     """
#     #     # self.socket.connectToHost(self.server_address, self.server_port)
#     #     address = self.le_address.text()
#     #     host = int(self.le_port.text())
#     #
#     #     print(f"[DEBUG] Connecting to {address} {type(address)}, {host} {type(host)} ")
#     #
#     #     self.socket.connectToHost(address, host)
#     #     # self.socket.connectToHost("127.0.0.1", 7777)
#     #
#     #     # Try to connect for `timeout` ms before giving up
#     #     if self.socket.waitForConnected(timeout):
#     #         self.server_address = address
#     #         self.server_port = port
#     #         # self.datapool.status_bar.showMessage(
#     #         #     f"Connected to server at {address}:{host}"
#     #         # )
#     #         print(f"Connected to server at {address}:{host}")
#     #     else:
#     #         # self.datapool.status_bar.showMessage(
#     #         #     f"Connection error: {self.socket.errorString()}"
#     #         # )
#     #         print(f"Connection error: {self.socket.errorString()}")
#     #         print(f"Error in connect_socket(): {self.socket.errorString()}")
#     #         if self.socket.isOpen():
#     #             print("connect_socket(): socket closed manually")
#     #             self.socket.close()
#     #
#     # # @Slot()
#     # def disconnect_socket(self, timeout=3000):
#     #     self.socket.disconnectFromHost()
#     #
#     #     # Try to connect for `timeout` ms before giving up
#     #     if self.socket.state() == QAbstractSocket.UnconnectedState or \
#     #             socket.waitForDisconnected(timeout):
#     #         # self.datapool.status_bar.showMessage("Disconnected")
#     #         print("Disconnected (if)")
#     #     else:
#     #         print(f"Error in disconnect_socket(): {self.socket.errorString()}")
#     #         if self.socket.isOpen():
#     #             print("disconnect_socket(): socket closed manually")
#     #             self.socket.close()
#     #
#     #         print("Disconnected (else)")
#     #         # self.datapool.status_bar.showMessage("Disconnected")
#     #
#     #
#     # def on_read_socket(self):
#     #     print("Signal: read_socket()")
#     #     pass
#     #
#     #
#     # def on_connected(self):
#     #     print("Signal: connected()")
#     #     # Set connection status to connected.
#     #     self.label_status.setText("ONLINE")
#     #     self.label_status.setStyleSheet("""QLabel {color: #00aa00;}""")
#     #
#     #     for widget in self.widgets_to_enable:
#     #         widget.setEnabled(True)
#     #
#     #     self.server_uptime = cf.get_server_uptime(self.socket, datastream=self.ds)
#     #     self.socket_uptime = 0.0
#     #
#     #     self.update_time_labels()
#     #     self.update_general_labels()
#     #
#     #     self.timer_update_time_labels.start(1000)
#     #     self.timer_correct_time.start(
#     #         self.datapool.config["time_correction_period"])
#     #     self.timer_update_general_labels.start(
#     #         self.datapool.config["label_update_period"])
#     #
#     #     self.do_ping_avg()
#     #
#     #
#     # def on_disconnected(self):
#     #     print("Signal: disconnected()")
#     #     self.label_status.setText("OFFLINE")
#     #     self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")
#     #
#     #     # self.datapool.status_bar.showMessage("Disconnected")
#     #
#     #     for widget in self.widgets_to_enable:
#     #         widget.setEnabled(False)
#     #
#     #     self.timer_update_time_labels.stop()
#     #     self.timer_correct_time.stop()
#     #     self.timer_update_general_labels.stop()
#
#
#     # def do_ping_avg(self):
#     #     ping_avg = cf.ping_n(
#     #         self.socket,
#     #         n=self.datapool.config["pings_per_test"],
#     #         datastream=self.ds,
#     #     )
#     #
#     #     if ping_avg == -1:
#     #         print("ping_n() returned -1. Something went wrong!")
#     #     else:
#     #         self.label_ping_avg.setText(f"{int(ping_avg*1E6)} \u03bcs")
#     #
#     #
#     # def correct_time(self):
#     #     self.server_uptime = cf.get_server_uptime(s, datastream=self.ds)
#     #     self.socket_uptime = cf.get_socket_uptime(s, datastream=self.ds)
#     #
#     #     self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
#     #     self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")
#     #
#     #
#     # def update_time_labels(self):
#     #     self.server_uptime += 1
#     #     self.socket_uptime += 1
#     #
#     #     self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
#     #     self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")
#     #
#     # def update_general_labels(self):
#     #     pass  # TODO
#     #
#     # def transfer_schedule(self):
#     #     pass  # TODO
#     #
#     # def clear_schedule(self):
#     #     pass  # TODO
#
#     #
#     # def do_get_Bm(self):
#     #     t0 = time()
#     #
#     #     r = cf.get_Bm(self.socket, datastream=self.ds)
#     #
#     #     bx, by, bz = round(r[1] * 1E-3, 3), round(r[2] * 1E-3, 3), round(r[3] * 1E-3, 3)
#     #     tt = time() - t0
#     #     print(f"r_time: {bx}, {by}, {bz}] \u03bcT")
#     #
#     #     self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT  ({int(tt * 1E6)} \u03bcs)")

# from PyQt5.QtCore import QTimer
# from PyQt5.QtWidgets import (
#     QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
#     QGroupBox, QHBoxLayout, QVBoxLayout)
# from PyQt5.QtNetwork import QAbstractSocket, QTcpSocket

stylesheet_groupbox_smallmargins_notitle = """
    QGroupBox {
        padding: 0px;
        padding-top: 0px;
    }
    QGroupBox::title {
        padding: 0px;
        height: 0px;
    }
"""

# From https://doc.qt.io/qtforpython-5/PySide2/QtNetwork/QAbstractSocket.html#PySide2.QtNetwork.PySide2.QtNetwork.QAbstractSocket.SocketError
socketerror_lookup = (
    ("QAbstractSocket.ConnectionRefusedError", "The connection was refused by the peer (or timed out)."),
    ("QAbstractSocket.RemoteHostClosedError", "The remote host closed the connection. Note that the client socket (i.e., this socket) will be closed after the remote close notification has been sent."),
    ("QAbstractSocket.HostNotFoundError", "The host address was not found."),
    ("QAbstractSocket.SocketAccessError", "The socket operation failed because the application lacked the required privileges."),
    ("QAbstractSocket.SocketResourceError", "The local system ran out of resources (e.g., too many sockets)."),
    ("QAbstractSocket.SocketTimeoutError", "The socket operation timed out."),
    ("QAbstractSocket.DatagramTooLargeError", "The datagram was larger than the operating system’s limit (which can be as low as 8192 bytes)."),
    ("QAbstractSocket.NetworkError", "An error occurred with the network (e.g., the network cable was accidentally plugged out)."),
    ("QAbstractSocket.AddressInUseError", "The address specified to bind() is already in use and was set to be exclusive."),
    ("QAbstractSocket.SocketAddressNotAvailableError", "The address specified to bind() does not belong to the host."),
    ("QAbstractSocket.UnsupportedSocketOperationError", "The requested socket operation is not supported by the local operating system (e.g., lack of IPv6 support)."),
    ("QAbstractSocket.ProxyAuthenticationRequiredError", "The socket is using a proxy, and the proxy requires authentication."),
    ("QAbstractSocket.SslHandshakeFailedError", "The SSL/TLS handshake failed, so the connection was closed (only used in QSslSocket )"),
    ("QAbstractSocket.UnfinishedSocketOperationError", "Used by QAbstractSocketEngine only, The last operation attempted has not finished yet (still in progress in the background)."),
    ("QAbstractSocket.ProxyConnectionRefusedError", "Could not contact the proxy server because the connection to that server was denied"),
    ("QAbstractSocket.ProxyConnectionClosedError", "The connection to the proxy server was closed unexpectedly (before the connection to the final peer was established)"),
    ("QAbstractSocket.ProxyConnectionTimeoutError", "The connection to the proxy server timed out or the proxy server stopped responding in the authentication phase."),
    ("QAbstractSocket.ProxyNotFoundError", "The proxy address set with setProxy() (or the application proxy) was not found."),
    ("QAbstractSocket.ProxyProtocolError", "The connection negotiation with the proxy server failed, because the response from the proxy server could not be understood."),
    ("QAbstractSocket.OperationError", "An operation was attempted while the socket was in a state that did not permit it."),
    ("QAbstractSocket.SslInternalError", "The SSL library being used reported an internal error. This is probably the result of a bad installation or misconfiguration of the library."),
    ("QAbstractSocket.SslInvalidUserDataError", "Invalid data (certificate, key, cypher, etc.) was provided and its use resulted in an error in the SSL library."),
    ("QAbstractSocket.TemporaryError", "A temporary error occurred (e.g., operation would block and socket is non-blocking)."),
    ("QAbstractSocket.UnknownSocketError", "An unidentified error occurred."),
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.address = "127.0.0.1"
        self.port = 7777

        self.packetcount = 0

        self.socket_tstart = 0.0
        self.socket_uptime = 0.0
        self.server_uptime = 0.0

        # datapool = DataPool(self, config)
        # self.setCentralWidget(ConnectionWindowDummy(config, datapool))

        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connect)
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.readyRead.connect(self.on_read)
        self.socket.errorOccurred.connect(self.on_socketerror)

        self.ds = QDataStream(self.socket)


        # ====================================================================
        # ==== TIMERS ========================================================
        self.socket_uptime_timer = QTimer()
        self.socket_uptime_timer.timeout.connect(self.do_uptime_update)


        # ==== CONNECTBOX ====================================================
        layout_connectbox1 = QHBoxLayout()

        self.button_connect = QPushButton("CONNECT")
        self.button_connect.clicked.connect(self.do_connect)

        self.button_disconnect = QPushButton("DISCONNECT")
        self.button_disconnect.clicked.connect(self.do_disconnect)

        layout_connectbox1.addWidget(self.button_connect)
        layout_connectbox1.addWidget(self.button_disconnect)

        layout_connectbox2 = QHBoxLayout()

        layout_connectbox2.addWidget(QLabel("Address:"))

        self.le_address = QLineEdit()
        self.le_address.setPlaceholderText("<server address>")
        self.le_address.setText("127.0.0.1")
        layout_connectbox2.addWidget(self.le_address)

        layout_connectbox2.addWidget(QLabel("Port:"))

        self.le_port = QLineEdit()
        self.le_port.setPlaceholderText("<port>")
        self.le_port.setText(str(7777))
        layout_connectbox2.addWidget(self.le_port)

        layout_connectbox = QVBoxLayout()

        layout_connectbox.addLayout(layout_connectbox1)
        layout_connectbox.addLayout(layout_connectbox2)

        group_connectbox = QGroupBox()
        group_connectbox.setStyleSheet(stylesheet_groupbox_smallmargins_notitle)
        group_connectbox.setLayout(layout_connectbox)

        # ====================================================================
        # ==== STATUS BOX ====================================================
        layout_statusbox = QGridLayout()


        layout_statusbox.addWidget(QLabel("Status:"), 0, 0)
        self.label_status = QLabel("OFFLINE")
        self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")
        layout_statusbox.addWidget(self.label_status, 0, 1)

        layout_statusbox.addWidget(QLabel("Host:"), 1, 0)
        self.label_host = QLabel("<host>")
        layout_statusbox.addWidget(self.label_host, 1, 1)

        layout_statusbox.addWidget(QLabel("Client (you):"), 2, 0)
        self.label_client = QLabel("<client>")
        layout_statusbox.addWidget(self.label_client, 2, 1)

        layout_statusbox.addWidget(QLabel("Host uptime:"), 3, 0)
        self.label_host_uptime = QLabel(f"{int(self.server_uptime)} s")
        layout_statusbox.addWidget(self.label_host_uptime, 3, 1)

        layout_statusbox.addWidget(QLabel("Socket uptime:"), 4, 0)
        self.label_socket_uptime = QLabel(f"{int(self.socket_uptime)} s")
        layout_statusbox.addWidget(self.label_socket_uptime, 4, 1)

        layout_statusbox.addWidget(QLabel("Packets exchanged:"), 5, 0)
        self.label_packets_exchanged = QLabel(str(self.packetcount))
        layout_statusbox.addWidget(self.label_packets_exchanged, 5, 1)

        layout_statusbox.addWidget(QLabel("Response time"), 6, 0)
        self.label_ping_avg = QLabel()
        layout_statusbox.addWidget(self.label_ping_avg, 6, 1)
        self.button_ping_avg = QPushButton("test")
        self.button_ping_avg.clicked.connect(self.do_ping_avg)
        layout_statusbox.addWidget(self.button_ping_avg, 6, 2)


        group_statusbox = QGroupBox()
        group_statusbox.setStyleSheet(stylesheet_groupbox_smallmargins_notitle)
        group_statusbox.setLayout(layout_statusbox)

        # ====================================================================
        # ==== MAIN LAYOUT ===================================================

        layout1 = QVBoxLayout()
        layout1.addWidget(group_connectbox)
        layout1.addWidget(group_statusbox)
        group1 = QGroupBox()
        group1.setLayout(layout1)

        self.setCentralWidget(group1)

        self.widgets_online_only = (
            self.button_disconnect,

            self.label_host,
            self.label_client,
            self.label_host_uptime,
            self.label_socket_uptime,
            self.label_ping_avg,
            self.button_ping_avg,
        )

        self.widgets_offline_only = (
            self.button_connect,
            self.le_address,
            self.le_port,
        )

        for widget in self.widgets_online_only:
            widget.setEnabled(False)





    def do_connect(self, timeout=3000):
        address = self.le_address.text()
        port = int(self.le_port.text())
        print(f"Connecting to {address}:{port}")
        self.socket.connectToHost(address, port)

        # Try to connect for `timeout` ms before giving up
        if self.socket.waitForConnected():
            print(f"Connection to {address}:{port} established!")
        else:
            # Error message is already taken care of by self.on_socketerror()
            # Just close socket if it is open:
            if self.socket.isOpen():
                print("connect_socket(): socket closed manually")
                self.socket.close()

    def do_disconnect(self):
        print("Disconnecting...")
        self.socket.disconnectFromHost()

        # Try to connect for `timeout` ms before giving up
        if self.socket.state() == QAbstractSocket.UnconnectedState or \
                socket.waitForDisconnected(timeout):
            print("Disconnected")
        else:
            print(f"Error in disconnect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                print("disconnect_socket(): socket closed manually")
                self.socket.close()

            self.datapool.status_bar.showMessage("Disconnected")

    def on_connect(self):
        print("[DEBUG] SIGNAL: socket.connected")
        # Turn status label to green and display ONLINE
        self.socket_tstart = time()
        self.socket_uptime_timer.start(1000)

        self.label_status.setText("ONLINE")
        self.label_status.setStyleSheet("""QLabel {color: #00aa00;}""")

        # Enable online-only widgets
        for widget in self.widgets_online_only:
            widget.setEnabled(True)
        # Disable offline-only widgets
        for widget in self.widgets_offline_only:
            widget.setEnabled(False)


    def on_disconnect(self):
        print("[DEBUG] SIGNAL: socket.disconnected")
        # Turn status label to red and display OFFLINE
        self.label_status.setText("OFFLINE")
        self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")

        self.socket_uptime_timer.stop()

        for widget in self.widgets_online_only:
            widget.setEnabled(False)
        # Enable offline-only widgets
        for widget in self.widgets_offline_only:
            widget.setEnabled(True)

    def on_read(self):
        print("[DEBUG] SIGNAL: socket.readyRead")
        print("[ON READ]")

        # print(self.socket.readAll()) # NEVER. EVER. DO THIS. OR PACKET CORRPUTION ENSUES!

    def on_socketerror(self, socketerror: QAbstractSocket.SocketError):
        print("[DEBUG] SIGNAL: socket.errorOccurred")
        print("The socket encountered the following error: ", end="")
        print(f"{socketerror_lookup[socketerror][0].split('.')[-1]}: ", end="")
        print(f"{socketerror_lookup[socketerror][1]}")


    def do_ping_avg(self):
        print("[DEBUG] do_ping_avg()")
        ping_avg = cf.ping(self.socket)
        # ping_avg = cf.ping_n(
        #     self.socket,
        #     n=1,
        #     datastream=self.ds,
        # )

        if ping_avg == -1:
            print("ping_n() returned -1. Something went wrong!")
        else:
            self.label_ping_avg.setText(f"{int(ping_avg*1E6)} \u03bcs")

    def do_echo(self):
        print("[DEBUG] do_echo()")
        echo = cf.echo(self.socket, "", self.ds)
        print(echo)


    def do_uptime_update(self):
        # print("[DEBUG] do_uptime_update()")
        self.socket_uptime = time()-self.socket_tstart
        self.label_socket_uptime.setText("{:.0f} s".format(self.socket_uptime))

    # def send_message(self):
    #     print("[DEBUG] send_message()")
    #     confirm = cf.message(self.socket, "Test message", self.ds)
    #     print(confirm)

    def get_uptime(self):
        print("[DEBUG] do_uptime()")
        print(cf.get_socket_uptime(self.socket, self.ds))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())