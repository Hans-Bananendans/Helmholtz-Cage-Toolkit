import csv
import numpy as np
import matplotlib.pyplot as plt
from time import time


# ==== INPUT =================================================

# filename = "testdata.csv"
filename = "data.csv"
to_plot = [
    # "Icx",
    # "Icy",
    # "Icz",
    # "Px",
    # "Py",
    # "Pz",
    "Bmx",
    "Bmy",
    "Bmz"
    ]
t_fromzero = True

# ============================================================

t0 = time()

data = np.genfromtxt(filename, delimiter=',', names=True)
colnames = data.dtype.names
ncols = len(data.dtype)
nrows = len(data)


# Normalize time data to 0:
if t_fromzero:
    data["t"] += -min(data["t"])


fig, ax = plt.subplots()

n_plots = 0
for colname in to_plot:
    ax.plot(data["t"], data[colname], label=colname)
    n_plots += 1
   
ax.set_xlabel("t")
ax.legend()

print(f"Generated {n_plots} plots of size {nrows} in {round(1000*(time()-t0),1)} ms")

plt.show()


