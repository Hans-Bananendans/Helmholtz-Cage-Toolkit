import os
import sys
import socket
from time import sleep, time
from threading import Thread

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
import helmholtz_cage_toolkit.codec.scc2q as scc
import helmholtz_cage_toolkit.client_functions as cf


class ConnectionWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool

        # Load relevant parameters from config file
        # self.server_address = config["server_address"]
        # self.server_port = config["server_port"]

        self.socket_uptime = 0.0
        self.server_uptime = 0.0

        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_read_socket)
        # self.socket.errorOccurred.connect(self.display_error)

        self.datapool.status_bar.showMessage("Disconnected")



        # ==== CONNECTBOX
        layout_connectbox1 = QHBoxLayout()

        self.button_connect = QPushButton(
            QIcon("./assets/icons/feather/phone-call.svg"), "CONNECT"
        )
        self.button_connect.clicked.connect(self.connect_socket)

        self.button_disconnect = QPushButton(
            QIcon("./assets/icons/feather/phone-off.svg"), "DISCONNECT")
        self.button_disconnect.clicked.connect(self.disconnect_socket)

        layout_connectbox1.addWidget(self.button_connect)
        layout_connectbox1.addWidget(self.button_disconnect)

        layout_connectbox2 = QHBoxLayout()

        layout_connectbox2.addWidget(QLabel("Address:"))

        self.lineedit_address = QLineEdit()
        self.lineedit_address.setPlaceholderText("<server address>")
        self.lineedit_address.setText(self.datapool.config["server_address"])
        layout_connectbox2.addWidget(self.lineedit_address)

        layout_connectbox2.addWidget(QLabel("Port:"))

        self.lineedit_port = QLineEdit()
        self.lineedit_port.setPlaceholderText("<port>")
        self.lineedit_port.setText(str(self.datapool.config["server_port"]))
        layout_connectbox2.addWidget(self.lineedit_port)

        layout_connectbox = QVBoxLayout()

        layout_connectbox.addLayout(layout_connectbox1)
        layout_connectbox.addLayout(layout_connectbox2)

        group_connectbox = QGroupBox()
        group_connectbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_connectbox.setLayout(layout_connectbox)


        # ==== STATUS BOX
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

        layout_statusbox.addWidget(QLabel("Response time"), 5, 0)
        self.label_ping_avg = QLabel()
        layout_statusbox.addWidget(self.label_ping_avg, 5, 1)
        self.button_ping_avg = QPushButton("test")
        self.button_ping_avg.clicked.connect(self.do_ping_avg)
        layout_statusbox.addWidget(self.button_ping_avg, 5, 2)


        group_statusbox = QGroupBox()
        group_statusbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_statusbox.setLayout(layout_statusbox)


        # ==== HHC BOX
        layout_hhcbox = QGridLayout()


        layout_hhcbox.addWidget(QLabel("HHC mode:"), 0, 0)
        self.label_hhcmode = QLabel("")
        layout_statusbox.addWidget(self.label_hhcmode, 0, 1)

        layout_hhcbox.addWidget(QLabel("HHC status:"), 1, 0)
        self.label_hhcstatus = QLabel("")
        layout_statusbox.addWidget(self.label_hhcstatus, 1, 1)

        layout_hhcbox.addWidget(QLabel("Schedule name:"), 2, 0)
        self.label_schedule_name = QLabel("")
        layout_statusbox.addWidget(self.label_schedule_name, 2, 1)

        layout_hhcbox.addWidget(QLabel("Segments:"), 3, 0)
        self.label_schedule_length = QLabel("")
        layout_statusbox.addWidget(self.label_schedule_length, 3, 1)

        layout_hhcbox.addWidget(QLabel("Duration:"), 4, 0)
        self.label_schedule_duration = QLabel("")
        layout_statusbox.addWidget(self.label_schedule_duration, 4, 1)


        group_hhcbox = QGroupBox()
        group_hhcbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_hhcbox.setLayout(layout_hhcbox)


        # ==== TRANSFER BOX
        self.button_transfer_schedule = QPushButton(
            QIcon("./assets/icons/feather/upload.svg"), "TRANSFER TO HHC"
        )
        self.button_transfer_schedule.clicked.connect(self.transfer_schedule)
        self.button_transfer_schedule.setMinimumWidth(320)

        self.button_clear_schedule = QPushButton(
            QIcon("./assets/icons/feather/trash.svg"), "CLEAR"
        )
        self.button_clear_schedule.clicked.connect(self.clear_schedule)


        layout_transferbox = QHBoxLayout()

        layout_transferbox.addWidget(self.button_transfer_schedule)
        layout_transferbox.addWidget(self.button_clear_schedule)

        group_transferbox = QGroupBox()
        group_transferbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_transferbox.setLayout(layout_transferbox)



        # button_ping = QPushButton("PING")
        # button_ping.clicked.connect(self.do_ping)
        # self.label_ping = QLabel()

        # button_get_bm = QPushButton("Get Bm")
        # button_get_bm.clicked.connect(self.do_get_Bm)
        # self.label_get_bm = QLabel()

        # # Disable widgets in widgets_to_enable group until connection is made
        self.widgets_to_enable = (
            self.button_disconnect,

            self.label_host,
            self.label_client,
            self.label_host_uptime,
            self.label_socket_uptime,
            self.label_ping_avg,
            self.button_ping_avg,

            self.label_hhcmode,
            self.label_hhcstatus,
            self.label_schedule_name,
            self.label_schedule_length,
            self.label_schedule_duration,

            self.button_transfer_schedule,
            self.button_clear_schedule,
        )


        # ==== MAIN LAYERS

        for widget in self.widgets_to_enable:
            widget.setEnabled(False)



        layout1 = QVBoxLayout()
        layout1.addWidget(group_connectbox)
        layout1.addWidget(group_statusbox)
        layout1.addWidget(group_hhcbox)
        layout1.addWidget(group_transferbox)


        group1 = QGroupBox()
        group1.setMaximumWidth(500)
        group1.setAlignment(Qt.AlignLeft)
        group1.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        group1.setLayout(layout1)

        layout0 = QHBoxLayout()

        layout0.addWidget(group1)
        layout0.addWidget(QWidget())

        self.setLayout(layout0)


        # ==== TIMERS
        if self.datapool.config["connect_on_startup"]:
            self.timer_connect_on_startup = Qtimer()
            self.timer_connect_on_startup.timeout.connect(
                self.connect_on_startup
            )
            self.timer_connect_on_startup.start(
                self.datapool.config["connect_on_startup_delay"]
            )

        self.timer_update_time_labels = QTimer()
        self.timer_update_time_labels.timeout.connect(self.update_time_labels)

        self.timer_correct_time = QTimer()
        self.timer_correct_time.timeout.connect(self.correct_time)

        self.timer_update_general_labels = QTimer()
        self.timer_update_general_labels.timeout.connect(
            self.update_general_labels)


        # Since all TCP communication is implemented using blocking, only
        # one request should ever be active at a time. As a result, a single
        # QDataStream instance should suffice.
        self.ds = QDataStream(self.socket)


    def connect_on_startup(self):
        """Slot for the one-off `timer_connect_on_startup`.

        Stops the timer, and attempt to connect to host.
        """
        self.timer_connect_on_startup.stop()
        self.connect_socket()


    def connect_socket(self, timeout=3000):
        """Tries to make a connection between self.socket and the host. Will
        handle failed attempts. Will update the status_bar.
        """
        # self.socket.connectToHost(self.server_address, self.server_port)
        address = self.lineedit_address.text()
        host = int(self.lineedit_port.text())

        print(f"[DEBUG] Connecting to {address} {type(address)}, {host} {type(host)} ")

        self.socket.connectToHost(address, host)
        # self.socket.connectToHost("127.0.0.1", 7777)

        # Try to connect for `timeout` ms before giving up
        if self.socket.waitForConnected(timeout):
            self.server_address = address
            self.server_port = port
            self.datapool.status_bar.showMessage(
                f"Connected to server at {address}:{host}"
            )
        else:
            self.datapool.status_bar.showMessage(
                f"Connection error: {self.socket.errorString()}"
            )

            print(f"Error in connect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                print("connect_socket(): socket closed manually")
                self.socket.close()

    # @Slot()
    def disconnect_socket(self, timeout=3000):
        self.socket.disconnectFromHost()

        # Try to connect for `timeout` ms before giving up
        if self.socket.state() == QAbstractSocket.UnconnectedState or \
                socket.waitForDisconnected(timeout):
            self.datapool.status_bar.showMessage("Disconnected")
        else:
            print(f"Error in disconnect_socket(): {self.socket.errorString()}")
            if self.socket.isOpen():
                print("disconnect_socket(): socket closed manually")
                self.socket.close()

            self.datapool.status_bar.showMessage("Disconnected")

    # @Slot()
    def on_read_socket(self):
        print("Signal: read_socket()")
        pass

    # @Slot()
    def on_connected(self):
        print("Signal: connected()")
        # Set connection status to connected.
        self.label_status.setText("ONLINE")
        self.label_status.setStyleSheet("""QLabel {color: #00aa00;}""")

        for widget in self.widgets_to_enable:
            widget.setEnabled(True)

        self.server_uptime = cf.get_server_uptime(self.socket, datastream=self.ds)
        self.socket_uptime = 0.0

        self.update_time_labels()
        self.update_general_labels()

        self.timer_update_time_labels.start(1000)
        self.timer_correct_time.start(
            self.datapool.config["time_correction_period"])
        self.timer_update_general_labels.start(
            self.datapool.config["label_update_period"])

        self.do_ping_avg()

    # @Slot()
    def on_disconnected(self):
        print("Signal: disconnected()")
        self.label_status.setText("OFFLINE")
        self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")

        self.datapool.status_bar.showMessage("Disconnected")

        for widget in self.widgets_to_enable:
            widget.setEnabled(False)

        self.timer_update_time_labels.stop()
        self.timer_correct_time.stop()
        self.timer_update_general_labels.stop()


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


    def do_ping_avg(self):
        ping_avg = cf.ping_n(
            self.socket,
            n=self.datapool.config["pings_per_test"],
            datastream=self.ds,
        )

        if ping_avg == -1:
            print("ping_n() returned -1. Something went wrong!")
        else:
            self.label_ping_avg.setText(f"{int(ping_avg*1E6)} \u03bcs")

    # # @Slot()
    # def do_ping(self):
    #     t0 = time()
    #     socket_stream = QDataStream(self.socket)
    #     packet_out = scc.encode_epacket("")
    #
    #     socket_stream.writeRawData(packet_out)
    #
    #     if self.socket.waitForReadyRead(100):
    #         if scc.decode_epacket(socket_stream.readRawData(scc.packet_size)) == "":
    #             t = time()-t0
    #             self.label_ping.setText(f"ping(): {int(t * 1E6)} \u03bcs")
    #         else:
    #             print("ping() failed (-1)!")
    #             self.label_ping.setText("ping(): -1")


    def correct_time(self):
        self.server_uptime = cf.get_server_uptime(s, datastream=self.ds)
        self.socket_uptime = cf.get_socket_uptime(s, datastream=self.ds)

        self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
        self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")


    def update_time_labels(self):
        self.server_uptime += 1
        self.socket_uptime += 1

        self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
        self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")

    def update_general_labels(self):
        pass  # TODO

    def transfer_schedule(self):
        pass  # TODO

    def clear_schedule(self):
        pass  # TODO



    # def do_ping(self):
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


    # def do_get_Bm(self):
    #     t0 = time()
    #     socket_stream = QDataStream(self.socket)
    #     packet_out = scc.encode_bpacket([0.] * 4)
    #     # print(packet_out)
    #     socket_stream.writeRawData(packet_out)
    #
    #     if self.socket.waitForReadyRead(100):
    #         inc = socket_stream.readRawData(scc.packet_size)
    #         r = scc.decode_bpacket(inc)
    #
    #         bx, by, bz = round(r[1]*1E-3, 3), round(r[2]*1E-3, 3), round(r[3]*1E-3, 3)
    #         tt = time()-t0
    #         self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT  ({int(tt*1E6)} \u03bcs)")
    #
    #
    # def do_get_Bm2(self):
    #     t0 = time()
    #
    #     r = get_Bm(self.socket)
    #     # r = scc.decode_bpacket(send_and_receive(scc.encode_bpacket([0.] * 4), self.socket))
    #
    #     bx, by, bz = round(r[1]*1E-3, 3), round(r[2]*1E-3, 3), round(r[3]*1E-3, 3)
    #     tt = time()-t0
    #     print(f"r_time: {bx}, {by}, {bz}] \u03bcT")
    #
    #     self.label_get_bm.setText(f"Bm2 = [{bx}, {by}, {bz}] \u03bcT  ({int(tt*1E6)} \u03bcs)")
    # @Slot()
    def do_get_Bm(self):
        t0 = time()

        r = client_functions.get_Bm(self.socket, datastream=self.ds)

        bx, by, bz = round(r[1] * 1E-3, 3), round(r[2] * 1E-3, 3), round(r[3] * 1E-3, 3)
        tt = time() - t0
        print(f"r_time: {bx}, {by}, {bz}] \u03bcT")

        self.label_get_bm.setText(f"Bm = [{bx}, {by}, {bz}] \u03bcT  ({int(tt * 1E6)} \u03bcs)")

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
    


