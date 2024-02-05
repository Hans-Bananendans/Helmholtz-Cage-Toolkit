import hashlib
from numpy import array
from time import time
from timeit import timeit



tm = 1705321618.6226978
Bm = [-12345.12345, -12345.23456, -12345.34567]
Im = [1234.1234, 1234.2345, 1234.3456]
Ic = [-41.039767666050004, -86.828165545449992, 27.42272022095]
Vc = [60.11111111111, 60.2222222222222, 60.3333333333333]
Vvc = [1.101, 1.202, 1.303]
Vcc = [2.101, 2.202, 2.303]

in0 = [tm, Bm, Im, Ic, Vc, Vvc, Vcc]

_pad = "#"

seg_test = [35, 60, 355.932203, -83331.392, -55280.007, 18644.068]


def encode_spacket0(
    i_seg: int,
    n_seg: int,
    t_seg: float,
    Bx_seg: float,
    By_seg: float,
    Bz_seg: float):  # Q Compatible
    """ Encodes an s_packet, which has the following anatomy:
    s (1 B)    segment number (32 B)    number of segments (32 B)
        segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Optimization: ~4400 ns/encode
    """
    return "s{:0>32}{:0>32}{:0<20}{:0<16}{:0<16}{:0<16}{}".format(
        str(i_seg)[:16],
        str(n_seg)[:16],
        str(t_seg)[:16],
        str(Bx_seg)[:16],
        str(By_seg)[:16],
        str(Bz_seg)[:16],
        _pad*123).encode()

def encode_spacket1(
    i_seg: int,
    n_seg: int,
    t_seg: float,
    Bx_seg: float,
    By_seg: float,
    Bz_seg: float):  # Q Compatible
    """ Encodes an s_packet, which has the following anatomy:
    s (1 B)    segment number (32 B)    number of segments (32 B)
        segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Optimization: ~4400 ns/encode
    """
    return "s{:0>32.32}{:0>32.32}{:0<20.20}{:0<16.16}{:0<16.16}{:0<16.16}{}".format(
        str(i_seg),
        str(n_seg),
        str(t_seg),
        str(Bx_seg),
        str(By_seg),
        str(Bz_seg),
        _pad*123).encode()

def decode_tpacket(t_packet):
    """ Decodes a t_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    Bm (3x16 B)    Im (3x12 B)    Ic (3x12 B)
               Vc (3x12 B)         Vvc (3x12 B)   Vcc (3x12 B)   padding (7 B)

    Optimization: ~5500 ns/decode (FX-8350)
    """
    t_decoded = t_packet.decode()
    return float(t_decoded[1:21]), \
        [
            float(t_decoded[21:37]),        # \
            float(t_decoded[37:53]),        # Bm
            float(t_decoded[53:69]),        # /
        ], [
            float(t_decoded[69:81]),        # \
            float(t_decoded[81:93]),        # Im
            float(t_decoded[93:105]),       # /
        ], [
            float(t_decoded[105:117]),      # \
            float(t_decoded[117:129]),      # Ic
            float(t_decoded[129:141]),      # /
        ], [
            float(t_decoded[141:153]),      # \
            float(t_decoded[153:165]),      # Vc
            float(t_decoded[165:177]),      # /
        ], [
            float(t_decoded[177:189]),       # \
            float(t_decoded[189:201]),       # Vvc
            float(t_decoded[201:213]),       # /
        ], [
            float(t_decoded[213:225]),       # \
            float(t_decoded[225:237]),       # Vcc
            float(t_decoded[237:249]),       # /
        ]


o0 = encode_spacket0(*seg_test)
o1 = encode_spacket1(*seg_test)


# o1 = decode_tpacket(o0)

print(len(o0), o0)
print(len(o1), o1)


# for i in range(7):
#     if i == 0:
#         print(str(in0[i]), str(o1[i]))
#     else:
#         for j in range(3):
#             print(str(in0[i][j]), str(o1[i][j]))


# o1 = encode_tpacket_1(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o2 = encode_tpacket_2(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o3 = encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o4 = encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)

# for thing in (o1, o2, o3, o4, o1 == o2, o2 == o3):
#     print(thing)



n = int(1E5)
tmult = int(1E6)

# print(f"encode_tpacket0 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket0(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
#
# print(f"encode_tpacket1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket1(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
#
# print(f"encode_tpacket2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket2(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")

