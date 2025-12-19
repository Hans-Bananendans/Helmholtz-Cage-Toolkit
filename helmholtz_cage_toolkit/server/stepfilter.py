""" test_eval

We found that within the measured Bm data there is odd regions where the
error grows by about 1 uT sporadically, and then goes back a while later.
This has a massive effect on pointing error, so let's see if we can filter
it out to find out how big of an effect exactly.

By sampling some of the step transients, we find something like this:
step error amplitude: ~1 uT
rising time: ~200 ms for the main linear part
falling time: ~200 ms for the main linear part

If the sample rate is 20 S/s, we are looking for events where for at least
thee samples, the slew rate of the error is +/- 5 uT/s

A crude method to filter these out would be:
 - Detect first edge. If error is larger in magnitude than before, it was a rising edge
 - If its a falling edge, ignore it, we only want to process rising-falling pairs
 - Remember the sample number of the start of the edge and 20 ms of samples further
    We'll call these e1_start and e1_end.
 - Detect second edge, also note the sample numbers of beginning and end.
    These will be e2_start and e2_end.
 - Calculate vertical shift between e1_start and e1_end.
 - For all samples between e1_end and e2_start, subtract this vertical shift
 - For samples between e1_start and e1_end, linear interpolation (constant)
 - For samples between e2_start and e2_end, linear interpolation
 - Increment the sample iterator by e2_end - e1_start - 1 samples

"""

# Imports
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from copy import deepcopy

def load_data(filename, verbose=True):
    skip_start = 0.5
    do_delay_correction = True

    data = np.genfromtxt(filename, delimiter=',', names=True)

    # Remove trailing zero entries
    if data["t"][-1] == 0:
        # len0 = len(data["t"])
        i = 1
        while data["t"][i] != 0:
            i += 1
        n_zerolines = len(data["t"]) - i
        print(f"Truncating {n_zerolines} zero lines from the end")
        data = np.genfromtxt(filename, delimiter=",", names=True, skip_footer=n_zerolines)

    # Measure sample time in dataset
    sample_time = np.mean(data["t"][1:8] - data["t"][0:7])
    assert (sample_time > 0.0)

    if do_delay_correction:
        # Implement command delay by measuring the sample rate and shifting by ~150 ms equivalent
        csd_float = np.round(0.150 / sample_time)
        csd = int(csd_float)
        print(f"Found sample rate of {np.round(1/sample_time, 2)} S/s")
        print(f"Correcting propagation delay by shifting Bc data by {csd_float} -> {csd} samples")
        # Shift Bc data
        data["Bcx"][csd:] = data["Bcx"][:-csd]
        data["Bcy"][csd:] = data["Bcy"][:-csd]
        data["Bcz"][csd:] = data["Bcz"][:-csd]
        data = data[:-csd]
    else:
        print("Skipping propagation delay correction...")

    if skip_start > 0:
        samples_to_skip = int(np.round(skip_start / sample_time))
        print(f"Discarding first {samples_to_skip} samples to filter start-up transients")
        data = data[samples_to_skip:]

    if verbose:
        print(f"steps = {len(data['t'])}")
        print(f"t length = {np.round(data['t'][-1], 1)} s")
        print(f"Bcx steps = {len(data['Bcx'])}   (last: {data['Bcx'][-1]} uT)")
        print(f"Bcy steps = {len(data['Bcy'])}   (last: {data['Bcy'][-1]} uT)")
        print(f"Bcz steps = {len(data['Bcz'])}   (last: {data['Bcz'][-1]} uT)")
        print(f"Bmx steps = {len(data['Bmx'])}   (last: {data['Bmx'][-1]} uT)")
        print(f"Bmy steps = {len(data['Bmy'])}   (last: {data['Bmy'][-1]} uT)")
        print(f"Bmz steps = {len(data['Bmz'])}   (last: {data['Bmz'][-1]} uT)\n")

    return data, 1/sample_time

verbose = False

ramp_width = 0.2
dt_detect = np.array([3.5, 2.8, 10])            # [uT/s] slew rate to detect

