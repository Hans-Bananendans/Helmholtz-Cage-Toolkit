import numpy as np
import matplotlib.pyplot as plt

v_central = 100
mutagen_scale = 0.1
fence_scale = 0.5


def mutate(v_prev):
    """Mutate a value from a starting value, but push back if it gets too
    far from some defined central value.
    """
    m = mutagen_scale*v_central*(2 * np.random.rand() - 1)
    d = v_prev - v_central
    if d == 0:
        d = 0.1 # Subvert /0 singularity later

    sign_d = d/abs(d)
    sign_m = m/abs(m)

    # print(f"d {d}")
    # print(f"sign_d {sign_d}   sign_m {sign_m}")

    if d/abs(d) == m/abs(m):
        mutagen = m * (1 - abs(d/v_central)*fence_scale)
    else:
        mutagen = m * (1 + abs(d/v_central)*fence_scale)

    # print(f"mutagen {mutagen}")

    return v_prev + mutagen


x = np.zeros(5000)
y = np.zeros(len(x))

x[0] = v_central
y[0] = v_central

for i in range(1, len(x)):
    x[i] = mutate(x[i-1])
    y[i] = mutate(y[i-1])


fig, ax = plt.subplots()
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.grid(True)
ax.set_axisbelow(True)

ax.scatter(x, y, color="r", s=2)
ax.plot(x, y, linestyle="solid", linewidth=1, color="r")

plt.show()
