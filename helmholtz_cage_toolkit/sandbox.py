import hashlib
from numpy import array
from time import time
from timeit import timeit



tm = 1705321618.6226978
Bm = [-12345.12345, -12345.23456, -12345.34567]
Im = [1234.1234, 1234.2345, 1234.3456]
Ic = [2345.1234, 2345.2345, 2345.3456]
Vc = [60.1, 60.2, 60.3]
Vvc = [1.101, 1.202, 1.303]
Vcc = [2.101, 2.202, 2.303]

in0 = [tm, Bm, Im, Ic, Vc, Vvc, Vcc]

_pad = "#"

def encode_tpacket(tm, Bm, Im, Ic, Vc, Vvc, Vcc):
    """ Encodes a b_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Optimization: ~13500 ns/encode
    """
    output = [tm, ]
    for par in (Bm, Im, Ic, Vc, Vvc, Vcc):
        output += [par[0], par[1], par[2]]
    return ("t{:0<20}"+"{:0<16}"*3+"{:0<12}"*15+"#"*7).format(*output).encode()

# def encode_tpacket_1(tm, Bm, Im, Ic, Vc, Vvc, Vcc):
#     """ Encodes a b_packet, which has the following anatomy:
#     b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)
#
#     Optimization: ~12500 ns/encode
#     """
#     output = [tm, ]
#     for par in (Bm, Im, Ic, Vc, Vvc, Vcc):
#         output += [par[0], par[1], par[2]]
#     return ("t{:0<20}"+"{:0<16}"*3+"{:0<12}"*15+"#######").format(*output).encode()


def decode_tpacket(b_packet):
    """ Decodes a b_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Efficiency by virtue of the KISS principle: ~1750 ns/decode (FX-8350)
    """
    t_decoded = b_packet.decode()
    return float(t_decoded[1:21]), [        # tm
           float(t_decoded[21:37]),         # \
           float(t_decoded[37:53]),         # Bm
           float(t_decoded[53:69]), ], [    # /
           float(t_decoded[69:81]),         # \
           float(t_decoded[81:93]),         # Im
           float(t_decoded[93:105]), ], [   # /
           float(t_decoded[105:117]),       # \
           float(t_decoded[117:129]),       # Ic
           float(t_decoded[129:141]), ], [  # /
           float(t_decoded[141:153]),       # \
           float(t_decoded[153:165]),       # Vc
           float(t_decoded[165:177]), ], [  # /
           float(t_decoded[177:189]),       # \
           float(t_decoded[189:201]),       # Vvc
           float(t_decoded[201:213]), ], [  # /
           float(t_decoded[213:225]),       # \
           float(t_decoded[225:237]),       # Vcc
           float(t_decoded[237:249]), ]     # /


# def decode_tpacket_2(b_packet):
#     """ Decodes a b_packet, which has the following anatomy:
#     b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)
#
#     Efficiency by virtue of the KISS principle: ~1750 ns/decode (FX-8350)
#     """
#     b_decoded = b_packet.decode()
#     b_array = array([
#         b_decoded[1:21],
#         b_decoded[21:37],
#         b_decoded[37:53],
#         b_decoded[53:69], # Im
#         b_decoded[69:81],
#         b_decoded[81:93],
#         b_decoded[93:105],  # Ic
#         b_decoded[105:117],
#         b_decoded[117:129],
#         b_decoded[129:141], # Vc
#         b_decoded[141:153],
#         b_decoded[153:165],
#         b_decoded[165:177],  # Vvc
#         b_decoded[177:189],
#         b_decoded[189:201],
#         b_decoded[201:213],  # Vcc
#         b_decoded[213:225],
#         b_decoded[225:237],
#         b_decoded[237:249],
#     ], dtype=float)
#     return (
#         b_array[0],
#         [b_array[1], b_array[2], b_array[3]],
#         [b_array[4], b_array[5], b_array[6]],
#         [b_array[7], b_array[8], b_array[9]],
#         [b_array[10], b_array[11], b_array[12]],
#         [b_array[13], b_array[14], b_array[15]],
#         [b_array[16], b_array[17], b_array[18]],
#     )

o0 = encode_tpacket(tm, Bm, Im, Ic, Vc, Vvc, Vcc)

o1 = decode_tpacket(o0)

print(o0)

for i in range(7):
    if i == 0:
        print(str(in0[i]), str(o1[i]))
    else:
        for j in range(3):
            print(str(in0[i][j]), str(o1[i][j]))


# o1 = encode_tpacket_1(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o2 = encode_tpacket_2(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o3 = encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)
# o4 = encode_tpacket_3(tm, Bm, Im, Ic, Vc, Vvc, Vcc)

# for thing in (o1, o2, o3, o4, o1 == o2, o2 == o3):
#     print(thing)



n = int(2E4)
tmult = int(1E6)

print(f"encode_tpacket (n={'{:1.0E}'.format(n)}):",
      round(timeit('encode_tpacket(tm, Bm, Im, Ic, Vc, Vvc, Vcc)',
                   globals=globals(), number=n)*tmult/n, 3), "us")


print(f"decode_tpacket (n={'{:1.0E}'.format(n)}):",
      round(timeit('decode_tpacket(o0)',
                   globals=globals(), number=n)*tmult/n, 3), "us")
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