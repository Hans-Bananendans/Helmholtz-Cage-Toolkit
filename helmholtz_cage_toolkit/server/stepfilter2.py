""" stepfilter2.py

Since the strange step error is correlated to the

"""

# Imports
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, symiirorder1
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
from copy import deepcopy

def load_data(filename, verbose=True):
    skip_start = 0.6
    command_delay = 0.100

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

    if command_delay > 0:
        # Implement command delay by measuring the sample rate and shifting by ~150 ms equivalent
        csd_float = np.round(command_delay / sample_time)
        csd = int(csd_float)
        print(f"Found sample rate of {np.round(1/sample_time, 2)} S/s")
        print(f"Correcting propagation delay by shifting Bc data by {csd_float} -> {csd} samples")
        # Shift Bc data
        data["Bcx"][csd:] = data["Bcx"][:-csd]
        data["Bcy"][csd:] = data["Bcy"][:-csd]
        data["Bcz"][csd:] = data["Bcz"][:-csd]
        data["Icx"][csd:] = data["Icx"][:-csd]
        data["Icy"][csd:] = data["Icy"][:-csd]
        data["Icz"][csd:] = data["Icz"][:-csd]
        data["polx"][csd:] = data["polx"][:-csd]
        data["poly"][csd:] = data["poly"][:-csd]
        data["polz"][csd:] = data["polz"][:-csd]
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

def calc_error(_Bc, _Bm, msg="Errors"):
    Ecabs = np.array([
        _Bm[0] - _Bc[0],
        _Bm[1] - _Bc[1],
        _Bm[2] - _Bc[2]
    ])

    Ecmag = np.sqrt(Ecabs[0] ** 2 + Ecabs[1] ** 2 + Ecabs[2] ** 2)

    Ecabsmax = max(Ecmag)
    Ecabsmaxs = [
        float(round(max(np.abs(Ecabs[0])), 3)),
        float(round(max(np.abs(Ecabs[1])), 3)),
        float(round(max(np.abs(Ecabs[2])), 3)),
    ]
    Erms_xyz = np.array([
        float(round(np.sqrt(np.mean(Ecabs[0] ** 2)), 3)),
        float(round(np.sqrt(np.mean(Ecabs[1] ** 2)), 3)),
        float(round(np.sqrt(np.mean(Ecabs[2] ** 2)), 3)),
    ])

    Erms = np.sqrt(Erms_xyz[0]**2 + Erms_xyz[1]**2 + Erms_xyz[2]**2)

    print(f"\n{msg}")
    print(
        f"Max error (x/y/z):    {Ecabsmaxs[0]} / {Ecabsmaxs[1]} / {Ecabsmaxs[2]}  ({round(Ecabsmax, 3)}) \u03BCT")
    print(
        f"RMS error (x/y/z):    {Erms_xyz[0]} / {Erms_xyz[1]} / {Erms_xyz[2]}  ({round(Erms, 3)}) \u03BCT")

    Eangle = np.empty_like(Ecmag)
    for i in range(len(Eangle)):
        vc = np.array([_Bc[0][i], _Bc[1][i], _Bc[2][i]])
        vm = np.array([_Bm[0][i], _Bm[1][i], _Bc[2][i]])
        vdot = np.dot(vc / np.linalg.norm(vc), vm / np.linalg.norm(vm))
        Eangle[i] = 180 / np.pi * np.arccos(vdot)
    Eanglemax = max(Eangle)
    Eanglerms = np.sqrt(np.mean(np.square(Eangle)))

    print(f"Max angle error:    {float(round(Eanglemax, 3))}\u00B0")
    print(f"RMS angle error:    {float(round(Eanglerms, 3))}\u00B0")

    return round(Erms, 3), Ecabsmax, float(round(Eanglerms, 3)), Eanglemax


verbose = False

ramp_width = 0.2
dt_detect = np.array([3.5, 2.8, 10])            # [uT/s] slew rate to detect

