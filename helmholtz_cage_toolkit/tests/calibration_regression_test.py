import numpy as np
import matplotlib.pyplot as plt


# Generate fake calibration data

def static_noise(axis):
    """Static noise model for B (EMF + disturbances)."""
    data = {
        "x": 5,
        "y": 1,
        "z": -45.
    }
    return data[axis]

def dynamic_noise(axis):
    """Dynamic noise model for B."""
    data = {
        "x": np.random.rand() - 0.5,
        "y": np.random.rand() - 0.5,
        "z": np.random.rand() - 0.5,
    }
    return data[axis]*5

def tf_vi(axis, v):
    """How PSU input voltage relates to output current."""
    data = {
        "x": 2,
        "y": 2,
        "z": 2,
    }
    return data[axis]*v

def tf_ib(axis, i):
    """How output current relates to output flux density."""
    data = {
        "x": 90,
        "y": 95,
        "z": 101,
    }
    return data[axis]*i

def gendata(axis, v):
    b = np.zeros_like(v)
    for i in range(len(v)):
        b[i] = tf_ib(axis, tf_vi(axis, v[i])) + static_noise(axis) + dynamic_noise(axis)
    return b
    # return tf_ib(axis, tf_vi(axis, v)) + static_noise(axis) + dynamic_noise(axis)


def gen_axis_input(axis, m, n):
    return np.repeat(np.concatenate((
        np.linspace(0, v_range[axis][1], int(n/2)),
        np.linspace(0, v_range[axis][0], int(n/2))
    )), m)

def linreg(x, y):
    n = len(x)

    x_avg = np.sum(x) / n
    y_avg = np.sum(y) / n

    sxx = np.sum(x*x) - n*x_avg*x_avg
    sxy = np.sum(x*y) - n*x_avg*y_avg

    b1 = sxy / sxx
    b0 = y_avg - b1*x_avg

    f = b1*x + b0
    R2 = 1 - np.sum((y-f)**2)/np.sum((y-y_avg)**2)

    return b1, b0, R2


v_range = {
    "x": [-4, 4],
    "y": [-4, 4],
    "z": [-4, 4],
}

n = 10 # Number of points per dimensions
m = 10 # Number of measurements per point

input_data, calib_data, regs = [], [], []

for i, axis in enumerate(("x", "y", "z")):
    input_data.append(gen_axis_input(axis, m, n))
    calib_data.append(gendata(axis, input_data[i]))
    regs.append(linreg(input_data[i], calib_data[i]))


print("Regression output:")
sign_txt = {-1: "-", 1: "+"}
for i, axis in enumerate(("x", "y", "z")):
    print(
        axis, ": B =", round(regs[i][0], 3), "* V",
        sign_txt[regs[i][1]/abs(regs[i][1])],
        round(abs(regs[i][1]), 3), "  |  R^2 =", round(regs[i][2], 8)
    )


fig, ax = plt.subplots()
ax.set_xlabel("Input voltage [V]")
ax.set_ylabel("Output flux density [\u03bcT]")
ax.grid(True)
ax.set_axisbelow(True)

for i, c in enumerate(("red", "green", "blue")):
    ax.scatter(input_data[i], calib_data[i], color=c, s=2)
    d = np.linspace(v_range[["x", "y", "z"][i]][0], v_range[["x", "y", "z"][i]][1])
    ax.plot(d, regs[i][0] * d + regs[i][1], linestyle="dashed", color=c)
    ax.plot(d, regs[i][0] * d, linestyle="solid", color=c)
# ax.plot(exr, splineX(exr), color="black")


plt.show()
