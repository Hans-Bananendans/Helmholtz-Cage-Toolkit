config = {
    "APPNAME": "Helmholtz Cage Toolkit",
    "VERSION": "0.0.1",

    # ==== General settings ====
    "verbosity": 1,
    "use_dummies": True,
    "default_windowsize": (1280, 720),
    "enable_skin": True,


    # ==== TCP connection settings ====
    "server_address": "127.0.0.1",
    "server_port": 7777,
    "buffer_size": 1024,
    "connect_on_startup": False,


    # ==== ADC settings ====
    "adc_pollrate": 30,


    # ==== DAC settings ====
    "vmax_dac": 5.0,  # VDC


    # ==== Power supply settings ====
    "vmax_supply": 60.0,  # VDC
    "imax_supply": 5.0,  # A


    # ==== Hardware and cable routing ====
    "adc_channel_bx": 0,
    "adc_channel_by": 1,
    "adc_channel_bz": 2,

    "dac_supply1_act": 0,
    "dac_supply1_cc": 2,
    "dac_supply1_vc": 4,

    "dac_supply2_act": 1,
    "dac_supply2_cc": 3,
    "dac_supply2_vc": 5,

    "dac_supply3_act": 8,
    "dac_supply3_cc": 10,
    "dac_supply3_vc": 12,


    # ==== Plotwindow settings ====
    "hhcplot_windowsize": (560, 220),
    "visualizer_windowsize": (560, 120),
    "visualizer_bscale": 100_000,
    "visualizer_updaterate": 30,


    # ==== LCD box styling ====
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


    # ==== Orbit Visualizer ====
    "ov_plotcolours": ("#ff00ffff", "#ff8000ff", "#00ffffff", "#ffff00ff", "#00ff00ff"),
    "ov_preferred_colour": 1,
    "ov_draw_B_vector": True,
    "ov_plotscale": 1E7,
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

    # "ov_draw": {
    #     "XY_grid": True,
    #     "tripod_ECI": True,
    #     "tripod_ECEF": False,
    #     "tripod_NED": False,
    #     "tripod_SI": False,
    #     "tripod_B": False,
    #     "earth_model": True,
    #     "satellite": False,
    #     "satellite_helpers": False,
    #     "position_vector": False,
    #     "orbit_lineplot": False,
    #     "orbit_scatterplot": False,
    #     "orbit_helpers": False,
    #     "velocity_vector": False,
    #     "B_vector": False,
    #     "B_fieldgrid_lineplot": True,
    #     "B_fieldgrid_scatterplot": False,
    #     },
    "ov_draw": {
        "XY_grid": True,
        "tripod_ECI": True,
        "tripod_ECEF": False,
        "tripod_NED": False,
        "tripod_SI": True,
        "tripod_B": False,
        "earth_model": True,
        "satellite": True,
        "satellite_helpers": True,
        "position_vector": True,
        "orbit_lineplot": True,
        "orbit_scatterplot": False,
        "orbit_helpers": True,
        "velocity_vector": False,
        "B_vector": True,
        "B_fieldgrid_lineplot": False,
        "B_fieldgrid_scatterplot": False,
    },
    "ov_anim": {
        "tripod_ECEF": True,
        "tripod_NED": True,
        "tripod_SI": True,
        "tripod_B": True,
        "earth_model": True,
        "satellite": True,
        "satellite_helpers": True,
        "position_vector": True,
        "velocity_vector": True,
        "B_vector": True,
        },
    "ov_rotate_earth": True,
    "ov_earth_model_smoothing": True,
    "ov_use_antialiasing": True,
    "ov_endpatching": True,


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
            "name": "ControlWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/sliders.svg"
        },
        2: {
            "name": "OrbitDesignWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/disc.svg"
        },
        3: {
            "name": "GeneratorWindow",
            "checkable": True,
            "icon": "./assets/icons/feather/activity.svg"
        },
        4: {
            "name": "Tab 4",
            "checkable": True,
            "icon": "./assets/icons/feather/box.svg"
        },
        5: {
            "name": "Tab 5",
            "checkable": True,
            "icon": "./assets/icons/feather/box.svg"
        },
        6: {
            "name": "Tab 6",
            "checkable": True,
            "icon": "./assets/icons/feather/info.svg"
        },
    },

    "default_tab": 0,

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

    "stylesheet_label_timestep":
        ''' 
            QLabel {
                background-color: #0a0a0a;
                color: #ffffff;
                font-family: mono;
                font-size: 20px;
            }
        ''',

}
