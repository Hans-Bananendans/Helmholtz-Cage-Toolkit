import numpy as np
from numpy import sin, cos, arccos, dot, array, ndarray, pi
from time import time
from timeit import timeit




# print(f"Unit vector `X`: [{R_ecef_ned[:,0].round(3)}]")
# print(f"Unit vector `Y`: [{R_ecef_ned[:,1].round(3)}]")
# print(f"Unit vector `Z`: [{R_ecef_ned[:,2].round(3)}]")
#
# p1_NED = (p1_ECEF - O_NED) @ R_ecef_ned.transpose()
#
# print(p1_NED)
#
# a1, a2 = pi/3, pi/5
# test1 = np.array([3, 4, 5])
# test1_t = R_ECEF_NED2(a1, a2)@test1
# test1_back = R_ECEF_NED2(a1, a2).transpose()@test1_t
#
# print(f"test1     : {test1}")
# print(f"test1_t   : {test1_t}")
# print(f"test1_back: {test1_back}")


# res1 = p0_ECEF@R_ECEF_NED(lat, long) + offset
# res2 = p0_ECEF@R_sanity(lat, long) + offset
#
# print(f"Result 1: {res1.round(3)}")
# print(f"Result 2: {res2.round(3)}")


