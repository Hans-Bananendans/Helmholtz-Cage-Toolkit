from time import sleep
import sys
import adi
import numpy as np

from control_lib import *

_VERBOSE = 4

# ==== SETUP ====
cn0554_object = cn0554_setup()

adc_channels = adc_channel_setup(cn0554_object, verbose=_VERBOSE)
dac_channels = dac_channel_setup(cn0554_object, verbose=_VERBOSE)

supply1 = PowerSupply(dac_channels[0], 
                      dac_channels[2], 
                      dac_channels[4],
                      verbose=_VERBOSE)

# ==== LOOP ====
while True:

    command = input("Enter command (c/v, val, t): ")

    # Loop break commands
    if command in ("exit", "quit", "q"):
        supply1.set_zero_output(verbose=_VERBOSE)
        print("Quitting loop")
        break
    else:        
        # Parsing command into control variables
        [prop, value, t] = command.split(" ")
        [prop, value, t] = [prop, float(value), float(t)]

    if prop in ("c", "cc", "current"):
        supply1.set_current_out(value, timeout=t, verbose=_VERBOSE)
    elif prop in ("v", "cv", "voltage"):
        supply1.set_voltage_out(value, timeout=t, verbose=_VERBOSE)
    else:
        supply1.set_zero_output(verbose=_VERBOSE)
        print("ERROR: Inproper specifier for current/voltage (given: ", prop, ")")