import numpy as np
from numpy import (
    pi,
    array, ndarray,
    sin, cos, arccos, arctan,
    dot, zeros, eye, linspace, column_stack, empty
)

from time import time
from scipy.special import jv


class Orbit:
    def __init__(self, body, h_r, e, i, raan, argp, ta):
        if 0 > e >= 1:
            raise ValueError(f"Eccentricity value {e} not allowed (only elliptical orbits are supported)!")
        if h_r <= 0:
            # raise ValueError(f"Provided orbit collides with Earth (h_r = {h_r})!")
            print(f"WARNING: Orbit with h_r = {round(h_r)} km will intersect with orbiting body (Earth)!")

        self.d2r = pi / 180
        self.body = body

        # All internal angles defined in radians
        self.h_r = h_r                      # Altitude of pericentre
        self.e = e                          # Eccentricity
        self.i = self.d2r*(i % 180)         # Inclination
        self.raan = self.d2r*(raan % 360)   # Right ascention of the ascending node
        self.argp = self.d2r*(argp % 360)   # Argument of periapsis
        self.ma0 = self.d2r*(ta % 360)      # Initial Mean anomaly

        # General orbital properties
        self.r_p = (self.body.r + self.h_r)/(1-self.e)   # Distance of pericentre
        self.r_a = self.r_p*(1+e)/(1-e)     # Distance of apocentre
        self.a = (self.r_p+self.r_a)/2      # Semi-major axis
        self.b = (self.r_p*self.r_a)**0.5   # Semi-minor axis
        self.period = 2*pi * (self.a**3 / self.body.gm)**0.5  # Orbital period



    def orbit_transformation_matrix(self):
        so, sO, si = sin(self.argp), sin(self.raan), sin(self.i)
        co, cO, ci = cos(self.argp), cos(self.raan), cos(self.i)

        # Source: Wakker
        T = array([
            [co*cO - so*sO*ci, -so*cO - co*sO*ci,  sO*si],
            [co*sO + so*cO*ci, -so*sO + co*cO*ci, -cO*si],
            [           so*si,             co*si,     ci]]
        )

        return T

    def get_i(self):
        return self.i/self.d2r

    def get_r_a(self):
        return self.r_a

    def get_r_p(self):
        return self.r_p

    def get_a(self):
        return self.a

    def get_b(self):
        return self.b

    def get_period(self):
        return self.period

    def equation_of_the_center(self, M, e, order=12):
        # General expression in terms of Bessel functions of the first kind
        # (see: https://en.wikipedia.org/wiki/Equation_of_the_center#Series_expansion)
        v = M
        if 0 < e < 1:  # If e == 0 (circular orbit) don't bother
            b = 1 / e * (1 - (1 - e * e) ** 0.5)
            for s in range(1, order):
                bt = 0
                for p in range(1, order):
                    bt += b**p*(jv(s-p, s*e)+jv(s+p, s*e))
                v += 2/s * (jv(s, s*e) + bt)*sin(s*M)

        return v

    def draw(self, subdivisions=128, spacing="isochronal", order=12):

        t0 = time()
        if spacing in ("equitemporal", "isochronal"):
            if self.e > 0.5:
                print("WARNING! Isochronal point generation of orbits with eccentricity > 0.5 may be subjected to oscillations. Consider increasing the order of the method, or using equidistant instead")

            # Spacing of mean anomaly
            mean_anomaly = linspace(0, 2 * pi, subdivisions + 1)[:-1]
            mean_anomaly = array([(ma+self.ma0) % (2*pi) for ma in mean_anomaly])
            true_anomaly = zeros(len(mean_anomaly))
            for i in range(len(mean_anomaly)):
                true_anomaly[i] = self.equation_of_the_center(
                    mean_anomaly[i], self.e, order=order)

        elif spacing == "equidistant":
            # Equally spacing points along orbit:
            mean_anomaly = linspace(0, 2*pi, subdivisions+1)[:-1]
            mean_anomaly = [(ma+self.ma0) % (2*pi) for ma in mean_anomaly]
            true_anomaly = mean_anomaly  # TODO: This neglects eccentricity, or does it?

        else:
            raise ValueError("Valid spacing settings: 'equidistant', 'isochronal'")

        # Radial components relative to focus:
        radials = self.a*(1-self.e**2) / (1 + self.e * cos(true_anomaly))

        # Flat ellipse coordinates
        xyzf = column_stack([
            radials * cos(true_anomaly),
            radials * sin(true_anomaly),
            zeros(len(true_anomaly))])

        # Calculate flight path angles
        gamma = arctan((self.e * sin(true_anomaly)) / (1 + self.e * cos(true_anomaly)))

        # Calculate absolute velocities:
        vabs = (self.body.gm*(2/(xyzf[:, 0]**2+xyzf[:, 1]**2)**0.5 - 1/self.a))**0.5

        # Calculate vectorial velocities (flat)
        v_xyzf = np.empty((len(true_anomaly), 3))
        for i in range(len(true_anomaly)):
            tg = true_anomaly[i] - gamma[i]
            v_xyzf[i, 0:2] = vabs[i]*array([[cos(tg), -sin(tg)], [sin(tg), cos(tg)]])@array([0., 1.])
            v_xyzf[i, 2] = 0.

        # Apply transformation to ellipse coordinates using orbital elements
        T = self.orbit_transformation_matrix()
        xyz = empty((len(true_anomaly), 3), dtype=float)
        v_xyz = empty((len(true_anomaly), 3), dtype=float)

        for i in range(len(xyzf)):
            # Calculate 3D coordinates of orbit points
            xyz[i] = dot(T, xyzf[i])
            # Calculate 3D velocity vectors of orbit points
            v_xyz[i] = dot(T, v_xyzf[i])

        # Angular momentum unit vector (is constant in both magnitude and
        # direction for unperturbed orbits with e>1)
        H_unit_vector = dot(T, np.array([0, 0, 1]))

        print(f"[DEBUG] draw() time: {round((time()-t0)*1E6, 1)} us")

        return xyz, mean_anomaly, true_anomaly, gamma, H_unit_vector, v_xyz


    def calc(self, ):
        pass

    def plot_simple(self, coordinates):
        x, y, z = coordinates
        fig, ax = plt.subplots()
        ax.plot(x, y, "r")
        ax.set(aspect=1)
        plt.show()

    def print_properties(self):
        # TODO
        print("To be implemented...")


class Body:
    def __init__(self, name: str, m, r, axial_rate):
        self.name = name
        self.m = m                          # kg
        self.g = 6.67430E-11
        self.gm = self.m*self.g
        self.r = r                          # m
        self.axial_rate = axial_rate        # rad/s


class Earth(Body):
    def __init__(self):
        super().__init__("Earth", 5.9722E24, 6.371E6, 72.921151467E-6)