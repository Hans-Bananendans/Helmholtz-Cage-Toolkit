# from scipy.signal import sawtooth, square
from pyIGRF import igrf_value
from scipy.interpolate import make_interp_spline

from time import time  # todo remove

from helmholtz_cage_toolkit import *
# from helmholtz_cage_toolkit
from helmholtz_cage_toolkit.orbit import Orbit, Earth
from helmholtz_cage_toolkit.utilities import cross3d
from helmholtz_cage_toolkit.pg3d import (
    uv3d,
    wrap,
    conv_ECI_geoc,
    R_SI_B,
    R_NED_ECI,
)


def interpolate(t,
                B,
                factor: int,
                type: str):
    """ General-purpose interpolation function for processing generated
    schedules, regardless of the underlying generator used. The idea is that
    this function is always applied, and when no interpolation needs to occur,
    the variable 'type' is left as 'none'. Variable 'factor' must be a
    positive integer and represends how many more points will be generated.
    For example, for a dataset of length 1000, a factor of 4 will result in an
    interpolated dataset of length 4000.

    Currently supported interpolation:
    'linear' : Linear interpolation for each axis
    'spline' : Cubic spline interpolation for each axis
    'none' or anything else : No interpolation, inputs are returned untouched

    't' must be a 1D array of length n
    'B' must be a bundle of three 1D arrays of length n containing the X, Y, Z
        components of B.
    """
    if factor < 1:
        raise ValueError(f"Input 'factor' must be a positive, non-zero integer (given {factor})!")

    if type == "linear":
        t_interp = linspace(t[0], t[-1], len(t) * factor)
        B_interp = [
            array(interp(t_interp, t, B[0])),
            array(interp(t_interp, t, B[1])),
            array(interp(t_interp, t, B[2])),
        ]
        return t_interp, B_interp

    elif type == "spline":
        # Interpolate time steps linearly
        t_interp = linspace(t[0], t[-1], len(t) * factor)

        # Construction ranges for interpolation
        r = range(len(t))
        r2 = linspace(r[0], r[-1], len(t_interp))

        # Construct spline contours, where boundary conditions clamp the ends
        splineX = make_interp_spline(r, B[0], bc_type="natural")
        splineY = make_interp_spline(r, B[1], bc_type="natural")
        splineZ = make_interp_spline(r, B[2], bc_type="natural")

        # Perform interpolation by running r2 through the spline contours
        B_interp = [
            splineX(r2),
            splineY(r2),
            splineZ(r2),
        ]
        return t_interp, B_interp

    elif type == "none":
        return t, B

    else:
        print(f"interpolate() was given an unknown type '{type}'; No interpolation was performed.")
        return t, B


interpolation_parameters = {
    "function": "none",
    "factor": 1,
}