filename = "TS_orbit1_2_202511211327_FIX.dat"
# filename = "TS_orbit1_2_OUT.dat"

data, sr = load_data(filename, verbose=verbose)

# print("data.dtypes", data.dtypes)
# print("data.names", data.names)

print(data.shape)
print(data.dtype)

# Optional: crop data
# data = data[:][0:2500]

dt_window = int(np.round((ramp_width * sr)))
if verbose: print(f"Set dt window to {dt_window}")


Ecabs = np.array([
    data["Bmx"] - data["Bcx"],
    data["Bmy"] - data["Bcy"],
    data["Bmz"] - data["Bcz"],
])

# Windowed derivative of relative error
Ecabs_dt = np.zeros_like(Ecabs)
for axis in range(3):
    for i in range(0, len(data["t"])-dt_window):
        Ecabs_dt[axis][i] = (Ecabs[axis][i+dt_window]-Ecabs[axis][i]) / (data["t"][i+dt_window]-data["t"][i])

# # Optional: shift
# shift = 2
# for axis in range(3):
#     Ecabs_dt[axis][shift:] = Ecabs_dt[axis][:-shift]

# Ecabs_ddt2 = np.zeros_like(Ecabs)
# # Ecabs_spk = np.zeros_like(Ecabs)
# for axis in range(3):
#     for i in range(0, len(Ecabs_dt[0])-dt_window):
#         Ecabs_ddt2[axis][i] = ((Ecabs_dt[axis][i+dt_window]-Ecabs_dt[axis][i]) / (data["t"][i+dt_window]-data["t"][i]))**2
    # for i in range(0, len(Ecabs_dt[0])-dt_window):
    #     Ecabs_spk[axis][i] = 0
    #     for j in range(dt_window):
    #         Ecabs_spk[axis][i] += Ecabs_dt[axis][i+j]

vDetect = np.zeros_like(Ecabs)

Bm = np.array([data["Bmx"], data["Bmy"], data["Bmz"]])
Bm_f = deepcopy(Bm)

for axis in range(3):
    rising = False
    falling = False
    i = 0
    while i < len(data["t"]-1):
        if np.abs(Ecabs_dt[axis][i]**2) >= dt_detect[axis]**2:
            v1_start = i
            v1_end = i + dt_window
            if verbose: print(f"v1_start, v1_end = {v1_start},  {v1_end}")
            # Is it rising edge (absolute error became larger):
            rising = np.abs(Ecabs[axis][v1_end]) > np.abs(Ecabs[axis][v1_start])

            if not rising:  # Ignore and skip a few samples
                i += dt_window
                if verbose: print(f"{v1_start} -> not rising")
            else:           # Try to detect falling edge:
                for j in range(v1_end + 10, len(data["t"]-1)):
                    if np.abs(Ecabs_dt[axis][j] ** 2) >= dt_detect[axis] ** 2:
                        # print(f"np.abs(Ecabs_dt[axis][i] ** 2: {np.abs(Ecabs_dt[axis][i] ** 2)}")
                        # print(f"dt_detect ** 2: {dt_detect[axis] ** 2}")
                        v2_start = j
                        v2_end = j + dt_window
                        if verbose: print(f"v2_start, v2_end = {v2_start},  {v2_end}")
                        falling = np.abs(Ecabs[axis][v2_start]) > np.abs(Ecabs[axis][v2_end])

                        if not falling:
                            if verbose: print(f"Anomaly: double rising edge detected ({v1_start} and {v2_start}")

                            break
                        else:

                            vDetect[axis][v1_start:v2_end] = 1
                            vDetect[axis][v1_end:v2_start] = 2
                            vDetect[axis][v1_start] = 4
                            vDetect[axis][v1_end] = 4
                            vDetect[axis][v2_start] = 4
                            vDetect[axis][v2_end] = 4

                            jump = Ecabs[axis][v1_end] - Ecabs[axis][v1_start]
                            Bm_f[axis][v1_end:v2_start] = Bm[axis][v1_end:v2_start] - jump

                            for itp in range(v1_end - v1_start + 1):
                                ki = v1_start + itp
                                Bm_f[axis][ki] = Bm[axis][v1_start] + itp/(v1_end - v1_start + 2) * (Bm_f[axis][v1_end+1] - Bm[axis][v1_start-1])
                                # print(f"{Bm[axis][v1_start]} + {itp/(v1_end - v1_start + 2)} * {(Bm_f[axis][v1_end+1] - Bm[axis][v1_start-1])} = {Bm_f[axis][ki]}")
                            for itp in range(v2_end - v2_start + 1):
                                ki = v2_start + itp
                                Bm_f[axis][ki] = Bm_f[axis][v2_start-1] + itp / (v2_end - v2_start + 2) * (Bm[axis][v2_end+1] - Bm_f[axis][v2_start-1])
                            break

        i += 1

