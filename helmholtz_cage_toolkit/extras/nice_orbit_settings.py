#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename.py

@author: Johan Monster
"""

a = {
    # Sort of a pseudo-helical rose with pleasing asymmetry.
    # ==== Orbital_default_parameters ====
    "orbital_default_generation_parameters": {
        # Orbital elements
        "orbit_eccentricity": 0.25,  # [-]
        "orbit_inclination": 50,  # [deg]
        "orbit_pericentre_altitude": 350E3,  # [m]
        "orbit_RAAN": 24,  # [deg]
        "orbit_argp": 0.,  # [deg]
        "orbit_ma0": 0.,  # [deg]

        # Body configuration
        "angle_body_x_0": 0.,  # [deg]
        "angle_body_y_0": 0.,  # [deg]
        "angle_body_z_0": 0.,  # [deg]
        "rate_body_x": 0.1,  # [deg/s]
        "rate_body_y": 0.,  # [deg/s]
        "rate_body_z": -0.1,  # [deg/s]

        # Various
        "earth_zero_datum": 0,  # [deg]
        "date0": 2024.0,  # [decimal date]

        # Simulation settings
        "n_orbit_subs": 512,  # [-] <positive int>
        "n_step": 10240,  # [-] <positive int>
        "time_speed_factor": 1.0  # [-] <positive float>
    },


    # Toroidal Eye
    # ==== Orbital_default_parameters ====
    "orbital_default_generation_parameters": {
        # Orbital elements
        "orbit_eccentricity": 0.0,  # [-]
        "orbit_inclination": 5,  # [deg]
        "orbit_pericentre_altitude": 600E3,  # [m]
        "orbit_RAAN": 0,  # [deg]
        "orbit_argp": 0.,  # [deg]
        "orbit_ma0": 0.,  # [deg]

        # Body configuration
        "angle_body_x_0": 0.,  # [deg]
        "angle_body_y_0": 0.,  # [deg]
        "angle_body_z_0": 0.,  # [deg]
        "rate_body_x": 0.5,  # [deg/s]
        "rate_body_y": 0.,  # [deg/s]
        "rate_body_z": 0.,  # [deg/s]

        # Various
        "earth_zero_datum": 0,  # [deg]
        "date0": 2024.0,  # [decimal date]

        # Simulation settings
        "n_orbit_subs": 512,  # [-] <positive int>
        "n_step": 10240,  # [-] <positive int>
        "time_speed_factor": 1.0  # [-] <positive float>
    },


    # Starfruit sketched by Jason Gathorne-Hardy
    # ==== Orbital_default_parameters ====
    "orbital_default_generation_parameters": {
        # Orbital elements
        "orbit_eccentricity": 0.0,  # [-]
        "orbit_inclination": 70,  # [deg]
        "orbit_pericentre_altitude": 300E3,  # [m]
        "orbit_RAAN": 0,  # [deg]
        "orbit_argp": 0.,  # [deg]
        "orbit_ma0": 0.,  # [deg]

        # Body configuration
        "angle_body_x_0": 0.,  # [deg]
        "angle_body_y_0": 90.,  # [deg]
        "angle_body_z_0": 45.,  # [deg]
        "rate_body_x": 0.025,  # [deg/s]
        "rate_body_y": 0.,  # [deg/s]
        "rate_body_z": 0.,  # [deg/s]

        # Various
        "earth_zero_datum": 0,  # [deg]
        "date0": 2024.0,  # [decimal date]

        # Simulation settings
        "n_orbit_subs": 512,  # [-] <positive int>
        "n_step": 10240,  # [-] <positive int>
        "time_speed_factor": 1.0  # [-] <positive float>
    },

}