# def generator_orbital(generation_parameters, datapool):
#     t0 = time()
#
#     print("[DEBUG] generator_orbital() called") # TODO REMOVE
#
#     # Assemble parameters
#     g = generation_parameters  # Shorthand
#     data = datapool
#
#     orbit_eccentricity = g["orbit_eccentricity"]
#     orbit_inclination = g["orbit_inclination"]
#     orbit_pericentre_altitude = g["orbit_pericentre_altitude"]
#     orbit_RAAN = g["orbit_RAAN"]
#     orbit_argp = g["orbit_argp"]
#     orbit_ma0 = g["orbit_ma0"]
#
#     # print("orbit_pericentre_altitude:", orbit_pericentre_altitude)
#
#     angle_body_x_0 = g["angle_body_x_0"]
#     angle_body_y_0 = g["angle_body_y_0"]
#     angle_body_z_0 = g["angle_body_z_0"]
#     rate_body_x = g["rate_body_x"]
#     rate_body_y = g["rate_body_y"]
#     rate_body_z = g["rate_body_z"]
#
#     earth_zero_datum = g["earth_zero_datum"]
#     date0 = g["date0"]
#
#     n_orbit_subs = g["n_orbit_subs"]
#     n_step = g["n_step"]
#     # time_speed_factor = g["time_speed_factor"]
#
#     t1 = time()
#
#     # ==== PREAMBLE
#
#     # Invoke the draw() function in Orbit class to generate orbit points.
#     xyz, v_xyz, ma, ta, gamma, huv = data.orbit.draw(
#         subdivisions=n_orbit_subs,
#         spacing=data.config["orbit_spacing"],
#         eotc_order=data.config["eotc_order"]
#     )
#
#     t2 = time()
#
#     dt = data.orbit.get_period() / n_orbit_subs
#     dth_E = data.orbit.body.axial_rate * dt
#
#     t3 = time()
#
#     # Pre-allocate data objects
#     i_step = array(range(n_step))
#     Rt_ECI_SI = empty((n_orbit_subs, 3, 3))
#     Rt_SI_B = empty((n_step, 3, 3))
#     hll = empty((n_step, 3))
#     B_ECI = empty((n_step, 3))
#     B_B = empty((n_step, 3))
#     date = empty(n_step)
#
#     t4 = time()
#
#     # R_ECI_SI
#     for isub in range(n_orbit_subs):
#         Rt_ECI_SI[isub, :, :] = vstack([
#             uv3d(v_xyz[isub]),  # X-component points along velocity vector
#             huv,  # Y-component points at angular momentum vector
#             cross3d(uv3d(v_xyz[isub]), huv)])  # Z-component points along the cross product of the two
#
#     t5 = time()
#
#     for i in range(n_step):
#         # Note: 31_556_952 is number of seconds in a Gregorian calendar year
#         date[i] = date0 + dt * i / 31_556_952  # decimal date at i_step
#
#         #
#         rotangles = array((  # [deg], [deg/s] -> [rad(/dt)]
#             180 / pi * (angle_body_x_0 + i * rate_body_x * dt),  # phi_B, angle around X
#             180 / pi * (angle_body_y_0 + i * rate_body_y * dt),  # theta_B, angle around Y
#             180 / pi * (angle_body_z_0 + i * rate_body_z * dt)  # psi_B, angle around Z
#         ))
#
#         Rt_SI_B[i, :, :] = R_SI_B(rotangles)
#
#         # Radius/altitude, longitude and latitude
#         rlli = conv_ECI_geoc(xyz[divmod(i, n_orbit_subs)[1], :])  # |ECI
#
#         hll[i, :] = array((
#             1E-3 * (rlli[0] - data.orbit.body.r),  # Altitude in [km]
#             # 1E-3*(rlli[2]),  # Altitude in [km]
#             180 / pi * wrap(rlli[1] - (earth_zero_datum + i * dth_E), 2 * pi),  # Geocentric longitude |ECEF [deg]
#             # Geocentric latitude |ECEF [deg]
#             180 / pi * rlli[2]
#         ))
#
#         # Local magnetic field vector (syntax: igrf_value(lat, lon, alt=0., year=2005.))
#         _, _, _, bx, by, bz, _ = igrf_value(
#             hll[i, 2],
#             hll[i, 1],
#             hll[i, 0],
#             date[i])
#
#         Bi_NED = array([bx, by, bz])  # B|NED
#         B_ECI[i, :] = R_NED_ECI(rlli[1], rlli[2]) @ Bi_NED  # B|ECI
#         Bi_SI = Rt_ECI_SI[divmod(i, n_orbit_subs)[1]] @ B_ECI[i, :]  # B|SI
#         B_B[i, :] = Rt_SI_B[i] @ Bi_SI  # B|B
#
#     t6 = time()
#
#     print(f"[DEBUG] generator_orbital() import:      {round((t1 - t0) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() draw:        {round((t2 - t1) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() orbit props: {round((t3 - t2) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() preallocate: {round((t4 - t3) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() loop n_subs: {round((t5 - t4) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() loop n_step: {round((t6 - t5) * 1E6, 1)} us")
#     print(f"[DEBUG] generator_orbital() TOTAL:       {round((t6 - t0) * 1E6, 1)} us")
#
#     return i_step, dt, dth_E, B_B, B_ECI, hll, date, Rt_ECI_SI, Rt_SI_B, xyz, \
#         v_xyz, ma, ta, gamma, huv


