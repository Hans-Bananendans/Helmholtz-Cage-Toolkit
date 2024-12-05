import hashlib
from numpy import array
from time import time
from timeit import timeit
import numpy as np
from collections import deque

tm = 1705321618.6226978
i_step = 1_234_567_890
Bm = [-12345.12345, -12345.23456, -12345.34567]
Bc = [-92345.12345, -82345.23456, -72345.34567]
Im = [1234.1234, 1234.2345, 1234.3456]
Ic = [-41.039767666050004, -86.828165545449992, 27.42272022095]
Vc = [60.11111111111, 60.2222222222222, 60.3333333333333]
Vvc = [1.101, 1.202, 1.303]
Vcc = [2.101, 2.202, 2.303]

in0 = [tm, Bm, Im, Ic, Vc, Vvc, Vcc]

_pad = "#"

seg_test = [35, 60, 355.932203, -83331.392, -55280.007, 18644.068]


def f1(x, item):
    return [item] + x[:-1]

def f2(x, item):
    x.insert(0, item)
    x.pop()
    return x

def f3(x, item):
    x.pop()
    x.insert(0, item)
    return x

def f4(x, item):
    del x[-1]
    x.insert(0, item)
    return x

def f5(x, item):
    x.insert(0, item)
    del x[-1]
    return x

def f9(x, item):
    x.appendleft(item)
    return x



# Generate list of lists of random values
# Bm = ((100*np.random.rand(1024, 3)).round(3)).tolist()
# Bmdeque = deque(Bm, len(Bm))


# print("Bm:")
# for item in Bm:
#     print(item)



item = [1.0, 1.0, 1.0]

# print(f1(Bm, item))
# print(f2(Bm, item))
# print(list(f3(Bmdeque, item)))
# print(return_n(Bm, 4))
# print(return_n_deque(Bmdeque, 4))



def encode_tpacket(tm, i_step, Im, Bm, Bc):
    """ Encodes a t_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    i_step (32 B)    Im (3x12 B)
               Bm (3x16 B)         Bc (3x16 B)      padding (71 B)
    TODO RE-BENCHMARK
    Optimization: 9398 ns/encode (FX-8350)
    """
    output = [str(tm), str(i_step), ]
    for par in (Im, Bm, Bc):
        output += [str(par[0]), str(par[1]), str(par[2])]
    return ("t{:0<20.20}"+"{:0>32.32}"+"{:0<12.12}"*3+"{:0<16.16}"*6+"#"*71
            ).format(*output).encode()


def decode_tpacket(t_packet):
    """ Decodes a t_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    i_step (32 B)    Im (3x12 B)
               Bm (3x16 B)         Bc (3x16 B)      padding (71 B)
    Optimization: 3597 ns/encode (FX-8350)
    """
    t_decoded = t_packet.decode()
    return float(t_decoded[1:21]), \
        int(t_decoded[21:53]), \
        [
            float(t_decoded[53:65]),        # \
            float(t_decoded[65:77]),        # Im
            float(t_decoded[77:89]),        # /
        ], [
            float(t_decoded[89:105]),        # \
            float(t_decoded[105:121]),        # Bm
            float(t_decoded[121:137]),       # /
        ], [
            float(t_decoded[137:153]),      # \
            float(t_decoded[153:169]),      # Bc
            float(t_decoded[169:185]),      # /
        ]





t_packet = encode_tpacket(tm, i_step, Im, Bm, Bc)

tm2, i_step2, Im2, Bm2, Bc2 = decode_tpacket(t_packet)

print(t_packet)
print(len(t_packet))

for pair in [[tm, tm2], [i_step, i_step2], [Im, Im2], [Bm, Bm2], [Bc, Bc2]]:
    if pair[0] == pair[1]:
        print("PASS: ", pair[0], pair[1])
    else:
        print("FAIL: ", pair[0], pair[1])




n = int(1E6)
tmult = int(1E6)
tunit = "us"

# print(f"f1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f1(Bm, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
# print(f"f2 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f2(Bm, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
# print(f"f3 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f3(Bm, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
# print(f"f4 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f4(Bm, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
# print(f"f5 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f5(Bm, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
# print(f"f9 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('f9(Bmdeque, item)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)


# print(f"encode_spacket0 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_spacket0(*seg_test)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)
#
# print(f"encode_spacket1 (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_spacket1(*seg_test)',
#                    globals=globals(), number=n)*tmult/n, 3), tunit)



print(f"encode_tpacket (n={'{:1.0E}'.format(n)}):",
      round(timeit('encode_tpacket(tm, i_step, Im, Bm, Bc)',
                   globals=globals(), number=n)*tmult/n, 3), "us")


print(f"decode_tpacket (n={'{:1.0E}'.format(n)}):",
      round(timeit('decode_tpacket(t_packet)',
                   globals=globals(), number=n)*tmult/n, 3), "us")



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