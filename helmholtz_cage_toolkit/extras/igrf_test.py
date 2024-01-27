import sys
import numpy as np
from time import time

from pyIGRF import igrf_value
from pyIGRF.calculate import igrf12syn

longitude = 60.     # deg (+E)
latitude = 60.      # deg (+N)
altitude = 400.       # km
year = 2020.        # date formatted as decimal year

repetitions = 1
time1 = []
time2 = []
gains = []

t0 = time()

for i in range(repetitions):
    t1 = time()
    d, i, h, x, y, z, f = igrf_value(latitude, longitude, altitude, year)
    t2 = time()
    # x, y, z, f = igrf12syn(year, 1, altitude, latitude, longitude)
    t3 = time()
    time1.append(t2-t1)
    time2.append(t3-t2)
    gains.append(1-(t3-t2)/(t2-t1))


# print("X, Y, Z =  ", round(x,1), round(y,1), round(z,1), "nT (+N, +E, +D)")
print("  X =  ", str(round(x, 1)).rjust(8), "  nT (+N)")
print("  Y =  ", str(round(y, 1)).rjust(8), "  nT (+E)")
print("  Z =  ", str(round(z, 1)).rjust(8), "  nT (+D)")
print("Magnitude   =", round(f, 1), "nT")
print("Declination =", round(d, 4), "deg (+E)")
print("Inclination =", round(i, 4), "deg (+D)")
print("Horizontal  =", round(h, 1), "nT")
print("")
print("Number of repetitions:", repetitions)
print("Average time igrf_value():", round(sum(time1)/len(time1)*1E6, 1), "us")
print("Average time igrf12syn() :", round(sum(time2)/len(time2)*1E6, 1), "us")
print("Gains:", round(100*sum(gains)/len(gains), 1), "%")
print("")
print("Total time", round(time()-t0, 3), "s")