def generator_orbital2(generation_parameters, datapool, timing=False):
    if timing:
        t0 = time()

    print("[DEBUG] generator_orbital2() called")

    # Assemble parameters
    g = generation_parameters  # Shorthand
    data = datapool

    orbit_eccentricity = g["orbit_eccentricity"]
    orbit_inclination = g["orbit_inclination"]
    orbit_pericentre_altitude = g["orbit_pericentre_altitude"]
    orbit_RAAN = g["orbit_RAAN"]
    orbit_argp = g["orbit_argp"]
    orbit_ma0 = g["orbit_ma0"]

    angle_body_x_0 = g["angle_body_x_0"]
    angle_body_y_0 = g["angle_body_y_0"]
    angle_body_z_0 = g["angle_body_z_0"]
    rate_body_x = g["rate_body_x"]
    rate_body_y = g["rate_body_y"]
    rate_body_z = g["rate_body_z"]

    earth_zero_datum = g["earth_zero_datum"]
    date0 = g["date0"]

    n_orbit_subs = g["n_orbit_subs"]
    n_step = g["n_step"]
    time_speed_factor = g["time_speed_factor"]

    if timing:
        t1 = time()

    # Pre-allocate data object
    simdata = {
        "i_step": array(range(n_step)),
        "Rt_ECI_SI": empty((n_orbit_subs, 3, 3)),
        "Rt_SI_B": empty((n_step, 3, 3)),
        "hll": empty((n_step, 3)),
        "B_ECI": empty((n_step, 3)),
        "B_B": empty((n_step, 3)),
        "date": empty(n_step),
    }

    if timing:
        t2 = time()

    # ==== PREAMBLE

    # Update the Orbit() class with the new orbital elements
    data.orbit = Orbit(
        Earth(),
        orbit_pericentre_altitude,
        orbit_eccentricity,
        orbit_inclination,
        orbit_RAAN,
        orbit_argp,
        orbit_ma0,
    )

    if timing:
        t3 = time()

    # print("DEBUG!!!")
    # print(datapool.config)

    # Invoke the draw() function in Orbit class to generate orbit points.
    simdata["xyz"], simdata["v_xyz"], simdata["ma"], \
        simdata["ta"], simdata["gamma"], simdata["huv"] = data.orbit.draw(
        subdivisions=n_orbit_subs,
        # spacing=data.config["orbit_spacing"],
        spacing="isochronal",
        eotc_order=data.config["eotc_order"]
    )

    if timing:
        t4 = time()

    dt = data.orbit.get_period() / n_orbit_subs     # [s/dt]
    dth_E = data.orbit.body.axial_rate * dt         # [rad/dt]

    simdata["dt"] = dt
    simdata["dth_E"] = dth_E
    simdata["th_E0"] = earth_zero_datum
    simdata["angle_body0"] = pi / 180 * array((
        angle_body_x_0, angle_body_y_0, angle_body_z_0
    ))
    simdata["n_orbit_subs"] = n_orbit_subs
    simdata["n_step"] = n_step
    simdata["t"] = dt/time_speed_factor * simdata["i_step"]


    if timing:
        t5 = time()

    # R_ECI_SI
    for isub in range(n_orbit_subs):
        simdata["Rt_ECI_SI"][isub, :, :] = vstack([
            uv3d(simdata["v_xyz"][isub]),  # X-component points along velocity vector
            simdata["huv"],  # Y-component points at angular momentum vector
            cross3d(uv3d(simdata["v_xyz"][isub]),
                    simdata["huv"])])  # Z-component points along the cross product of the two

    if timing:
        t6 = time()
        t7a = 0
        t7b = 0
        t7c = 0
        t7d = 0
        t7e = 0
        t7f = 0
        t7g = 0
        t7 = time()

    for i in range(n_step):

        # Note: 31_556_952 is number of seconds in a Gregorian calendar year
        simdata["date"][i] = date0 + dt * i / 31_556_952  # decimal date at i_step

        if timing:
            t7a += time()-t7
            t7 = time()

        rotangles = array((  # [deg], [deg/s] -> [rad(/dt)]
            pi/180 * (angle_body_x_0 + i * rate_body_x * dt),   # phi_B, angle around X
            pi/180 * (angle_body_y_0 + i * rate_body_y * dt),   # theta_B, angle around Y
            pi/180 * (angle_body_z_0 + i * rate_body_z * dt)    # psi_B, angle around Z
        ))

        if timing:
            t7b += time()-t7
            t7 = time()

        # R_SI_B
        simdata["Rt_SI_B"][i, :, :] = R_SI_B(rotangles)

        if timing:
            t7c += time()-t7
            t7 = time()

        # Radius/altitude, longitude and latitude
        rlli = conv_ECI_geoc(simdata["xyz"][divmod(i, n_orbit_subs)[1], :])  # |ECI

        if timing:
            t7d += time()-t7
            t7 = time()

        simdata["hll"][i, :] = array((
            1E-3 * (rlli[0] - data.orbit.body.r),  # Altitude in [km]
            # 1E-3*(rlli[2]),  # Altitude in [km]
            180 / pi * wrap(rlli[1] - (earth_zero_datum + i * dth_E), 2 * pi),  # Geocentric longitude |ECEF [deg]
            # Geocentric latitude |ECEF [deg]
            180 / pi * rlli[2]
        ))

        if timing:
            t7e += time()-t7
            t7 = time()

        # Local magnetic field vector (syntax: igrf_value(lat, lon, alt=0., year=2005.))
        _, _, _, bx, by, bz, _ = igrf_value(
            simdata["hll"][i, 2],
            simdata["hll"][i, 1],
            simdata["hll"][i, 0],
            simdata["date"][i])

        if timing:
            t7f += time()-t7
            t7 = time()

        Bi_NED = array([bx, by, bz])                                    # B|NED
        simdata["B_ECI"][i, :] = R_NED_ECI(rlli[1], rlli[2]) @ Bi_NED   # B|ECI
        Bi_SI = simdata["Rt_ECI_SI"][divmod(i, n_orbit_subs)[1]] \
                @ simdata["B_ECI"][i, :]                                # B|SI
        simdata["B_B"][i, :] = simdata["Rt_SI_B"][i] @ Bi_SI            # B|B

        if timing:
            t7g += time()-t7
            t7 = time()

    if timing:
        t7 = time()

        print(f"[DEBUG] generator_orbital2() import:      {round((t1 - t0) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() preallocate: {round((t2 - t1) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() orbit updat: {round((t3 - t2) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() draw:        {round((t4 - t3) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() orbit props: {round((t5 - t4) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() loop n_subs: {round((t6 - t5) * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() loop n_step: {round((t7 - t6) * 1E6, 1)} us")
        print(f"[DEBUG] a): {round(t7a * 1E6, 1)} us")
        print(f"[DEBUG] b): {round(t7b * 1E6, 1)} us")
        print(f"[DEBUG] c): {round(t7c * 1E6, 1)} us")
        print(f"[DEBUG] d): {round(t7d * 1E6, 1)} us")
        print(f"[DEBUG] e): {round(t7e * 1E6, 1)} us")
        print(f"[DEBUG] f): {round(t7f * 1E6, 1)} us")
        print(f"[DEBUG] g): {round(t7g * 1E6, 1)} us")
        print(f"[DEBUG] generator_orbital2() TOTAL:       {round((t7 - t0) * 1E6, 1)} us")

    return simdata


