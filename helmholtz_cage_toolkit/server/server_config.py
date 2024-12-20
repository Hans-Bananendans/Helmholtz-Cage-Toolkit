server_config = {
    # ==== General settings ====
    "SERVER_ADDRESS": "127.0.0.1",
    "SERVER_PORT": 7777,

    # ==== Thread settings ====
    "threaded_read_ADC_rate": 8,   # S/s
    "threaded_write_DAC_rate": 8,  # S/s
    "threaded_control_rate": 100, # Hz

    "internal_buffer_size": 5,
    "verbosity": 4,
    # "verbosity_printtimestamp": True,

    # ==== ADC settings ====
    "adc_pollrate": 30,     # S/s TODO DEPRECATED?

    # ==== DAC settings ====
    "vmax_dac": 5.0,        # V

    # ==== Settings for Bm mutation ====
    "mutate_Bm": False,
    "params_mutate": [
        [100, 100, 100],    # central value
        [0.1, 0.1, 0.1],    # mutation scale
        [0.5, 0.5, 0.5],    # fence strength
    ],

    # ==== Settings for Bm injection ====
    "inject_Bm": False,


    # ==== Power supply settings ====
    "vmax_supply": 30.0,    # V
    "imax_supply": 5.0,     # A
    "r_load": 7,            # Ohm
    "v_above": 2,           # V
    "i_above": 0.2,         # A

    "vlevel_pol": 5.0,      # V
    "v_psu_enable": 5.0,    # V

    "I_slew_max": [1000, 1000, 1000],    # [A/s] Maximum allowed current slew rate

    # ==== Playback settings ====
    "default_play_looping": True,

    # Linear regression coefficients for VC transfer function ([b0, b1] -> B_out = b0 + b1*V)
    "params_tf_VB_x": [0, 100],
    "params_tf_VB_y": [0, 100],
    "params_tf_VB_z": [0, 100],

    # Linear regression coefficients for VC transfer function ([a, b] -> v_cc = a*v + b)
    "params_tf_vc_x": [15.05305, -4.80750],
    "params_tf_vc_y": [15.05305, -4.80750],
    "params_tf_vc_z": [15.05305, -4.80750],

    # Linear regression coefficients for CC transfer function ([a, b] -> v_vc = a*i + b)
    "params_tf_cc_x": [2.000974, -0.012608],
    "params_tf_cc_y": [2.000974, -0.012608],
    "params_tf_cc_z": [2.000974, -0.012608],


    # ==== Hardware and cable routing ====
    # Note: Only pin mappings must start with 'pin_', otherwise config will not
    # be interpreted correctly by code elsewhere.
    "pin_adc_channel_imx": 0,
    "pin_adc_channel_imy": 1,
    "pin_adc_channel_imz": 2,

    "pin_adc_board_power": 3,

    "pin_adc_channel_bmx": 4,
    "pin_adc_channel_bmy": 5,
    "pin_adc_channel_bmz": 6,

    "pin_adc_aux1": 7,

    "pin_dac_supply_x_vcc": 3,
    "pin_dac_supply_x_vvc": 1,
    "pin_dac_supply_x_pol": 0,

    "pin_dac_supply_y_vcc": 7,
    "pin_dac_supply_y_vvc": 5,
    "pin_dac_supply_y_pol": 4,

    "pin_dac_supply_z_vcc": 11,
    "pin_dac_supply_z_vvc": 9,
    "pin_dac_supply_z_pol": 8,

    "pin_dac_psu_enable": 13, # TODO Rename to pin_dac_output_enable

    "pin_dac_aux1": 2,
    "pin_dac_aux2": 6,
    "pin_dac_aux3": 10,
    "pin_dac_aux4": 12,
    "pin_dac_aux5": 14,
    "pin_dac_aux6": 15,
    }