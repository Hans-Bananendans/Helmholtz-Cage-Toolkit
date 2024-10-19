server_config = {
    # ==== General settings ====
    # "SERVER_ADDRESS": "127.0.0.1",
    "SERVER_PORT": 7777,


    "verbosity": 6,
    # "verbosity_printtimestamp": True,


    # ==== ADC settings ====
    "adc_pollrate": 30,  # TODO STALE

    # ==== DAC settings ====
    "vmax_dac": 5.0,  # VDC  # TODO STALE

    # ==== Power supply settings ====
    "vmax_supply": 60.0,  # VDC  # TODO STALE
    "imax_supply": 5.0,  # A  # TODO STALE

    "vlevel_pol": 5.0,  # VDC

    # Linear regression coefficients for VC transfer function ([a, b] -> v_cc = a*v + b)
    "params_tf_vc_x": [15.05305, -4.80750],
    "params_tf_vc_y": [15.05305, -4.80750],
    "params_tf_vc_z": [15.05305, -4.80750],

    # Linear regression coefficients for CC transfer function ([a, b] -> v_vc = a*i + b)
    "params_tf_cc_x": [1.7260, -0.6736],
    "params_tf_cc_y": [1.7260, -0.6736],
    "params_tf_cc_z": [1.7260, -0.6736],

    # ==== Hardware and cable routing ====
    # Note: Only pin mappings must start with 'pin_', otherwise config will not
    # be interpreted correctly by code elsewhere.
    "pin_adc_channel_bmx": 4,
    "pin_adc_channel_bmy": 5,
    "pin_adc_channel_bmz": 6,

    "pin_adc_channel_imx": 0,
    "pin_adc_channel_imy": 1,
    "pin_adc_channel_imz": 2,

    "pin_adc_board_power": 3,

    "pin_dac_supply_x_act": 10,
    "pin_dac_supply_x_vcc": 3,
    "pin_dac_supply_x_vvc": 1,
    "pin_dac_supply_x_pol": 0,

    "pin_dac_supply_y_act": 12,
    "pin_dac_supply_y_vcc": 7,
    "pin_dac_supply_y_vvc": 5,
    "pin_dac_supply_y_pol": 4,

    "pin_dac_supply_z_act": 14,
    "pin_dac_supply_z_vcc": 11,
    "pin_dac_supply_z_vvc": 9,
    "pin_dac_supply_z_pol": 8,

    # "pin_dac_supply_x_act": 0,
    # "pin_dac_supply_x_vcc": 2,
    # "pin_dac_supply_x_vvc": 4,
    # "pin_dac_supply_x_pol": 6,

    # "pin_dac_supply_y_act": 1,
    # "pin_dac_supply_y_vcc": 3,
    # "pin_dac_supply_y_vvc": 5,
    # "pin_dac_supply_y_pol": 7,

    # "pin_dac_supply_z_act": 8,
    # "pin_dac_supply_z_vcc": 10,
    # "pin_dac_supply_z_vvc": 12,
    # "pin_dac_supply_z_pol": 14,

    }