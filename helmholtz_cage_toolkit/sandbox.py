import hashlib
from hashlib import blake2b, blake2s
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


n = int(1E3)
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



# print(f"encode_tpacket (n={'{:1.0E}'.format(n)}):",
#       round(timeit('encode_tpacket(tm, i_step, Im, Bm, Bc)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")
#
#
# print(f"decode_tpacket (n={'{:1.0E}'.format(n)}):",
#       round(timeit('decode_tpacket(t_packet)',
#                    globals=globals(), number=n)*tmult/n, 3), "us")






test_schedule = [
    [0, 6, 0.0, 0.0, 0.0, 0.0],
    [1, 6, 3.0, 1.0, 0.0, 0.0],
    [2, 6, 5.0, 2.0, 0.0, 0.0],
    [3, 6, 7.0, 3.0, 0.0, 0.0],
    [4, 6, 9.0, 4.0, 0.0, 0.0],
    [5, 6, 10.0, 0.0, 0.0, 0.0],
]

tsa = array(test_schedule)






def init_buffer_tolist(buffer_size, entry_size, dtype=float):
    """Automatically creates a buffer object, which is a list with a number
    of entries. The number of entries is equal to <buffer_size>.
    The entries themselves are lists if <entry_size> is larger than 1,
    making the buffer 2D. For <entry_size> equal to 1, the buffer will be
    1D instead.
    """
    if buffer_size <= 0:
        raise ValueError(f"init_buffer(): buffer_size cannot be {buffer_size}!")

    if entry_size == 1:
        return np.zeros(buffer_size, dtype=dtype).tolist()
    elif entry_size > 1:
        return np.zeros((buffer_size, entry_size), dtype=dtype).tolist()
    else:
        raise ValueError(f"init_buffer(): Negative entry_size given!")


def init_buffer_list(buffer_size, entry_size, dtype=float):
    """Automatically creates a buffer object, which is a list with a number
    of entries. The number of entries is equal to <buffer_size>.
    The entries themselves are lists if <entry_size> is larger than 1,
    making the buffer 2D. For <entry_size> equal to 1, the buffer will be
    1D instead.
    """
    if buffer_size <= 0:
        raise ValueError(f"init_buffer(): buffer_size cannot be {buffer_size}!")

    if entry_size == 1:
        return list(np.zeros(buffer_size, dtype=dtype))
    elif entry_size > 1:
        return list(np.zeros((buffer_size, entry_size), dtype=dtype))
    else:
        raise ValueError(f"init_buffer(): Negative entry_size given!")

def init_buffer_fixlist(buffer_size, entry_size, dtype=float) -> list:
    """Automatically creates a buffer object, which is a list with a number
    of entries. The number of entries is equal to <buffer_size>.
    The entries themselves are lists if <entry_size> is larger than 1,
    making the buffer 2D. For <entry_size> equal to 1, the buffer will be
    1D instead.
    """
    if buffer_size <= 0:
        raise ValueError(f"init_buffer(): buffer_size cannot be {buffer_size}!")

    if entry_size == 1:
        return list(np.zeros(buffer_size, dtype=dtype).tolist())
    elif entry_size > 1:
        return list(np.zeros((buffer_size, entry_size), dtype=dtype).tolist())
    else:
        raise ValueError(f"init_buffer(): Negative entry_size given!")

print(init_buffer_tolist(10, 1))
print(init_buffer_list(10, 1))
print(init_buffer_fixlist(10, 1))

print(f"tolist() (n={'{:1.0E}'.format(n)}):",
      round(timeit('init_buffer_tolist(1000, 6)',
                   globals=globals(), number=10000)*tmult/n, 3), tunit)

print(f"list(  ) (n={'{:1.0E}'.format(n)}):",
      round(timeit('init_buffer_list(1000, 6)',
                   globals=globals(), number=10000)*tmult/n, 3), tunit)


print(f"listfix(  ) (n={'{:1.0E}'.format(n)}):",
      round(timeit('init_buffer_fixlist(1000, 6)',
                   globals=globals(), number=10000)*tmult/n, 3), tunit)


def calculate_schedule_hash(schedule: list, digest_size=32):
    """Creates a schedule digest using the BLAKE2b algorithm"""
    return blake2b(array(schedule).tobytes(), digest_size=digest_size).hexdigest()

def calculate_schedule_hash2(schedule: list, digest_size=32):
    """Creates a schedule digest using the BLAKE2s algorithm"""
    return blake2s(array(schedule).tobytes(), digest_size=digest_size).hexdigest()
m = 1000

print(calculate_schedule_hash(test_schedule*m, 64))
print(calculate_schedule_hash(test_schedule*m, 32))
print(calculate_schedule_hash(test_schedule*m, 16))
print(calculate_schedule_hash(test_schedule*m, 8))
print(calculate_schedule_hash(test_schedule*m, 4))

print(calculate_schedule_hash2(test_schedule*m, 32))
print(calculate_schedule_hash2(test_schedule*m, 16))
print(calculate_schedule_hash2(test_schedule*m, 8))
print(calculate_schedule_hash2(test_schedule*m, 4))


n = int(1E3)
tmult = int(1E6)
tunit = "us"

print(f"64 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash(test_schedule*m, 64)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"32 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash(test_schedule*m, 32)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"16 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash(test_schedule*m, 16)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"8 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash(test_schedule*m, 8)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"4 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash(test_schedule*m, 4)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)


print(f"s32 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash2(test_schedule*m, 32)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"s16 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash2(test_schedule*m, 16)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"s8 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash2(test_schedule*m, 8)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)
print(f"s4 (n={'{:1.0E}'.format(n)}):",
      round(timeit('calculate_schedule_hash2(test_schedule*m, 4)',
                   globals=globals(), number=n)*tmult/n, 3), tunit)












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

#
# test_schedule = [
#     [0, 6, 0.0, 0.0, 0.0, 0.0],
#     [1, 6, 3.0, 1.0, 0.0, 0.0],
#     [2, 6, 5.0, 2.0, 0.0, 0.0],
#     [3, 6, 7.0, 3.0, 0.0, 0.0],
#     [4, 6, 9.0, 4.0, 0.0, 0.0],
#     [5, 6, 10.0, 0.0, 0.0, 0.0],
# ]
#
# m = 1
#
# t0 = time()
# bshash = hashlib.blake2b(array(test_schedule*m).tobytes(), digest_size=64).digest()
# t1 = time()
# bshash_hex = hashlib.blake2b(array(test_schedule*m).tobytes(), digest_size=64).hexdigest()
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