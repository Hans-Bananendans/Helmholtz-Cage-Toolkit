config = {
    "APPNAME": "Helmholtz Cage Toolkit",
    "VERSION": "0.3.0",


    # ==== General settings ====
    "verbosity": 1,
    "use_dummies": True,
    "default_windowsize": (1280, 900),

    # ==== TCP connection settings ====
    "server_address": "127.0.0.1",
    # "server_address": "169.254.241.64",
    "server_port": 7777,
    # "buffer_size": 1024,  # Specified by codec instead

    "connect_on_startup": False,
    "connect_on_startup_delay": 3000,
    "label_update_period": 5000,
    "time_correction_period": 60000,
    "pings_per_test": 8,


    # ==== Data acquisition ====
    "telemetry_polling_rate": 30,   # [S/s] How frequently Bm is polled

    "CW_HHCPlots_refresh_rate": 30,
    "CW_values_refresh_rate": 30,

    "tracking_timer_period": 10,

    "enable_arrow_tips": True,  # Whether to plot vectors with tips (substantial overhead)


    # ==== Local ====
    # In the GUI application, you can choose to automatically reject (negate)
    # the local Earth magnetic field vector (B_EMF). There are two ways to
    # tell the GUI what this vector is:
    # 1. Specify the config setting 'local_EMF' -> [bx, by, bz] nT in the
    #    frame of the Helmholtz cage.
    # 2. Set the config setting 'local_EMF' to 'None'. This will make the GUI
    #    calculate the local EMF from the IGRF model. To do this, parameters
    #    'local_latitude', 'local_longitude', 'local_altitude' must be
    #    correctly specified. The time component will be taken from the Unix
    #    epoch. In addition, a rotation matrix to convert from the ENU frame
    #    to the cage frame must be specified 'R_ENU_cageframe'.
    # 3. Use the "Take from Bm" button in the GUI, although this will not
    #    strictly provide B_EMF but will include ambient fields at the location
    #    as well.
    "local_EMF": None,
    "local_latitude": 51.99002134132983,        # [deg] +N, -S
    "local_longitude": 4.375289736921873,       # [deg] +E, -W
    "local_altitude": 30,                       # [m]   +U, -D
    "R_ENU_cageframe": [[ 0.92050, 0.39073, 0],    # R_Z(-23 deg)
                        [-0.39073, 0.92050, 0],
                        [       0,        0, 1]],

    # ==== ADC settings ====
    "adc_pollrate": 30,  # TODO STALE


    # ==== DAC settings ====
    "vmax_dac": 5.0,  # VDC  # TODO STALE


    # ==== Power supply settings ====
    "vmax_supply": 60.0,  # VDC  # TODO STALE
    "imax_supply": 5.0,  # A  # TODO STALE


    # ==== Hardware and cable routing ====
    "adc_channel_bx": 0,  # TODO STALE
    "adc_channel_by": 1,  # TODO STALE
    "adc_channel_bz": 2,  # TODO STALE

    "dac_supply1_act": 0,  # TODO STALE
    "dac_supply1_cc": 2,  # TODO STALE
    "dac_supply1_vc": 4,  # TODO STALE

    "dac_supply2_act": 1,  # TODO STALE
    "dac_supply2_cc": 3,  # TODO STALE
    "dac_supply2_vc": 5,  # TODO STALE

    "dac_supply3_act": 8,  # TODO STALE
    "dac_supply3_cc": 10,  # TODO STALE
    "dac_supply3_vc": 12,  # TODO STALE


    # ==== Plotwindow settings ====
    "hhcplot_windowsize": (560, 220),
    "visualizer_windowsize": (560, 120),
    "visualizer_bscale": 200_000,
    "visualizer_updaterate": 30,

    "plotcolor_Bc": "#00ffff",  # cyan
    "plotcolor_Bm": "#ffbf00",  # amber
    "plotcolor_Br": "#40ff00",  # lime
    "plotcolor_Bo": "#ff00ff",  # magenta


    # ==== LCD box styling ==== # TODO STALE
    "lcd_maxdigits": 8,
    "stylesheet_lcd_red":
        """QLCDNumber {
        color: rgba(244, 67, 54, 255);
        background-color: rgba(244, 67, 54, 26);
        border-color: rgba(244, 67, 54, 77);
        }""",
    "stylesheet_lcd_green":
        """QLCDNumber {
        color: rgba(50, 255, 50, 255);
        background-color: rgba(50, 255, 50, 26);
        border-color: rgba(50, 255, 50, 77);
        }""",
    "stylesheet_lcd_blue":
        """QLCDNumber {
        color: rgba(0, 146, 255, 255);
        background-color: rgba(0, 146, 255, 26);
        border-color: rgba(0, 146, 255, 77);
        }""",
    "stylesheet_lcd_white":
        """QLCDNumber {
        color: rgba(255, 255, 255, 255);
        background-color: rgba(255, 255, 255, 26);
        border-color: rgba(255, 255, 255, 77);
        }""",

    "show_plot_visibility_tabs": True,

    # ==== Orbit Visualizer ====
    "ov_plotcolours": ("#ff00ffff", "#ff8000ff", "#00ffffff", "#ffff00ff", "#00ff00ff"),
    "ov_preferred_colour": 1,
    # "ov_draw_B_vector": True,
    "ov_plotscale": 1E7,
    "ov_autorotate_angle": -0.25,
    "ov_earth_model_resolution": (16, 24),
    "ov_earth_model_colours": {
            "ocean": "#002bff",
            "ice": "#eff1ff",
            "cloud": "#dddddd",
            "green1": "#1b5c0f",
            "green2": "#093800",
            "green3": "#20c700",
            "test": "#ff0000",
        },
    "ov_satellite_model_scale": 0.1,

    "ov_draw": {
        "xy_grid": True,
        "tripod_ECI": True,
        "tripod_ECEF": False,
        "tripod_NED": False,
        "tripod_SI": False,
        "tripod_B": True,
        "earth_model": True,
        "satellite": True,
        "satellite_helpers": True,
        "satellite_model": True,
        "position_vector": False,
        "orbit_lineplot": True,
        "orbit_scatterplot": False,
        "orbit_helpers": True,
        "velocity_vector": False,
        "angular_momentum_vector": False,
        "b_vector": True,
        "b_lineplot": False,
        "b_linespokes": False,
        "b_fieldgrid": False,
        "autorotate": False,
    },

    "ov_rotate_earth": True,
    "ov_earth_model_smoothing": True,
    "ov_use_antialiasing": True,
    "ov_endpatching": True,

    # ==== Cage3D Plot ====
    "c3d_cage_dimensions": {
        "x": 1.85,
        "y": 1.95,
        "z": 2.05,
        "t": 0.08,
        "z_offset": 2.05/2,
        "spacing": 0.5445,
    },
    "c3d_cage_alpha": 0.25,
    "c3d_line_alpha": 0.1,
    "c3d_component_alpha": 1.0,
    "c3d_preferred_colour": 2,
    "c3d_plotscale": 5E4,
    "c3d_draw": {
        "xy_grid": True,
        "tripod_b": True,
        "cage_structure": True,
        "cage_illumination": False,
        "satellite_model": False,
        "lineplot": True,
        "linespokes": True,
        "b_vector": True,
        "b_dot": True,
        "b_tail": True,
        "b_components": False,

        "autorotate": False,
    },
    "c3d_autorotate_angle": -0.25,
    "c3d_tail_length": [3, 6, 9, 12, 15, 18, 21, 24],
    "c3d_satellite_model": {
        "x_dim": 0.1,
        "y_dim": 0.1,
        "z_dim": 0.2,
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    },

    # ==== Orbital generator options ====
    "eotc_order": 12,                       # Default order to use for the Equation of the Centre approximation
    "orbit_spacing": "isochronal",          # Default orbit point spacing

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
        "n_step": 4096,  # [-] <positive int>
        "time_speed_factor": 1.0  # [-] <positive float>
    },



    # ==== Cyclics_default_parameters ====
    "cyclics_default_generation_parameters": {
        "duration": 10,
        "resolution": 10,
        "predelay": 0.0,
        "postdelay": 0.0,
        "fbaseX": "constant",
        "fbaseY": "constant",
        "fbaseZ": "constant",
        "amplitudeX": 1.0,
        "amplitudeY": 1.0,
        "amplitudeZ": 1.0,
        "frequencyX": 0.1,
        "frequencyY": 0.1,
        "frequencyZ": 0.1,
        "phaseX": 0.0,
        "phaseY": 0.0,
        "phaseZ": 0.0,
        "offsetX": 0.0,
        "offsetY": 0.0,
        "offsetZ": 0.0,
        "fbase_noiseX": "gaussian",
        "fbase_noiseY": "gaussian",
        "fbase_noiseZ": "gaussian",
        "noise_factorX": 0.0,
        "noise_factorY": 0.0,
        "noise_factorZ": 0.0,
    },

    # ==== default_interpolation_parameters ====
    "default_interpolation_parameters": {
        "function": "none",
        "factor": 1,
    },



    # ==== Themes ====
    "enable_theme": True,
    "theme": "dark_teal",  # <- Write key from "available_themes" here

    "available_themes": {
        # "dark_orange": "dark_orange.xml",
        "dark_amber": "dark_amber.xml",
        "dark_blue": "dark_blue.xml",
        "dark_cyan": "dark_cyan.xml",
        "dark_lightgreen": "dark_lightgreen.xml",
        "dark_medical": "dark_medical.xml",
        "dark_pink": "dark_pink.xml",
        "dark_purple": "dark_purple.xml",
        "dark_red": "dark_red.xml",
        "dark_teal": "dark_teal.xml",
        "dark_yellow": "dark_yellow.xml",
        "light_amber": "light_amber.xml",
        "light_blue_500": "light_blue_500.xml",
        "light_blue": "light_blue.xml",
        "light_cyan_500": "light_cyan_500.xml",
        "light_cyan": "light_cyan.xml",
        "light_lightgreen_500": "light_lightgreen_500.xml",
        "light_lightgreen": "light_lightgreen.xml",
        "light_orange": "light_orange.xml",
        "light_pink_500": "light_pink_500.xml",
        "light_pink": "light_pink.xml",
        "light_purple_500": "light_purple_500.xml",
        "light_purple": "light_purple.xml",
        "light_red_500": "light_red_500.xml",
        "light_red": "light_red.xml",
        "light_teal_500": "light_teal_500.xml",
        "light_teal": "light_teal.xml",
        "light_yellow": "light_yellow.xml",
    },




    # Lookup table for tab bar construction
    # TODO -> Requires use of exec() for .addAction() and .triggered.connect()
    "menu_dict": {
    },

    # Lookup table for tab bar construction
    "tab_dict": {
        0: {
            "name": "ConnectionWindow",
            "checkable": True,
            "icon": "./assets/icons/link.svg"
        },
        1: {
            "name": "CommandWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/sliders.svg"
        },
        2: {
            "name": "OrbitalWindow",
            "checkable": True,
            "icon": "./assets/icons/orbitB.svg"
        },
        # 3: {
        #     "name": "OrbitDesignWindow",
        #     "checkable": True,
        #     "icon": "./assets/icons/orbitB.svg"
        # },
        3: {
            "name": "GeneratorWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/activity.svg"
        },
        4: {
            "name": "WebcamWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/video.svg"
        },
        5: {
            "name": "ControlWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/sliders.svg"
        },
        6: {
            "name": "Tab 6",
            "checkable": True,
            "icon": "./assets/icons/feather/box.svg"
        },
        7: {
            "name": "Tab 7",
            "checkable": True,
            "icon": "./assets/icons/feather/info.svg"
        },
    },

    "default_tab": 2,

    # ==== Stylesheets for individual widgets ====
    "stylesheet_groupbox_smallmargins_notitle":
        ''' 
            QGroupBox {
                padding: 0px;
                padding-top: 0px;
            }
            QGroupBox::title {
                padding: 0px;
                height: 0px;
            }
        ''',
    "stylesheet_groupbox_smallmargins":
        ''' 
            QGroupBox {
                padding: 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                padding: 2px;
                height: 0px;
            }
        ''',
    "stylesheet_groupbox_hidden":
        ''' 
            QGroupBox {
                border: 0;
                padding: 0px;
                padding-top: 0px;
            }
            QGroupBox::title {
                border: 0;
                padding: 0px;
                height: 0px;
            }
        ''',


    "stylesheet_label_timestep":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: mono;
                font-size: 20px;
            }
        ''',

    "stylesheet_label_bmx_large":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ff0000;
                font-family: mono;
                font-size: 36px;
            }
        ''',
    "stylesheet_label_bmx_small":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ff0000;
                font-family: mono;
                font-size: 18px;
            }
        ''',
    "stylesheet_label_bmy_large":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: mono;
                font-size: 36px;
            }
        ''',
    "stylesheet_label_bmy_small":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: mono;
                font-size: 18px;
            }
        ''',
    "stylesheet_label_bmz_large":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #004bff;
                font-family: mono;
                font-size: 36px;
            }
        ''',
    "stylesheet_label_bmz_small":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #004bff;
                font-family: mono;
                font-size: 18px;
            }
        ''',
    "stylesheet_label_bm_large":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: mono;
                font-size: 36px;
            }
        ''',
    "stylesheet_label_bm_small":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: mono;
                font-size: 18px;
            }
        ''',
    "stylesheet_label_bmheader_small":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #999999;
                font-family: mono;
                font-size: 18px;
            }
        ''',

}