print(f"encode_spacket0 (n={'{:1.0E}'.format(n)}):",
      round(timeit('encode_spacket0(*seg_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"encode_spacket1 (n={'{:1.0E}'.format(n)}):",
      round(timeit('encode_spacket1(*seg_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

# print(f"decode_tpacket (n={'{:1.0E}'.format(n)}):",
#       round(timeit('decode_tpacket(o0)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
#
# print(f"decode_tpacket_2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('decode_tpacket_2(o0)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")


# print(f"encode_tpacket_2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket_2(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
# print(f"encode_tpacket_3 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
# print(f"encode_tpacket_4 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
# N = 12345.67890
#
# NN = [
#     12345.67890,
#     -12345.67890,
#     1.0,
#     2,
#     0.0,
#     0.1543,
# ]
#
#
#
# def f1(N):
#     if N >= 0:
#         l, s = divmod(float(N), 1)
#         return str(int(l)), str(s)[1:5]
#     else:
#         l, s = divmod(float(N), -1)
#         return str(int(l)), str(s)[2:6]
#
# def f2(N):
#     l, s = str(float(N)).split(".")
#     return l[-6:], ("."+s+"000")[:4]
#
#
# for num in NN:
#     print(f1(num), f2(num))
#
#
#
# n = int(1E4)
# tmult = int(1E6)
#
# print(f"f1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f1(N)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
# print(f"f2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f2(N)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")



# self_Bc = [50., 50., 50.]
# self_Br = [-5., 2.5, -45.]
# self_Bm = [70., 70., 70.]
# self_Vc = [60.0, 60.0, 60.0]
# self_Ic = [1200., 1200., 1200.]
# self_Im = [1400., 1400., 1400.]
#
# def f1(self_Bc, self_Br, self_Bm, self_Vc, self_Ic, self_Im):
#     Bc = [self_Bc[0], self_Bc[1], self_Bc[2],
#           (self_Bc[0] ** 2 + self_Bc[1] ** 2 + self_Bc[2] ** 2) ** (1 / 2)]
#     Br = [self_Br[0], self_Br[1], self_Br[2],
#           (self_Br[0] ** 2 + self_Br[1] ** 2 + self_Br[2] ** 2) ** (1 / 2)]
#     Bm = [self_Bm[0], self_Bm[1], self_Bm[2],
#           (self_Bm[0] ** 2 + self_Bm[1] ** 2 + self_Bm[2] ** 2) ** (1 / 2)]
#
#     Bo = [Bc[0] - Br[0], Bc[1] - Br[1], Bc[2] - Br[2],
#           ((Bc[0] - Br[0]) ** 2 + (Bc[1] - Br[1]) ** 2 + (Bc[2] - Br[2]) ** 2) ** (1 / 2)]
#     Bd = [Bo[0] - Bm[0], Bo[1] - Bm[1], Bo[2] - Bm[2],
#           ((Bo[0] - Bm[0]) ** 2 + (Bo[1] - Bm[1]) ** 2 + (Bo[2] - Bm[2]) ** 2) ** (1 / 2)]
#
#     Vc = [self_Vc[0], self_Vc[1], self_Vc[2], self_Vc[0] + self_Vc[1] + self_Vc[2]]
#     Ic = [self_Ic[0], self_Ic[1], self_Ic[2], self_Ic[0] + self_Ic[1] + self_Ic[2]]
#     Im = [self_Im[0], self_Im[1], self_Im[2], self_Im[0] + self_Im[1] + self_Im[2]]
#     Id = [Ic[0] - Im[0], Ic[1] - Im[1], Ic[2] - Im[2], Ic[3] - Im[3]]
#
#     return Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id
#
# n = int(1E6)
# tmult = int(1E6)
#
# print(f"f1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f1(self_Bc, self_Br, self_Bm, self_Vc, self_Ic, self_Im)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")



# a = [4., 4., 4., 4.]
# b = [1., 2., 3., 3.5]
#
#
# def f1(a, b):
#     return [a[i]-b[i] for i in range(4)]
#
# def f2(a, b):
#     c = [0., 0., 0., 0.]
#     for i in range(4):
#         c[i] = a[i]-b[i]
#     return c
#
# def f3(a, b):
#     return [a[0]-b[0], a[1]-b[1], a[2]-b[2], a[3]-b[3]]
#
#
# print(f1(a, b), f2(a, b), f3(a, b))
# print(type(f1(a, b)), type(f2(a, b)), type(f3(a, b)))
# print(type(f1(a, b)[0]), type(f2(a, b)[0]), type(f3(a, b)[0]))
#
# n = int(1E6)
# tmult = int(1E6)
#
# print(f"f1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f1(a, b)', globals=globals(), number=n)*tmult/n, 3), "us")
#
# print(f"f2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f2(a, b)', globals=globals(), number=n)*tmult/n, 3), "us")
#
# print(f"f3 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f3(a, b)', globals=globals(), number=n)*tmult/n, 3), "us")


# test_schedule = [
#     [0, 6, 0.0, 0.0, 0.0, 0.0],
#     [1, 6, 3.0, 1.0, 0.0, 0.0],
#     [2, 6, 5.0, 2.0, 0.0, 0.0],
#     [3, 6, 7.0, 3.0, 0.0, 0.0],
#     [4, 6, 9.0, 4.0, 0.0, 0.0],
#     [5, 6, 10.0, 0.0, 0.0, 0.0],
# ]
# t0 = time()
# bshash = hashlib.blake2b(array(test_schedule).tobytes(), digest_size=64).digest()
# t1 = time()
# bshash_hex = hashlib.blake2b(array(test_schedule).tobytes(), digest_size=64).hexdigest()
# t2 = time()
# print(bshash, len(bshash))
# print(bshash_hex, len(bshash_hex), type(bshash_hex))
# print("Time:", int((t1-t0)*1E6), ",", int((t2-t1)*1E6), "\u03bcs")



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