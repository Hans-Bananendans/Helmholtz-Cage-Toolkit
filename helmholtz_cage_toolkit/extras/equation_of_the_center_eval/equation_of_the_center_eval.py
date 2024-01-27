import numpy as np
from numpy import pi, sin, cos, tan, arcsin, arccos, arctan, arctan2
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from time import time
from scipy.special import jv

# Early branch of Orbit class that evaluates the "Equation of the Center" performance

class Orbit:
    def __init__(self, body, a, e, i, raan, argp, ta, invert_fix=False):
        if 0 > e >= 1:
            raise ValueError(f"Eccentricity value {e} not allowed (only elliptical orbits are supported)!")
        if a <= 0:
            raise ValueError(f"Invalid semi-major axis specified {a}!")

        self.d2r = pi / 180
        self.body = body

        # Using angle inversion to fix a bug where inclination and RAAN go in the opposite direction
        # TODO: Find the source of the bug and fix properly
        if invert_fix:
            inv = -1
        else:
            inv = 1

        # All internal angles defined in radians
        self.a = a                          # Semi-major axis
        self.e = e                          # Eccentricity
        self.i = self.d2r*(inv*i % 180)         # Inclination
        self.raan = self.d2r*(inv*raan % 360)   # Right ascention of the ascending node
        self.argp = self.d2r*(argp % 360)   # Argument of periapsis
        self.ta = self.d2r*(ta % 360)       # True anomaly


        # General orbital properties
        self.period = self.get_period()     # Orbital period
        self.b = self.a*(1-self.e**2)**0.5  # Semi-minor axis

    def orbit_transformation_matrix(self):
        T = np.zeros((3, 3))

        # "Fixed" version with RAAN and argument of periapsis switched around
        T[0][0] = cos(self.argp)*cos(self.raan) - sin(self.argp)*cos(self.i)*sin(self.raan)
        T[0][1] = sin(self.argp)*cos(self.raan) + cos(self.argp)*cos(self.i)*sin(self.raan)
        T[0][2] = sin(self.i)*sin(self.raan)
        T[1][0] = -cos(self.argp)*sin(self.raan) - sin(self.argp)*cos(self.i)*cos(self.raan)
        T[1][1] = -sin(self.argp)*sin(self.raan) + cos(self.argp)*cos(self.i)*cos(self.raan)
        T[1][2] = sin(self.i)*cos(self.raan)
        T[2][0] = sin(self.i)*sin(self.argp)
        T[2][1] = -sin(self.i)*cos(self.argp)
        T[2][2] = cos(self.i)

        # # Unmodified from https://en.wikipedia.org/wiki/Orbital_elements#Euler_angle_transformations
        # T[0][0] = cos(self.raan)*cos(self.argp) - sin(self.raan)*cos(self.i)*sin(self.argp)
        # T[0][1] = sin(self.raan)*cos(self.argp) + cos(self.raan)*cos(self.i)*sin(self.argp)
        # T[0][2] = sin(self.i)*sin(self.argp)
        # T[1][0] = -cos(self.raan)*sin(self.argp) - sin(self.raan)*cos(self.i)*cos(self.argp)
        # T[1][1] = -sin(self.raan)*sin(self.argp) + cos(self.raan)*cos(self.i)*cos(self.argp)
        # T[1][2] = sin(self.i)*cos(self.argp)
        # T[2][0] = sin(self.i)*sin(self.raan)
        # T[2][1] = -sin(self.i)*cos(self.raan)
        # T[2][2] = cos(self.i)

        return T

    def get_i(self):
        return self.i/self.d2r

    def get_period(self):
        return 2*pi * (self.a**3 / self.body.gm)**0.5

    def equation_of_the_center(self, M, e, order=6, method="A"):
        if method == "A":  # Fixed order e**7 truncated (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
            v = M
            v += 2*e*sin(M)
            v += 5/4*e**2*sin(2*M)
            v += e**3/12*(13*sin(3*M) - 3*sin(M))
            v += e**4/96*(103*sin(4*M) - 44*sin(2*M))
            v += e**5/960*(1097*sin(5*M) - 645*sin(3*M) + 50*sin(M))
            v += e**6/960*(1223*sin(6*M) - 902*sin(4*M) + 85*sin(2*M))

        if method == "B":  # General expression in terms of Bessel functions of the first kind (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
            v = M  # If e == 0 (circular orbit) don't bother
            if 0 < e < 1:
                b = 1 / e * (1 - (1 - e * e) ** 0.5)
                for s in range(1, order):
                    bt = 0
                    for p in range(1, order):
                        bt += b**p*(jv(s-p, s*e)+jv(s+p, s*e))
                    v += 2/s * (jv(s, s*e) + bt)*sin(s*M)

        return v

    def draw(self, subdivisions=128, spacing="equidistant", order=12, method="B"):

        t0 = time()
        if spacing in ("equitemporal", "isochronal"):
            if self.e > 0.5:
                print("WARNING! Isochronal point generation of orbits with eccentricity > 0.5 may be subjected to oscillations. Consider increasing the order of the method, or using equidistant instead")

            # Spacing of mean anomaly
            mean_anomaly = np.linspace(0, 2 * pi, subdivisions + 1)[:-1]
            angulars = np.zeros(len(mean_anomaly))
            for i in range(len(mean_anomaly)):
                angulars[i] = self.equation_of_the_center(mean_anomaly[i],
                                                          self.e,
                                                          order=order,
                                                          method=method)


        elif spacing == "equidistant":
            # Using polar coordinates:
            angulars = np.linspace(0, 2*pi, subdivisions+1)[:-1]


        else:
            raise ValueError("Valid spacing settings: 'equidistant', 'isochronal'")

        # Radial components relative to focus:
        radials = self.a*(1-self.e**2) / (1 + self.e * cos(angulars))

        # Flat coordinates
        xf = radials * cos(angulars)
        yf = radials * sin(angulars)
        zf = np.zeros(len(xf))

        x = np.zeros(len(xf))
        y = np.zeros(len(xf))
        z = np.zeros(len(xf))

        T = self.orbit_transformation_matrix()

        for i in range(len(xf)):
            x[i], y[i], z[i] = np.dot(T, np.array([xf[i], yf[i], zf[i]]))

        print(f"draw() time: {round((time()-t0)*1E6, 1)} ns")
        return x, y, z

    def calc(self, ):
        pass

    def plot_simple(self, coordinates):
        x, y, z = coordinates
        fig, ax = plt.subplots()
        ax.plot(x, y, "r")
        ax.set(aspect=1)
        plt.show()


