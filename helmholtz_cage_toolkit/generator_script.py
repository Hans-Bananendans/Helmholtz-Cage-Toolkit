from time import time
from timeit import timeit
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from scipy.signal import (
    chirp,
    gausspulse,
    sawtooth,
    square,
    unit_impulse
)


from helmholtz_cage_toolkit.file_handling import (
    make_schedule,
    write_bsch_file,
    initialize_bsch_file,
    generate_header
)

# ================================================================
# ============================ INPUTS ============================

# Type the name of the schedule here:
schedulename = "schedule3"

# If <filename> is None, the name of the schedule file will be
# <schedulename>.bsch. If you want it to be something else, you
# can specify it here, and it will be <filename>.bsch instead.
filename = None

# Schedule sample rate [S/s]
sample_rate = 20

# Schedule duration [s]
schedule_duration = 62

# Make a plot of result?
do_plot = True

# Overwrite file with same name if it already exists?
do_overwrite = True

# ----- Automation -----
t = np.arange(0, schedule_duration + 1/sample_rate, 1/sample_rate)

# ================================================================
# ===================== DEFINE Bc(t) HERE ========================


# Bcx = 150 * chirp(t, 0.035, 62, 0.5, phi=-90, method="logarithmic")
# Bcy = 150 * chirp(t, 0.055, 62, 0.5, phi=-90, method="logarithmic")
# Bcz = 150 * chirp(t, 0.085, 62, 0.5, phi=-90, method="logarithmic")

# sd = schedule_duration/2
# Bcx = (3*t-sd*1.5) * np.sin(0.9*t)
# Bcy = (3*t-sd*3.0) * np.sin(1.2*t)
# Bcz = (3*t-sd*4.5) * np.sin(1.35*t)

Bcx = 100 * chirp(t, 0.035, 62, 0.5, phi=-90, method="logarithmic")
Bcy = 100 * chirp(t, 0.055, 62, 0.5, phi=-90, method="logarithmic")
Bcz = 100 * chirp(t, 0.085, 62, 0.5, phi=-90, method="logarithmic")

# ================================================================
# ----- Automation -----
Bc = np.array([Bcx, Bcy, Bcz])

schedule = make_schedule(t, Bc).transpose()

if not filename:
    filename = schedulename
filename += ".bsch"

header_string = generate_header(
    filename,
    'none',
    None,
    None
)

initialize_bsch_file(filename, header_string, overwrite=do_overwrite)
write_bsch_file(filename, schedule)

if do_plot:
    fig, axs = plt.subplots(3, 1, figsize=(18, 8))
    for axis in range(3):
        axs[axis].grid(True)
        axs[axis].set_ylabel(f"Bc {('X', 'Y', 'Z')[axis]} [uT]")
    axs[2].set_xlabel("t [s]")

    axs[0].plot(t, Bcx, "r", alpha=1)
    axs[1].plot(t, Bcy, "g", alpha=1)
    axs[2].plot(t, Bcz, "b", alpha=1)

    plt.show()