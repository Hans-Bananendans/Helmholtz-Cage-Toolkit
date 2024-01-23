# Scans through all ADC channels and prints their output

# Imports

import numpy as np

from config import config

if config["use_dummies"]:
    print("Notice: Using dummy functions...")
    from dummy_functions import InterfaceBoard, PowerSupply, Magnetometer
else:
    from control_lib import InterfaceBoard, PowerSupply, Magnetometer

# def setup_cn0554(config, verbose=0):
#     interface_board = InterfaceBoard(config)
#     adc_channels = adc_channel_setup(cn0554_object, verbose=0)
#     dac_channels = dac_channel_setup(cn0554_object, verbose=0)
#     return cn0554_object, adc_channels, dac_channels

def setup_interface_board(config):

    interface_board = InterfaceBoard(config)
    return interface_board

def setup_supplies(config, interface_board):

    supply1 = PowerSupply(
        config,
        interface_board,
        config["dac_supply1_act"],
        config["dac_supply1_cc"],
        config["dac_supply1_vc"],

        # interface_board.dac_channels[config["dac_supply1_act"]],
        # interface_board.dac_channels[config["dac_supply1_cc"]],
        # interface_board.dac_channels[config["dac_supply1_vc"]],
    )
    supply2 = PowerSupply(
        config,
        interface_board,
        config["dac_supply2_act"],
        config["dac_supply2_cc"],
        config["dac_supply2_vc"],
    )
    supply3 = PowerSupply(
        config,
        interface_board,
        config["dac_supply3_act"],
        config["dac_supply3_cc"],
        config["dac_supply3_vc"],
    )

    return supply1, supply2, supply3
    
def setup_magnetometer(config, interface_board):
    magnetometer = Magnetometer(
        config,
        interface_board,
        config["adc_channel_bx"],
        config["adc_channel_by"],
        config["adc_channel_bz"],
        # interface_board.adc_channels[config["adc_channel_bx"]],
        # interface_board.adc_channels[config["adc_channel_by"]],
        # interface_board.adc_channels[config["adc_channel_bz"]],
    )
    return magnetometer

