from time import time, sleep
from datetime import datetime
from numpy.random import random
from timeit import timeit

from threading import Thread


from scc2 import SCC

msg1 = ("eTest!"+"a"*150+"@"*100).encode()


import socket



# control_vals = [[1.0, 2.0, 3.0], [0.1, 0.2, 0.3], [60.1, 60.2, 60.3]]
# control_vals2 = [1.0, 2.0, 3.0, 0.1, 0.2, 0.3, 60.1, 60.2, 60.3]
#
# def test(vals):
#     return ",".join([str(item) for row in vals for item in row])
#
# def test2(vals):
#     return ",".join([str(val) for val in vals])
#
#
# control_vals_string = test(control_vals)
# print(test(control_vals))
# print(test2(control_vals2))

# msg1_dec = msg1.decode()

# print(msg1.decode()[1:].rstrip("@"))
#
# print(msg1.decode()[1:msg1.decode().find("@")])
#
# print(msg1_dec[1:msg1_dec.find("@")])

# setup = """
# t = time()
# """
#
# v1 = """
# msg1.decode().rstrip("@")
# """
#
# v2 = """
# msg1.decode()[1:msg1.decode().find("@")]
# """
#
# v3 = """
# msg1_dec = msg1.decode()
# msg1_dec[1:msg1_dec.find("@")]
# """
#
# def my_round(number, ndigits=0):
#     p = 10**ndigits
#     return (number * p * 2 + 1) // 2 / p


tmult = int(1E6)
n = int(1E5)


# print("t_avg:", round(timeit(stmt=v1, setup=setup,
#                              globals=globals(), number=n)
#                       * tmult / n, 3), "us")
#
# print("t_avg:", round(timeit(stmt=v2, setup=setup,
#                              globals=globals(), number=n)
#                       * tmult / n, 3), "us")

# print("t_avg:", round(timeit(stmt=v3, setup=setup,
#                              globals=globals(), number=n)
#                       * tmult / n, 3), "us")

# print("t_avg:", round(timeit('encode_bpacketB(Bm)', globals=globals(), number=n) * tmult / n, 3), "us")



