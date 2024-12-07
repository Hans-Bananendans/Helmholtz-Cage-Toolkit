"""
This is an all-in-one test script to test and benchmark most functionalities
of the server.


WORK IN PROGRESS

While this version uses QTcpSocket which results in more representative test,
you have to embed this into a Qt implementation. Doing so means that the tests
will be executed as part of the back-end Qt event loop, which has the tendency
to suppress any error messages to the terminal. The whole point of these tests
is to debug, and so this makes it rather poor for this purpose.

"""

import os
import sys
import socket
from time import sleep, time
from timeit import timeit

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
from helmholtz_cage_toolkit.server.server_config import server_config
import helmholtz_cage_toolkit.scc.scc4 as codec
import helmholtz_cage_toolkit.client_functions as cf




# ==== TESTS =============================================================
def tests():
    print("\n ==== Starting tests ====")

    a = invalid_function()

    sleep(2)




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()


        # ==== NETWORKING ====================================================
        self.server_address = server_config["SERVER_ADDRESS"]
        self.server_port = server_config["SERVER_PORT"]

        self.socket = QTcpSocket(self)
        self.socket.connected.connect(self.on_connect)
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.readyRead.connect(self.on_read)
        self.socket.errorOccurred.connect(self.on_socketerror)

        self.ds = QDataStream(self.socket)


        # ==== UI ============================================================
        self.setGeometry(300, 300, 280, 80)

        layout_hbox = QHBoxLayout()

        self.button_connect = QPushButton("Connect")
        self.button_connect.clicked.connect(self.do_connect)

        self.button_start = QPushButton("Start")
        self.button_start.clicked.connect(self.do_start)

        layout_hbox.addWidget(self.button_connect)
        layout_hbox.addWidget(self.button_start)

        self.bar = QProgressBar()
        self.bar.setGeometry(30, 40, 200, 25)

        self.txt = QLabel()

        layout_vbox = QVBoxLayout()
        layout_vbox.addLayout(layout_hbox)
        layout_vbox.addWidget(self.bar)
        layout_vbox.addWidget(self.txt)

        central_widget = QGroupBox()
        central_widget.setLayout(layout_vbox)
        self.setCentralWidget(central_widget)

        self.n_tests = 0
        self.i_tests = 0
        self.txt_test = ""
        self.update_gui()

    # ==== UTILITIES =========================================================
    def do_connect(self, timeout=3000):
        address = self.server_address
        port = self.server_port
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

    def do_start(self):
        self.n_tests = 27
        self.i_tests = 0
        self.txt_test = ""
        self.update_gui()

        try:
            tests()
            self.do_disconnect()

        except: # noqa
            self.button_start.setText("ERROR")
            self.do_disconnect()

    def on_connect(self):
        print("[DEBUG] SIGNAL: socket.connected")
        self.socket_tstart = time()
        self.button_connect.setText("CONNECTED")
        self.button_connect.setEnabled(False)


    def on_disconnect(self):
        print("[DEBUG] SIGNAL: socket.disconnected")
        self.button_connect.setEnabled(True)
        self.button_connect.setText("Connect")

    def on_read(self):
        # print("[DEBUG] SIGNAL: socket.readyRead")
        # print("[ON READ]")
        pass

    def on_socketerror(self, socketerror: QAbstractSocket.SocketError):
        print("[DEBUG] SIGNAL: socket.errorOccurred")
        print("The socket encountered the following error: ", end="")
        print(f"{socketerror_lookup[socketerror][0].split('.')[-1]}: ", end="")
        print(f"{socketerror_lookup[socketerror][1]}")

    def update_gui(self):
        self.txt.setText(
            f"({self.i_tests}/{self.n_tests}) {self.txt_test}"
        )
        if self.n_tests == 0:
            self.bar.setValue(0)
        else:
            self.bar.setValue(int(self.i_tests/self.n_tests*100))

    # def test_test(self):
    #     print("[DEBUG] Starting tests()")
    #
    #     for i in range(self.n_tests):
    #         self.i_tests += 1
    #         self.txt_test = f"Test {self.i_tests}"
    #         self.update_gui()
    #         sleep(5/self.n_tests)
    #     sleep(2)



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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())