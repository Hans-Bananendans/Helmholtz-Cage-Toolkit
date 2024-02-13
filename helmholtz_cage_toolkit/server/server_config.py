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

    # ==== Hardware and cable routing ====
    # Note: Only pin mappings must start with 'pin_', otherwise config will not
    # be interpreted correctly by code elsewhere.
    "pin_adc_channel_bmx": 0,
    "pin_adc_channel_bmy": 1,
    "pin_adc_channel_bmz": 2,

    "pin_adc_channel_imx": 4,
    "pin_adc_channel_imy": 5,
    "pin_adc_channel_imz": 6,

    "pin_adc_board_power": 7,

    "pin_dac_supply1_act": 0,
    "pin_dac_supply1_vcc": 2,
    "pin_dac_supply1_vvc": 4,
    "pin_dac_supply1_pol": 6,

    "pin_dac_supply2_act": 1,
    "pin_dac_supply2_vcc": 3,
    "pin_dac_supply2_vvc": 5,
    "pin_dac_supply2_pol": 7,

    "pin_dac_supply3_act": 8,
    "pin_dac_supply3_vcc": 10,
    "pin_dac_supply3_vvc": 12,
    "pin_dac_supply3_pol": 14,
    }