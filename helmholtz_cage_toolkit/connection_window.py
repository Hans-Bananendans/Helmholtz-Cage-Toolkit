import os
import sys
import socket
from time import sleep, time
from threading import Thread

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
import helmholtz_cage_toolkit.scc.scc2q as scc
import helmholtz_cage_toolkit.client_functions as cf


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


class ConnectionWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool

        # Define instance variables
        self.socket_uptime = 0.0
        self.server_uptime = 0.0
        self.packet_exchanged = 0

        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_read_socket)
        self.socket.errorOccurred.connect(self.on_socketerror)

        # Since all TCP communication is implemented using blocking, only
        # one request should ever be active at a time. As a result, a single
        # QDataStream instance should suffice.
        self.ds = QDataStream(self.socket)

        self.datapool.socket = self.socket
        self.datapool.ds = self.ds

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

        self.le_address = QLineEdit()
        self.le_address.setPlaceholderText("<server address>")
        self.le_address.setText(self.datapool.config["server_address"])
        layout_connectbox2.addWidget(self.le_address)

        layout_connectbox2.addWidget(QLabel("Port:"))

        self.le_port = QLineEdit()
        self.le_port.setPlaceholderText("<port>")
        self.le_port.setText(str(self.datapool.config["server_port"]))
        layout_connectbox2.addWidget(self.le_port)

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
        self.label_server = QLabel("<host>")
        layout_statusbox.addWidget(self.label_server, 1, 1)

        layout_statusbox.addWidget(QLabel("Client (you):"), 2, 0)
        self.label_client = QLabel("<client>")
        layout_statusbox.addWidget(self.label_client, 2, 1)

        layout_statusbox.addWidget(QLabel("Host uptime:"), 3, 0)
        self.label_server_uptime = QLabel(f"{int(self.server_uptime)} s")
        layout_statusbox.addWidget(self.label_server_uptime, 3, 1)

        layout_statusbox.addWidget(QLabel("Socket uptime:"), 4, 0)
        self.label_socket_uptime = QLabel(f"{int(self.socket_uptime)} s")
        layout_statusbox.addWidget(self.label_socket_uptime, 4, 1)

        layout_statusbox.addWidget(QLabel("Packets exchanged:"), 5, 0)
        self.label_packets_exchanged = QLabel(str(self.packet_exchanged))
        layout_statusbox.addWidget(self.label_packets_exchanged, 5, 1)

        layout_statusbox.addWidget(QLabel("Response time"), 6, 0)
        self.label_ping_avg = QLabel()
        layout_statusbox.addWidget(self.label_ping_avg, 6, 1)
        self.button_ping_avg = QPushButton("test")
        self.button_ping_avg.clicked.connect(self.do_ping_avg)
        layout_statusbox.addWidget(self.button_ping_avg, 6, 2)


        group_statusbox = QGroupBox()
        group_statusbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_statusbox.setLayout(layout_statusbox)


        # ==== HHC BOX
        layout_hhcbox = QGridLayout()


        layout_hhcbox.addWidget(QLabel("HHC mode:"), 0, 0)
        self.label_hhcmode = QLabel("")
        layout_hhcbox.addWidget(self.label_hhcmode, 0, 1)

        layout_hhcbox.addWidget(QLabel("HHC status:"), 1, 0)
        self.label_hhcstatus = QLabel("")
        layout_hhcbox.addWidget(self.label_hhcstatus, 1, 1)

        layout_hhcbox.addWidget(QLabel("Schedule name:"), 2, 0)
        self.label_schedule_name = QLabel("")
        layout_hhcbox.addWidget(self.label_schedule_name, 2, 1)

        layout_hhcbox.addWidget(QLabel("Segments:"), 3, 0)
        self.label_schedule_length = QLabel("")
        layout_hhcbox.addWidget(self.label_schedule_length, 3, 1)

        layout_hhcbox.addWidget(QLabel("Duration:"), 4, 0)
        self.label_schedule_duration = QLabel("")
        layout_hhcbox.addWidget(self.label_schedule_duration, 4, 1)


        group_hhcbox = QGroupBox()
        group_hhcbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_hhcbox.setLayout(layout_hhcbox)


        # ==== TRANSFER BOX
        self.button_transfer_schedule = QPushButton(
            QIcon("./assets/icons/feather/upload.svg"), "TRANSFER TO HHC"
        )
        self.button_transfer_schedule.clicked.connect(self.do_transfer_schedule)
        self.button_transfer_schedule.setMinimumWidth(320)

        self.button_clear_schedule = QPushButton(
            QIcon("./assets/icons/feather/trash.svg"), "CLEAR"
        )
        self.button_clear_schedule.clicked.connect(self.do_clear_schedule)


        layout_transferbox = QHBoxLayout()

        layout_transferbox.addWidget(self.button_transfer_schedule)
        layout_transferbox.addWidget(self.button_clear_schedule)

        group_transferbox = QGroupBox()
        group_transferbox.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )
        group_transferbox.setLayout(layout_transferbox)


        # ==== MAIN LAYERS

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
        layout0.addWidget(QWidget())  # Right half of window as placeholder

        self.setLayout(layout0)


        # ==== TIMERS
        if self.datapool.config["connect_on_startup"]:
            self.timer_connect_on_startup = QTimer()
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



        # ==== PRECONFIG
        # Gather timers. Leave self.timer_connect_on_startup out
        self.timers = (
            self.timer_correct_time,
            self.timer_update_time_labels,
            self.timer_update_general_labels,
        )
        self.timers_intervals = [0]*len(self.timers)

        self.widgets_online_only = (
            self.button_disconnect,

            self.label_server,
            self.label_client,
            self.label_server_uptime,
            self.label_socket_uptime,
            self.label_packets_exchanged,
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

        self.widgets_offline_only = (
            self.button_connect,
            self.le_address,
            self.le_port,
        )

        # Disable widgets in widgets_online_only group until connection is made
        for widget in self.widgets_online_only:
            widget.setEnabled(False)

        self.datapool.status_bar.showMessage("Disconnected")


        self.hhc_play_mode = "-"
        self.hhc_play_status = "-"
        self.hhc_schedule_info = ("-", "-", "-")

        self.label_hhcmode.setText("-")
        self.label_hhcstatus.setText("-")
        self.label_schedule_name.setText("-")
        self.label_schedule_length.setText("-")
        self.label_schedule_duration.setText("-")


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
        address = self.le_address.text()
        port = int(self.le_port.text())
        self.socket.connectToHost(address, port)
        # self.socket.connectToHost("127.0.0.1", 7777)

        # Try to connect for a while, before giving up
        if self.socket.waitForConnected():
            pass
        else:
            # If socket is somehow still open, close it
            if self.socket.isOpen():
                self.socket.close()

    # @Slot()
    def disconnect_socket(self, timeout=3000):
        self.socket.disconnectFromHost()

        # Try to connect for `timeout` ms before giving up
        if self.socket.state() == QAbstractSocket.UnconnectedState or \
                socket.waitForDisconnected(timeout):
            pass
        else:
            # If socket is somehow still open, close it
            if self.socket.isOpen():
                self.socket.close()


    # @Slot()
    def on_read_socket(self):
        # print("[DEBUG] SIGNAL: readyRead")
        self.packet_exchanged += 1
        # TODO AFTER TESTING, MOVE THIS TO self.update_general_labels()
        self.label_packets_exchanged.setText(str(self.packet_exchanged))

    # @Slot()
    def on_connected(self):
        # print("[DEBUG] SIGNAL: socket.connected")
        self.datapool.socket_connected = True

        # Set connection status to connected.
        self.label_status.setText("ONLINE")
        self.label_status.setStyleSheet("""QLabel {color: #00aa00;}""")

        for widget in self.widgets_online_only:
            widget.setEnabled(True)
        for widget in self.widgets_offline_only:
            widget.setEnabled(False)

        self.server_uptime = cf.get_server_uptime(self.socket, datastream=self.ds)
        self.socket_uptime = 0.0

        self.update_time_labels()
        self.update_general_labels()

        self.timer_update_time_labels.start(1000)
        self.timer_correct_time.start(
            self.datapool.config["time_correction_period"])
        self.timer_update_general_labels.start(
            self.datapool.config["label_update_period"])

        # Display addresses and ports
        server_address = self.socket.peerAddress().toString()
        server_port = self.socket.peerPort()
        self.label_server.setText("{}:{}".format(server_address, server_port))
        self.label_client.setText("{}:{}".format(
            self.socket.localAddress().toString(), self.socket.localPort()
        ))
        print(f"Connected to server at {server_address}:{server_port}")
        self.datapool.status_bar.showMessage(
            f"Connected to server at {server_address}:{server_port}"
        )

        self.packet_exchanged = 0

        self.do_ping_avg()

        # self.datapool.enable_Bm_acquisition()
        self.datapool.enable_timer_get_telemetry()
        self.datapool.command_window.do_on_connected()

    # @Slot()
    def on_disconnected(self):
        # print("[DEBUG] SIGNAL: socket.disconnected")
        self.datapool.socket_connected = False

        # self.datapool.disable_Bm_acquisition()
        self.datapool.disable_timer_get_telemetry()

        self.label_status.setText("OFFLINE")
        self.label_status.setStyleSheet("""QLabel {color: #ff0000;}""")

        self.label_server.setText("<host>")
        self.label_client.setText("<client>")
        print("Disconnected")
        self.datapool.status_bar.showMessage("Disconnected")

        for widget in self.widgets_online_only:
            widget.setEnabled(False)
        for widget in self.widgets_offline_only:
            widget.setEnabled(True)

        self.datapool.command_window.do_on_disconnected()

        self.timer_update_time_labels.stop()
        self.timer_correct_time.stop()
        self.timer_update_general_labels.stop()





    def on_socketerror(self, socketerror: QAbstractSocket.SocketError):
        # print("[DEBUG] SIGNAL: socket.errorOccurred")
        print("The socket encountered the following error: ", end="")
        print(f"{socketerror_lookup[socketerror][0].split('.')[-1]}: ", end="")
        print(f"{socketerror_lookup[socketerror][1]}")


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
        self.server_uptime = cf.get_server_uptime(self.socket, datastream=self.ds)
        self.socket_uptime = cf.get_socket_uptime(self.socket, datastream=self.ds)

        self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
        self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")


    def update_time_labels(self):
        self.server_uptime += 1
        self.socket_uptime += 1

        self.label_server_uptime.setText(f"{int(self.server_uptime)} s")
        self.label_socket_uptime.setText(f"{int(self.socket_uptime)} s")

    def update_general_labels(self):
        hhc_play_mode = cf.get_play_mode(self.socket, self.ds)
        if hhc_play_mode != self.hhc_play_mode:
            if hhc_play_mode:
                self.label_hhcmode.setText("play mode")
            else:
                self.label_hhcmode.setText("manual mode")
        self.hhc_play_mode = hhc_play_mode

        hhc_play_status = cf.get_play_status(self.socket, self.ds)
        if hhc_play_status != self.hhc_play_status:
            self.label_hhcstatus.setText(hhc_play_status)
        self.hhc_play_status = hhc_play_status

        hhc_schedule_info = cf.get_schedule_info(self.socket, self.ds)
        if hhc_schedule_info != self.hhc_schedule_info:
            self.label_schedule_name.setText(hhc_schedule_info[0])
            self.label_schedule_length.setText(str(hhc_schedule_info[1]))
            self.label_schedule_duration.setText("{:.3f} s".format(
                hhc_schedule_info[2]))
        self.hhc_schedule_info = hhc_schedule_info


    def suspend_timers(self):  # TODO Keep in here for now, but not sure if needed
        print("[DEBUG] suspend_timers()")
        for i, timer in enumerate(self.timers):
            self.timers_intervals[i] = timer.interval()
            timer.stop()

    def resume_timers(self):  # TODO Keep in here for now, but not sure if needed
        print("[DEBUG] resume_timers()")
        for i, timer in enumerate(self.timers):
            timer.start(self.timers_intervals[i])


    def do_transfer_schedule(self):
        # self.suspend_timers()  # TODO: Remove after tests

        t0 = time()
        schedule = list(column_stack(self.datapool.schedule))
        confirm = cf.transfer_schedule(
            self.socket,
            schedule,
            "myschedule",
            datastream=self.ds
        )

        print("Done. Transferred {} segments in {:.0f} \u03bcs".format(
            len(schedule),
            (time()-t0)*1E6
        ))

        # print("[DEBUG] TYPE CHECK: {}|{}, {}|{}, {}|{}, {}|{}, {}|{}, {}|{}".format(
        #     schedule[1][0], type(schedule[1][0]),
        #     schedule[1][1], type(schedule[1][1]),
        #     schedule[1][2], type(schedule[1][2]),
        #     schedule[1][3], type(schedule[1][3]),
        #     schedule[1][4], type(schedule[1][4]),
        #     schedule[1][5], type(schedule[1][5]),))

        # Simulates the effect of s-packet encoding and decoding on a copy of
        # the local schedule, so that the local schedule and remote schedule
        # can be hashed apples-to-apples.
        for i, row in enumerate(schedule):
            schedule[i] = [
                int(float(str(row[0])[:16])),
                int(float(str(row[1])[:16])),
                float(str(row[2])[:16]),
                float(str(row[3])[:16]),
                float(str(row[4])[:16]),
                float(str(row[5])[:16])
            ]

        # print("[DEBUG] TYPE CHECK: {}|{}, {}|{}, {}|{}, {}|{}, {}|{}, {}|{}".format(
        #     schedule[1][0], type(schedule[1][0]),
        #     schedule[1][1], type(schedule[1][1]),
        #     schedule[1][2], type(schedule[1][2]),
        #     schedule[1][3], type(schedule[1][3]),
        #     schedule[1][4], type(schedule[1][4]),
        #     schedule[1][5], type(schedule[1][5]),))


        # print("[DEBUG] Print schedule @ server")
        # confirm1 = cf.print_schedule(self.socket, datastream=self.ds)

        # Verify transfer by comparing BLAKE2b hash of local and remote schedule

        verify = cf.verify_schedule(self.socket, schedule, datastream=self.ds)
        if verify:
            print("Transfer verification: PASS")
        else:
            print("Transfer verification: FAIL")
            local_hash = cf.schedule_hash(schedule)
            print("Local hash:", local_hash)
            remote_hash = cf.get_schedule_hash(self.socket, datastream=self.ds)
            print("Remote hash:", remote_hash)

        # self.resume_timers()  # TODO: Remove after tests

    def do_clear_schedule(self):
        ack = cf.initialize_schedule(self.socket, datastream=self.ds)



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
    