# filename = "TS_orbit1_2_202511211327_FIX.dat"
# filename = "TS_orbit2_202511211346.dat"
# filename = "TS_orbit3_202511211355_FIX.dat" # BAD
# filename = "TS_orbit4_202511211417_FIX.dat" # BAD
# filename = "TS_orbit5_202511211512_FIX.dat"
# filename = "TS_orbit6_202511211603_FIX.dat"
# filename = "TS_orbit7_20251125_FIX.dat"
# filename = "TS_orbit8_20251125_FIX.dat"
# filename = "TS_orbit9_20251125_FIX.dat"
# filename = "TS_orbit10_20251125_FIX.dat"

# filename = "schedule1_202511211615.dat"   # BAD
# filename = "schedule2_202511211619.dat"   # BAD
filename = "schedule3_202511211626.dat"   # BAD

data, sr = load_data(filename, verbose=verbose)

# print("data.dtypes", data.dtypes)
# print("data.names", data.names)

# print(data.shape)
# print(data.dtype)

# Optional: crop data
# data = data[:][0:2500]

dt_window = int(np.round((ramp_width * sr)))
if verbose: print(f"Set dt window to {dt_window}")


Ecabs = np.array([
    data["Bmx"] - data["Bcx"],
    data["Bmy"] - data["Bcy"],
    data["Bmz"] - data["Bcz"],
])


vDetect = np.zeros_like(Ecabs)

Bc = np.array([data["Bcx"], data["Bcy"], data["Bcz"]])
Bm = np.array([data["Bmx"], data["Bmy"], data["Bmz"]])


Eabsrms0, Eabsmax0, Eanglerms0, Eanglemax0 = calc_error(Bc, Bm, msg="Raw errors")

Bm_f = deepcopy(Bm)

Bm_f[0] = data["Bmx"] - 1.0 * (data["polx"] - 1)/2
Bm_f[1] = data["Bmy"] - 1.0 * (data["poly"] - 1)/2
Bm_f[2] = data["Bmz"] - 1.0 * (data["polz"] - 1)/2

calc_error(Bc, Bm_f, msg="Errors after correcting steps")

pol = np.array([data["polx"], data["poly"], data["polz"]])

# Second pass to filter out spikes
back_samples = 5
for axis in range(3):
    for i in range(1, len(data["t"]-1)):
        p_1 = np.round(pol[axis][i-1])
        p0 = np.round(pol[axis][i])
        if ((p_1 == -1 and p0 == 1) or (p_1 == 1 and p0 == -1)) and i > back_samples:
            avg_spike = np.mean(Bm_f[axis][i-back_samples:i-1])
            avg_edge = (Bm_f[axis][i-back_samples-1] + Bm_f[axis][i+1])/2
            Bm_f[axis][i - back_samples:i] = 0.05*(Bm_f[axis][i - back_samples:i] - avg_spike) + avg_edge
            # Bm_f[axis][i - back_samples:i - 1] -= avg_spike     # Subtract average of spike value
            # Bm_f[axis][i - back_samples:i - 1] *= 0.1           # Compress
            # Bm_f[axis][i - back_samples:i - 1] += avg_edge      # Add average of boundaries

calc_error(Bc, Bm_f, msg="Errors after smoothing spikes")


# Offset correction
Ecabs_f = np.array([
    Bm_f[0] - Bc[0],
    Bm_f[1] - Bc[1],
    Bm_f[2] - Bc[2],
])

Ecabs_f_mean = np.array([
    np.mean(Ecabs_f[0]),
    np.mean(Ecabs_f[1]),
    np.mean(Ecabs_f[2]),
])

Bm_f[0] = Bm_f[0] - Ecabs_f_mean[0]
Bm_f[1] = Bm_f[1] - Ecabs_f_mean[1]
Bm_f[2] = Bm_f[2] - Ecabs_f_mean[2]

Ecabs_f = np.array([
    Bm_f[0] - Bc[0],
    Bm_f[1] - Bc[1],
    Bm_f[2] - Bc[2],
])

