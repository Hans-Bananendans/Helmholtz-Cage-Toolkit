from time import sleep
import sys
import adi
import numpy as np

from helmholtz_cage_toolkit.server.control_lib import *
# from control_lib import *

_VERBOSE = 4

# ==== SETUP ====
cn0554_object = cn0554_setup()

adc_channels = adc_channel_setup(cn0554_object, verbose=_VERBOSE)
dac_channels = dac_channel_setup(cn0554_object, verbose=_VERBOSE)

supply1 = PowerSupply(dac_channels[0], 
                      dac_channels[2], 
                      dac_channels[4],
                      dac_channels[8],
                      verbose=_VERBOSE)

supply2 = PowerSupply(dac_channels[1], 
                      dac_channels[3], 
                      dac_channels[5],
                      dac_channels[10],
                      verbose=_VERBOSE)

supply3 = PowerSupply(dac_channels[9], 
                      dac_channels[11], 
                      dac_channels[13],
                      dac_channels[12],
                      verbose=_VERBOSE)

# ==== LOOP ====
while True:

    command = input("Reverse current signal (T/F): ")

    # Loop break commands
    if command in ("exit", "quit", "q"):
        supply1.set_zero_output(verbose=_VERBOSE)
        supply2.set_zero_output(verbose=_VERBOSE)
        supply3.set_zero_output(verbose=_VERBOSE)
        print("Quitting loop")
        break
    else:
        r = command.split(" ")

    for i, supply in enumerate((supply1, supply2, supply3)):
        if r[i] == "T":
            supply.reverse_polarity(True)
        else:
            supply.reverse_polarity(False)

    # else:
    #     supply1.set_zero_output(verbose=_VERBOSE)
    #     print("ERROR: Inproper command:", command, ")")