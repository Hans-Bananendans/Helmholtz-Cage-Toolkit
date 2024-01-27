
# from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
#                              QSizePolicy, QLabel, QFontDialog, QApplication)
# import sys

import sys

from PyQt5.QtNetwork import (
    QTcpServer,
    QTcpSocket,
    QHostAddress,
    QAbstractSocket,
)

from PyQt5.QtCore import (
    QDir,
    QObject,
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
)
from PyQt5.QtWidgets import (
    QApplication,
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

class Messenger(object):
    def __init__(self):
        super(Messenger, self).__init__()
        self.TCP_HOST = "127.0.0.1"  # QtNetwork.QHostAddress.LocalHost
        self.TCP_SEND_TO_PORT = 7011
        self.pSocket = None
        self.listenServer = None
        self.pSocket = QTcpSocket()
        self.pSocket.readyRead.connect(self.slotReadData)
        self.pSocket.connected.connect(self.on_connected)
        self.pSocket.error.connect(self.on_error)

    def slotSendMessage(self):
        self.pSocket.connectToHost(self.TCP_HOST, self.TCP_SEND_TO_PORT)

    def on_error(self, error):
        if error == QAbstractSocket.ConnectionRefusedError:
            print(
                'Unable to send data to port: "{}"'.format(
                    self.TCP_SEND_TO_PORT
                )
            )
            print("trying to reconnect")
            QtCore.QTimer.singleShot(1000, self.slotSendMessage)

    def on_connected(self):
        cmd = "Hi there!"
        print("Command Sent:", cmd)
        ucmd = cmd.encode("utf-8")
        self.pSocket.write(ucmd)
        self.pSocket.flush()
        self.pSocket.disconnectFromHost()

    def slotReadData(self):
        print("Reading data:", self.pSocket.readAll())
        # QByteArray data = pSocket->readAll();


class Client(QObject):
    def SetSocket(self, socket):
        self.socket = socket
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_connected)
        self.socket.readyRead.connect(self.on_readyRead)
        print(
            "Client Connected from IP %s" % self.socket.peerAddress().toString()
        )

    def on_connected(self):
        print("Client Connected Event")

    def on_disconnected(self):
        print("Client Disconnected")

    def on_readyRead(self):
        msg = self.socket.readAll()
        print(type(msg), msg.count())
        print("Client Message:", msg)


class Server(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self)
        self.TCP_LISTEN_TO_PORT = 7011
        self.server = QTcpServer()
        self.server.newConnection.connect(self.on_newConnection)

    def on_newConnection(self):
        while self.server.hasPendingConnections():
            print("Incoming Connection...")
            self.client = Client(self)
            self.client.SetSocket(self.server.nextPendingConnection())

    def StartServer(self):
        if self.server.listen(
            QHostAddress.Any, self.TCP_LISTEN_TO_PORT
        ):
            print(
                "Server is listening on port: {}".format(
                    self.TCP_LISTEN_TO_PORT
                )
            )
        else:
            print("Server couldn't wake up")


class Example(QMainWindow):
    def __init__(self):
        super(Example, self).__init__()
        self.setWindowTitle("TCP/Server")
        self.resize(300, 300)

        self.uiConnect = QPushButton("Connect")

        # layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.uiConnect)
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        # Connections
        self.uiConnect.clicked.connect(self.setup)

    def setup(self):
        self.server = Server()
        self.server.StartServer()

        self.tcp = Messenger()
        self.tcp.slotSendMessage()


def main():

    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


# import sys
# import os
# from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QPushButton, QFileDialog, QVBoxLayout
#
#
# class MyApp(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.window_width, self.window_height = 800, 200
#         self.setMinimumSize(self.window_width, self.window_height)
#
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         self.options = ('Get File Name', 'Get File Names', 'Get Folder Dir', 'Save File Name')
#
#         self.combo = QComboBox()
#         self.combo.addItems(self.options)
#         layout.addWidget(self.combo)
#
#         btn = QPushButton('Launch')
#         btn.clicked.connect(self.launchDialog)
#         layout.addWidget(btn)
#
#     def launchDialog(self):
#         option = self.options.index(self.combo.currentText())
#
#         if option == 0:
#             response = self.getFileName()
#         elif option == 1:
#             response = self.getFileNames()
#         elif option == 2:
#             response = self.getDirectory()
#         elif option == 3:
#             response = self.getSaveFileName()
#         else:
#             print('Got Nothing')
#
#     def getFileName(self):
#         file_filter = 'Data File (*.xlsx *.csv *.dat);; Excel File (*.xlsx *.xls)'
#         response = QFileDialog.getOpenFileName(
#             parent=self,
#             caption='Select a data file',
#             directory=os.getcwd(),
#             filter=file_filter,
#             initialFilter='Excel File (*.xlsx *.xls)'
#         )
#         print(response)
#         return response[0]
#
#     def getFileNames(self):
#         file_filter = 'Data File (*.xlsx *.csv *.dat);; Excel File (*.xlsx *.xls)'
#         response = QFileDialog.getOpenFileNames(
#             parent=self,
#             caption='Select a data file',
#             directory=os.getcwd(),
#             filter=file_filter,
#             initialFilter='Excel File (*.xlsx *.xls)'
#         )
#         return response[0]
#
#     def getDirectory(self):
#         response = QFileDialog.getExistingDirectory(
#             self,
#             caption='Select a folder'
#         )
#         return response
#
#     def getSaveFileName(self):
#         file_filter = 'Data File (*.xlsx *.csv *.dat);; Excel File (*.xlsx *.xls)'
#         response = QFileDialog.getSaveFileName(
#             parent=self,
#             caption='Select a data file',
#             directory='Data File.dat',
#             filter=file_filter,
#             initialFilter='Excel File (*.xlsx *.xls)'
#         )
#         print(response)
#         return response[0]
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     app.setStyleSheet('''
#         QWidget {
#             font-size: 35px;
#         }
#     ''')
#
#     myApp = MyApp()
#     myApp.show()
#
#     try:
#         sys.exit(app.exec_())
#     except SystemExit:
#         print('Closing Window...')