calc_error(Bc, Bm_f, msg="Errors after removing constant offsets")


# Correlated magnitude correction

Bc_norm = np.array([
    Bc[0]/max(Bc[0]),
    Bc[1]/max(Bc[1]),
    Bc[2]/max(Bc[2]),
])

factor = 0.5
Bm_f[0] = Bm_f[0] - (factor * Bc_norm[0])
Bm_f[1] = Bm_f[1] - (factor * Bc_norm[1])
Bm_f[2] = Bm_f[2] - (factor * Bc_norm[2])

Ecabs_ff = np.array([
    Bm_f[0] - Bc[0],
    Bm_f[1] - Bc[1],
    Bm_f[2] - Bc[2],
])

# Bm_f[0] = savgol_filter(Bm_f[0], 7, 5)
# Bm_f[1] = savgol_filter(Bm_f[1], 7, 5)
# Bm_f[2] = savgol_filter(Bm_f[2], 7, 5)

# dummy = np.zeros_like(Ecabs_ff)

# dummy[0] = savgol_filter(Ecabs_ff[0], 12, 10)
# dummy[1] = savgol_filter(Ecabs_ff[1], 12, 10)
# dummy[2] = savgol_filter(Ecabs_ff[2], 12, 10)

# dummy[0] = gaussian_filter1d(Ecabs_ff[0], sigma=3)
# dummy[1] = gaussian_filter1d(Ecabs_ff[1], sigma=3)
# dummy[2] = gaussian_filter1d(Ecabs_ff[2], sigma=3)
#
#
# Ecabs_ff = np.array([
#     dummy[0],
#     dummy[1],
#     dummy[2],
# ])
# Ecabs_ff[0] = savgol_filter(Ecabs_ff[0], 12, 10)
# Ecabs_ff[1] = savgol_filter(Ecabs_ff[1], 12, 10)
# Ecabs_ff[2] = savgol_filter(Ecabs_ff[2], 12, 10)

# Ecabs_ff[0] = gaussian_filter1d(Ecabs_ff[0], sigma=3)
# Ecabs_ff[1] = gaussian_filter1d(Ecabs_ff[1], sigma=3)
# Ecabs_ff[2] = gaussian_filter1d(Ecabs_ff[2], sigma=3)

# print(f"Ecabs_f_mean after correction: {Ecabs_f_mean}")


Eabsrms1, Eabsmax1, Eanglerms1, Eanglemax1 = calc_error(Bc, Bm_f, msg="Errors after correlated magnitude correction")

print(f"\nREDUCTIONS ({filename})")
print(f"Max error [\u03BCT]: {round(Eabsmax0,3)} -> {round(Eabsmax1,3)}  (-{round(100-100*Eabsmax1/Eabsmax0,2)}%)")
print(f"RMS error [\u03BCT]: {round(Eabsrms0,3)} -> {round(Eabsrms1,3)}  (-{round(100-100*Eabsrms1/Eabsrms0,2)}%)")
print(f"Max error  [\u00B0]: {round(Eanglemax0,2)} -> {round(Eanglemax1,2)}  (-{round(100-100*Eanglemax1/Eanglemax0,2)}%)")
print(f"RMS error  [\u00B0]: {round(Eanglerms0,2)} -> {round(Eanglerms1,2)}  (-{round(100-100*Eanglerms1/Eanglerms0,2)}%)")

# # Offset correction
# Ecabs_ff_mean = np.array([
#     np.mean(Ecabs_f[0]),
#     np.mean(Ecabs_f[1]),
#     np.mean(Ecabs_f[2]),
# ])
#
# Bm_f[0] = Bm_f[0] - Ecabs_ff_mean[0]
# Bm_f[1] = Bm_f[1] - Ecabs_ff_mean[1]
# Bm_f[2] = Bm_f[2] - Ecabs_ff_mean[2]
#
# Ecabs_fff = np.array([
#     Bm_f[0] - Bc[0],
#     Bm_f[1] - Bc[1],
#     Bm_f[2] - Bc[2],
# ])
#
# calc_error(Bc, Bm_f, msg="Errors after removing offset AGAIN")