orbital_generation_parameters = {
    # Orbital elements
    "orbit_eccentricity": 0.2,  # [-]
    "orbit_inclination": 54,  # [deg]
    "orbit_pericentre_altitude": 400E3,  # [m]
    "orbit_RAAN": 0,  # [deg]
    "orbit_argp": 0,  # [deg]
    "orbit_ma0": 0,  # [deg]

    # Body configuration
    "angle_body_x_0": 0,  # [deg]
    "angle_body_y_0": 0,  # [deg]
    "angle_body_z_0": 0,  # [deg]
    "rate_body_x": 0,  # [deg/s]
    "rate_body_y": 0,  # [deg/s]
    "rate_body_z": 0,  # [deg/s]

    # Various
    "earth_zero_datum": 0,  # [deg]
    "date0": 2024.0,  # [decimal date]

    # Simulation settings
    "n_orbit_subs": 256,  # [-] <positive int>
    "n_step": 1024,  # [-] <positive int>
    # "interpolation_factor": 1,          # [-] <positive int>
    "time_speed_factor": 1.0            # [-] <positive float>
}

# ============================================================================
# ========================== TESTING =========================================
# ============================================================================

if __name__ == "__main__":
    # ==== Orbital_default_parameters ====
    orbital_default_generation_parameters = {
        # Orbital elements
        "orbit_eccentricity": 0.0,  # [-]
        "orbit_inclination": 0.0,  # [deg]
        "orbit_pericentre_altitude": 400E3,  # [km]
        "orbit_RAAN": 0.,  # [deg]
        "orbit_argp": 0.,  # [deg]
        "orbit_ma0": 0.,  # [deg]

        # Body configuration
        "angle_body_x_0": 0,  # [deg]
        "angle_body_y_0": 0,  # [deg]
        "angle_body_z_0": 0,  # [deg]
        "rate_body_x": 0,  # [deg/s]
        "rate_body_y": 0,  # [deg/s]
        "rate_body_z": 0,  # [deg/s]

        # Various
        "earth_zero_datum": 0,  # [deg]
        "date0": 2024.0,  # [decimal date]

        # Simulation settings
        "n_orbit_subs": 256,  # [-] <positive int>
        "n_step": 1024,  # [-] <positive int>
        # "interpolation_factor": 1,          # [-] <positive int>
        "time_speed_factor": 1.0            # [-] <positive float>
    }

    odgp = orbital_default_generation_parameters  # Shorthand


    class DummyDataPool:
        def __init__(self, orbit):
            self.config = {
                "orbit_spacing": "isochronal",
                "eotc_order": 12,
            }
            self.orbit = orbit


    orbit = Orbit(
        Earth(),
        odgp["orbit_pericentre_altitude"],
        odgp["orbit_eccentricity"],
        odgp["orbit_inclination"],
        odgp["orbit_RAAN"],
        odgp["orbit_argp"],
        odgp["orbit_ma0"]
    )

    dummy_datapool = DummyDataPool(orbit)

    # i_step, dt, dth_E, B_B, B_ECI, hll, date, Rt_ECI_SI, Rt_SI_B, xyz, \
    #     v_xyz, ma, ta, gamma, huv = generator_orbital(odgp, dummy_datapool)

    print("########################################")

    simdata = generator_orbital2(odgp, dummy_datapool)
    print(simdata.keys())

    # print(i_step == simdata["i_step"])
    # print(dt == simdata["dt"])
    # print(dth_E == simdata["dth_E"])
    # print(B_B == simdata["B_B"])
    # print(B_ECI == simdata["B_ECI"])
    # print(hll == simdata["hll"])
    # print(date == simdata["date"])
    # print(Rt_ECI_SI == simdata["Rt_ECI_SI"])
    # print(Rt_SI_B == simdata["Rt_SI_B"])
    # print(xyz == simdata["xyz"])
    # print(v_xyz == simdata["v_xyz"])
    # print(ma == simdata["ma"])
    # print(ta == simdata["ta"])
    # print(gamma == simdata["gamma"])
    # print(huv == simdata["huv"])

    # print("\ni_step:", len(i_step), i_step)
    # print("\ndt, dth_E", round(dt, 3), round(dth_E, 6))
    # print(f"Check: {round(orbit.get_period(), 3)}/{odgp['n_orbit_subs']} = {round(orbit.get_period()/odgp['n_orbit_subs'],3)}")
    # print("\nB_B:", len(B_B), B_B)
    # print("\nB_ECI:", len(B_ECI), B_ECI)
    # print("\nhll:", len(hll), hll)
    # print("\ndate:", len(date), date)
    #
    # print("\nRt_ECI_SI:", len(Rt_ECI_SI), Rt_ECI_SI)
    # print("\nRt_SI_B:", len(Rt_SI_B), Rt_SI_B)
    #
    # print("\nxyz:", len(xyz), xyz)
    # print("\nv_xyz:", len(v_xyz), v_xyz)
    #
    # print("\nma:", len(ma), ma)
    # print("\nta:", len(ta), ta)
    # print("\ngamma:", len(gamma), gamma)
    # print("\nhuv:", len(huv), huv)

    # import matplotlib.pyplot as plt
    #
    # ran = linspace(0, 2*pi, 100)
    # earth = 6378000*array([cos(ran), sin(ran)])
    #
    # fig, ax = plt.subplots()
    # # ax.plot(xyz[:, 0], xyz[:, 1], "r", earth[0], earth[1], "b")
    # vabs = (v_xyz[:, 0]**2 + v_xyz[:, 1]**2 + v_xyz[:, 2])**0.5
    # ranny = array(range(odgp["n_orbit_subs"]))
    # # print(vabs)
    # print(len(vabs))
    # print(len(vabs)==len(ranny))
    # print(v_xyz)
    #
    # ax.plot(10*ranny, vabs, "r")
    # plt.show()