class Body:
    def __init__(self, name: str, m, r):
        self.name = name
        self.m = m
        self.g = 6.67430E-11
        self.gm = self.m*self.g
        self.r = r


class Earth(Body):
    def __init__(self):
        super().__init__("Earth", 5.9722E24, 6.371E6)


evalsets = [
    # ["A", 6],
    ["B", 5],
    ["B", 6],
    ["B", 7],
    ["B", 8],
    ["B", 9],
    ["B", 10],
    ["B", 12],
    ["B", 14],
    ["B", 16],
    ["B", 20],
    ["B", 24],
    ["B", 32],
]

earth = Earth()
eval_dummy_orbit = Orbit(earth, earth.r, 0, 0, 0, 0, 0)

print(f"Begin with {len(evalsets)} sets. Grab a coffee, this could take a minute...")

for i_evalset, evalset in enumerate(evalsets):

    t_begin = time()

    # ==== Evaluation of equation of the center method
    teval0 = time()
    eval_method = evalset[0]
    eval_o = evalset[1]
    eval_e = (0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.9)
    eval_subs = 1024
    eval_M = np.linspace(0, 2*pi, eval_subs)
    eval_f = np.zeros((len(eval_e), eval_subs))
    for i_e, ee in enumerate(eval_e):
        for i_M, M in enumerate(eval_M):
            eval_f[i_e][i_M] = eval_dummy_orbit.equation_of_the_center(
                M, ee, order=eval_o, method=eval_method)
    teval1 = time()-teval0

    # ==== Evaluation plot
    fig, axe = plt.subplots()

    for i_e in range(len(eval_e)):
        axe.plot(eval_M, eval_f[i_e], label="e = "+str(eval_e[i_e]))
    axe.legend()
    axe.set_xlabel("Mean anomaly M (rad)")
    axe.set_ylabel("True anomaly f (rad)")
    axe.set_title(f"Evaluation of equation of the center for order {eval_o} (method {eval_method})\n Evaluation time: {round(teval1*1000,3)} ms")
    pi_formatter = FuncFormatter(lambda val, pos: "{:.0g}$\pi$".format(val/np.pi) if val != 0 else '0')
    axe.xaxis.set_major_formatter(pi_formatter)
    axe.yaxis.set_major_formatter(pi_formatter)
    axe.xaxis.set_major_locator(MultipleLocator(base=np.pi))
    axe.xaxis.set_minor_locator(MultipleLocator(base=np.pi/4))
    axe.yaxis.set_major_locator(MultipleLocator(base=np.pi))
    axe.yaxis.set_minor_locator(MultipleLocator(base=np.pi/4))
    axe.grid(True, which="both")


    fig.savefig(f"equation_of_the_center_eval_{eval_o}{eval_method}.png")

    print(f"({i_evalset+1}/{len(evalsets)}) Made set {eval_o}{eval_method} at {eval_subs} subdivisions in {round(time()-t_begin, 3)} s...")

    # plt.show()