# Offset correction
Ecabs_f = np.array([
    Bm_f[0] - data["Bcx"],
    Bm_f[1] - data["Bcy"],
    Bm_f[2] - data["Bcz"],
])

Ecabs_f_mean = np.array([
    np.mean(Ecabs_f[0]),
    np.mean(Ecabs_f[1]),
    np.mean(Ecabs_f[2]),
])
print(f"Ecabs_f_mean before correction: {Ecabs_f_mean}")

Bm_f[0] = Bm_f[0] - Ecabs_f_mean[0]
Bm_f[1] = Bm_f[1] - Ecabs_f_mean[1]
Bm_f[2] = Bm_f[2] - Ecabs_f_mean[2]

Ecabs_f = np.array([
    Bm_f[0] - data["Bcx"],
    Bm_f[1] - data["Bcy"],
    Bm_f[2] - data["Bcz"],
])

Ecabs_f_mean = np.array([
    np.mean(Ecabs_f[0]),
    np.mean(Ecabs_f[1]),
    np.mean(Ecabs_f[2]),
])

print(f"Ecabs_f_mean after correction: {Ecabs_f_mean}")



# Factor correction
# Bm_f[0] = Bm_f[0] / (20/20 * data["Bcx"]/max(data["Bcx"]))
# Bm_f[1] = Bm_f[1] / (30/30 * data["Bcy"]/max(data["Bcy"]))
# Bm_f[2] = Bm_f[2] / (30/30 * data["Bcz"]/max(data["Bcz"]))


fig, axs = plt.subplots(3, 1, figsize=(18,8))
for axis in range(3):
    axs[axis].grid(True)
    axs[axis].set_ylabel(f"Ec {('X', 'Y', 'Z')[axis]} [uT]")
axs[2].set_xlabel("t [s]")

axs[0].plot(data["t"], Ecabs[0], "r", alpha=0.5)
axs[1].plot(data["t"], Ecabs[1], "g", alpha=0.5)
axs[2].plot(data["t"], Ecabs[2], "b", alpha=0.5)

axs[0].plot(data["t"], Ecabs_f[0], "r", alpha=1)
axs[1].plot(data["t"], Ecabs_f[1], "g", alpha=1)
axs[2].plot(data["t"], Ecabs_f[2], "b", alpha=1)

# axs[0].plot(data["t"], Bm[0], "r", alpha=0.5)
# axs[1].plot(data["t"], Bm[1], "g", alpha=0.5)
# axs[2].plot(data["t"], Bm[2], "b", alpha=0.5)
#
# axs[0].plot(data["t"], Bm_f[0], "r", alpha=1)
# axs[1].plot(data["t"], Bm_f[1], "g", alpha=1)
# axs[2].plot(data["t"], Bm_f[2], "b", alpha=1)

# axs[0].plot(data["t"], Ecabs_dt[0], "r:", alpha=0.5)
# axs[1].plot(data["t"], Ecabs_dt[1], "g:", alpha=0.5)
# axs[2].plot(data["t"], Ecabs_dt[2], "b:", alpha=0.5)
#
axs[0].plot(data["t"], Ecabs_dt[0]**2/10, "r:", alpha=1)
axs[1].plot(data["t"], Ecabs_dt[1]**2/10, "g:", alpha=1)
axs[2].plot(data["t"], Ecabs_dt[2]**2/10, "b:", alpha=1)