# Factor correction
# Bm_f[0] = Bm_f[0] / (20/20 * data["Bcx"]/max(data["Bcx"]))
# Bm_f[1] = Bm_f[1] / (30/30 * data["Bcy"]/max(data["Bcy"]))
# Bm_f[2] = Bm_f[2] / (30/30 * data["Bcz"]/max(data["Bcz"]))


fig, axs = plt.subplots(3, 1, figsize=(18,8))
for axis in range(3):
    axs[axis].grid(True)
    axs[axis].set_ylabel(f"Ec {('X', 'Y', 'Z')[axis]} [uT]")
axs[2].set_xlabel("t [s]")

axs[0].plot(data["t"], Ecabs[0], "r", alpha=0.2)
axs[1].plot(data["t"], Ecabs[1], "g", alpha=0.2)
axs[2].plot(data["t"], Ecabs[2], "#04F", alpha=0.2)

axs[0].plot(data["t"], data["polx"], "r:", alpha=1)
axs[1].plot(data["t"], data["poly"], "g:", alpha=1)
axs[2].plot(data["t"], data["polz"], "#04F", ls=":", alpha=1)

axs[0].plot(data["t"], Ecabs_f[0], "r", alpha=0.4)
axs[1].plot(data["t"], Ecabs_f[1], "g", alpha=0.4)
axs[2].plot(data["t"], Ecabs_f[2], "#04F", alpha=0.4)

axs[0].plot(data["t"], Ecabs_ff[0], "r", alpha=0.8)
axs[1].plot(data["t"], Ecabs_ff[1], "g", alpha=0.8)
axs[2].plot(data["t"], Ecabs_ff[2], "#04F", alpha=0.8)

# axs[0].plot(data["t"], Ecabs_fff[0], "r", alpha=0.8)
# axs[1].plot(data["t"], Ecabs_fff[1], "g", alpha=0.8)
# axs[2].plot(data["t"], Ecabs_fff[2], "b", alpha=0.8)

# axs[0].plot(data["t"], Ecabs_f[0], "r", alpha=1)
# axs[1].plot(data["t"], Ecabs_f[1], "g", alpha=1)
# axs[2].plot(data["t"], Ecabs_f[2], "b", alpha=1)

axs[0].plot(data["t"], Bc[0]/max(Bc[0]), "#000", alpha=1)
axs[1].plot(data["t"], Bc[1]/max(Bc[1]), "#000", alpha=1)
axs[2].plot(data["t"], Bc[2]/max(Bc[2]), "#000", alpha=1)

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
# axs[0].plot(data["t"], Ecabs_dt[0]**2/10, "r:", alpha=1)
# axs[1].plot(data["t"], Ecabs_dt[1]**2/10, "g:", alpha=1)
# axs[2].plot(data["t"], Ecabs_dt[2]**2/10, "b:", alpha=1)
#
# axs[0].scatter(data["t"], vDetect[0], s=2, c="k")
# axs[1].scatter(data["t"], vDetect[1], s=2, c="k")
# axs[2].scatter(data["t"], vDetect[2], s=2, c="k")

plt.show()


data["Bmx"] = Bm_f[0]
data["Bmy"] = Bm_f[1]
data["Bmz"] = Bm_f[2]

header = ["t", "Icx", "Icy", "Icz", "Imx", "Imy", "Imz", "Bcx", "Bcy", "Bcz", "Bmx", "Bmy", "Bmz", "polx", "poly", "polz", "ERROR"]
filename_new = filename[:-4] + "_FILTER2.dat"
with open(filename_new, "w") as file:
    file.write(",".join(header) + "\n")
with open(filename_new, "a") as file:
    np.savetxt(file, np.array(data).transpose(), fmt="%f", delimiter=",")