axs[0].scatter(data["t"], vDetect[0], s=2, c="k")
axs[1].scatter(data["t"], vDetect[1], s=2, c="k")
axs[2].scatter(data["t"], vDetect[2], s=2, c="k")

plt.show()


data["Bmx"] = Bm_f[0]
data["Bmy"] = Bm_f[1]
data["Bmz"] = Bm_f[2]

header = ["t", "Icx", "Icy", "Icz", "Bmx", "Bmy", "Bmz", "Bcx", "Bcy", "Bcz"]

# filename_new = filename[:-4] + "_STEPFIX.dat"
# with open(filename_new, "w") as file:
#     file.write(",".join(header) + "\n")
# with open(filename_new, "a") as file:
#     np.savetxt(file, np.array(data).transpose(), fmt="%f", delimiter=",")


def doDataAnalysis(self):
    sample_time = np.mean(data["t"][1:8] - data["t"][0:7])

    # Bcdot = np.array([
    #
    # ])

    Ecabs = np.array([
        data["Bmx"] - data["Bcx"],
        data["Bmy"] - data["Bcy"],
        data["Bmz"] - data["Bcz"],
    ])
    Ecrel = np.array([
        100 * Ecabs[0] / data["Bcx"],
        100 * Ecabs[1] / data["Bcy"],
        100 * Ecabs[2] / data["Bcz"],
    ])

    Ecmag = np.sqrt(Ecabs[0]**2 + Ecabs[1]**2 + Ecabs[2]**2)
    # meanEcabs = [
    #     float(round(np.mean(np.sqrt(Ecabs[0]**2)), 3)),
    #     float(round(np.mean(np.sqrt(Ecabs[1]**2)), 3)),
    #     float(round(np.mean(np.sqrt(Ecabs[2]**2)), 3)),
    # ]
    Ecabsmax = max(Ecmag)
    Ecabsmaxs = [
        float(round(max(np.abs(Ecabs[0])), 3)),
        float(round(max(np.abs(Ecabs[1])), 3)),
        float(round(max(np.abs(Ecabs[2])), 3)),
    ]
    Erms = np.array([
        float(round(np.sqrt(np.mean(Ecabs[0] ** 2)), 3)),
        float(round(np.sqrt(np.mean(Ecabs[1] ** 2)), 3)),
        float(round(np.sqrt(np.mean(Ecabs[2] ** 2)), 3)),
    ])
    Ecnorm = Ecmag / Ecabsmax
    print(f"Max absolute error (x/y/z):     {Ecabsmaxs[0]} / {Ecabsmaxs[1]} / {Ecabsmaxs[2]}  ({round(Ecabsmax,3)}) \u03BCT")
    # print(f"Max absolute error:             {round(Ecabsmax,3)} \u03BCT")
    # print(f"Mean absolute error (x/y/z):    {meanEcabs[0], meanEcabs[1], meanEcabs[2]} \u03BCT")
    # print(f"Mean absolute error:            {round(np.mean(Ecmag), 3)} \u03BCT")
    print(f"RMS error (x/y/z):              {Erms[0]} / {Erms[1]} / {Erms[2]}  ({round(np.mean(Erms), 3)}) \u03BCT")
    # print(f"RMS error:                      {round(np.mean(Erms), 3)} \u03BCT")

    Eangle = np.empty_like(Ecmag)
    for i in range(len(Eangle)):
        vc = np.array([data["Bcx"][i], data["Bcy"][i], data["Bcz"][i]])
        vm = np.array([data["Bmx"][i], data["Bmy"][i], data["Bmz"][i]])
        vdot = np.dot(vc / np.linalg.norm(vc), vm / np.linalg.norm(vm))
        Eangle[i] = 180 / np.pi * np.arccos(vdot)
    Eanglemax = max(Eangle)
    Eanglerms = np.sqrt(np.mean(np.square(Eangle)))

    print(f"Max angle error:                {float(round(Eanglemax,3))}\u00B0")
    print(f"RMS angle error:                {float(round(Eanglerms,3))}\u00B0")


