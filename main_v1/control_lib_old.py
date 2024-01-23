# Scans through all ADC channels and prints their output

# Imports
import sys
import adi
import numpy as np
from time import time, sleep
import matplotlib.pyplot as plt

global _PRINT_READOUT
_PRINT_READOUT = False

global _REFRESH_RATE
_REFRESH_RATE = 50

# ===== ADC Setup ============
def adc_channel_sort(channel_list: list):
    """
    Takes the list of PyADI ADC channels of the AD7124-8 and sorts it such
    that the channel numbers correspond to the list entry positions.
    """
    channel_list += [channel_list.pop(1)] # move voltage1011 to the back
    channel_list += [channel_list.pop(1)] # move voltage1213 to the back
    channel_list += [channel_list.pop(1)] # move voltage1415 to the back
    return channel_list

def adc_raw_to_volts(val_raw, 
                     offset=-8388726, 
                     calib_scale=3.378301E-6,  # See calibration doc for details
                     rounding=None):
    """
    Can be used to convert raw ADC measurements into voltages according to personal
    calibration performed.

    Refer to the calibration documentation for details
    """
    if rounding:
        return round((val_raw+offset) * calib_scale, rounding)
    else:
        return (val_raw+offset) * calib_scale

def adc_reading(channel):
    """Perform a single measurement on a single ADC channel."""
    return adc_raw_to_volts(channel.raw)

def adc_measurement(channels, invert=False):
    """
    Perform single measurements on all specified channels, and return
    the results, along with a unix timestamp.
    """
    
    measurement = []
    timestamp = time()
    if invert:
        for chan in channels:
            measurement.append(-1*adc_reading(chan))
    else:
        for chan in channels:
            measurement.append(adc_reading(chan))   
    return measurement, timestamp

def adc_channel_setup(cn0554_object, verbose=0):
    # Verbose feedback
    if verbose >= 1:
        print("adc_channel_setup(): Initializing ADC channels...")

    # Sort the channels (once and once only!)
    adc_channels = adc_channel_sort(cn0554_object.adc.channel)

    return adc_channels


# ===== DAC Setup ============
def dac_channel_sort(channel_list: list):
    """
    Takes the list of PyADI DAC channels of the LTC2688 and sorts it such
    that the channel numbers correspond to the list entry positions.
    """
    for i in range(6):
        # Move voltage10 through voltage15 to back of the list
        channel_list += [channel_list.pop(2)]
    return channel_list

def dac_channel_setup(cn0554_object, verbose=0):
    """
    Takes a CN0554 object and returns a sorted list of its DAC channel objects.
    """

    # Verbose feedback
    if verbose >= 1:
        print("dac_channel_setup(): Initializing DAC channels...")

    # Fetch DAC channel names
    dac_channel_names = cn0554_object.dac.channel_names

    # Sort channels (move voltage10 through voltage15 to back of the list)
    dac_channel_names = dac_channel_sort(dac_channel_names)
    
    # Assemble a list with the instantiated channel objects
    dac_channels = []
    for i, name in enumerate(dac_channel_names):
        dac_channels.append(eval("cn0554_object.dac."+str(name)))

    # Verbose feedback
    if verbose >= 2:
        for chan in dac_channels:
            print("Initialized:", str(chan.name).ljust(9), ":", chan)

    # Return list of instantiated channel objects
    return dac_channels

def dac_set_voltage(channels, value, verbose=0):
    """
    Take one or multiple DAC channels, and set it to a specific voltage in [V]
    """

    # If a single channel entry is given without a list/array, put it in one.
    if type(channels) not in (list, tuple, np.ndarray):
        channels = [channels]

    # Disallow values outside of [0, 5] VDC    
    if value > 5 or value < 0:
        raise ValueError("Error: set_dac_voltage only accepts [0, 5] V!")
    
    # Map voltage value to corresponding raw value
    offset = -32768
    scale = 0.457763671E-3
    # Last terms are a quick and dirty calibration correction
    value_raw = int(((value / scale) - offset) + value + 1.5)

    # Safety measure:
    # Hard-clipping raw values to preventing overvoltage
    if value_raw < 32768:
        value_raw = 32768
    if value_raw > 43697:
        value_raw = 43697

    # Apply value to channels
    for chan in channels:
        if verbose >= 2:
            print("set_dac_voltage(): Setting voltage of", 
                  chan.name, "to", value, "V (",value_raw,")")
        chan.raw = value_raw

def dac_set_channels_zero(dac_channels, verbose=0):
    """
    Convenience function to set all specified DAC channels to zero volt output.
    """
    dac_set_voltage(dac_channels, 0.0, verbose=0)
    
    if verbose >= 2:
        print("set_channels_zero(): Set all DAC channels to 0 V")


# ===== CN0554 Setup ============
def cn0554_setup():
    """
    Instantiates a PyADI CN0554 object
    """
    board = adi.cn0554()

    return board

# ===== PowerSupply class ============

class PowerSupply:
    """
    Class for abstracting the configuration of a BK Precision 1685B power supply 
    through three LMC2688 DAC channels.
    """
    def __init__(self, channel_activate, channel_cv, channel_cc, vmax=5.0, verbose=0):
        self.channel_activate = channel_activate
        self.channel_cv = channel_cv
        self.channel_cc = channel_cc

        self.vmax = vmax

        # Provide power to the internal +5VDC pin on the power supply
        self.activate(verbose=verbose)

        # Always set channels to zero at the start
        self.set_zero_output(verbose=verbose)

    def tf_cc_inv(self, v):
        """
        Power supply transfer function that specifies the current channel input 
        voltage required for a desired output current. The output voltage limit
        is set to maximum, so that the power supply itself picks the appropriate
        voltage to achieve the desired output current. Uses a linear regression 
        correction found by personal measurements.
        """
        return (v + 0.6652)/1.6982

    def tf_cv_inv(self, v):
        """
        Power supply transfer function that specifies the current channel input 
        voltage required for a desired output voltage. Uses a linear regression 
        correction found by personal measurements.
        """
        return (v + 4.8973)/14.9116

    def activate(self, verbose=0):
        """
        Activates control of the given power supply through the activation
        DAC channel.
        """

        dac_set_voltage(self.channel_activate, 5.0, verbose=verbose)

        if verbose >= 1:
            print("activate(): Activated power supply", self)

    def deactivate(self, verbose=0):
        """
        Deactivates control of the given power supply through the activation
        DAC channel.
        """

        # First set outputs to zero
        self.set_zero_output(verbose=verbose)
        
        # Then set internal +5VDC channel to zero
        dac_set_voltage(self.channel_activate, 0.0, verbose=verbose)

        if verbose >= 1:
            print("deactivate(): Deactivated power supply", self)
        pass

    def set_zero_output(self, verbose=0):
        dac_set_channels_zero([self.channel_cv, self.channel_cc], verbose=verbose)   

    def set_current_out(self, current_out, timeout=0, verbose=0):
        """
        Sets a specific output current on the power supply using the current
        control channel. The output voltage limit is set to maximum, so that 
        the power supply itself picks the appropriate voltage to achieve the 
        desired output current.
        
        current_out         Desired output current in [A]
        timeout             Specify a time [s] after which the set current
                            returns to zero. If set to 0, timeout is disabled.
        """

        dac_set_voltage(self.channel_cv, self.vmax, verbose=verbose)
        dac_set_voltage(self.channel_cc, self.tf_cc_inv(current_out), verbose=verbose)

        # TODO: Remove timeout functionality in favour of an application-driven
        # threaded alternative (non-blocking alternatives to sleep()).
        if timeout > 0:
            sleep(timeout)
            dac_set_voltage(self.channel_cv, 0, verbose=0)
            dac_set_voltage(self.channel_cc, 0, verbose=0)
            if verbose >= 2:
                print("Timed shut-off after", timeout, "s")

    def set_voltage_out(self, voltage_out, timeout=0, verbose=0):
        """
        Sets a specific output voltage on the power supply using the voltage
        control channel. The output current limit is set to maximum, so that 
        the power supply itself picks the appropriate current to achieve the 
        desired output voltage.
        
        voltage_out         Desired output voltage in [V]
        timeout             Specify a time [s] after which the set current
                            returns to zero. If set to 0, timeout is disabled.
        """

        dac_set_voltage([self.channel_cv], self.tf_cv_inv(voltage_out), verbose=verbose)
        dac_set_voltage([self.channel_cc], self.vmax, verbose=verbose)

        # TODO: Remove timeout functionality in favour of an application-driven
        # threaded alternative (non-blocking alternatives to sleep()).
        if timeout > 0:
            sleep(timeout)
            dac_set_voltage(self.channel_cv, 0, verbose=0)
            dac_set_voltage(self.channel_cc, 0, verbose=0)
            if verbose >= 2:
                print("Timed shut-off after", timeout, "s")


# ===== Magnetometer class ============

class Magnetometer:
    """
    Class for abstracting the configuration of an AlphaLab analog
    milligaussmeter through three differential AD7124-8 DAC channels.
    """
    def __init__(self, channel_bx, channel_by, channel_bz, verbose=0):
        self.channel_bx = channel_bx
        self.channel_by = channel_by
        self.channel_bz = channel_bz
        self.channels = (self.channel_bx, self.channel_by, self.channel_bz)
        # self.vmax = 5.0

    def measurement(self, convert_to_b=True):

        m = adc_measurement(self.channels, invert=True)

        if convert_to_b:
            return ([self.tf_vm_bm(vm) for vm in m[0]], m[1])
        else:
            return m

    def tf_vm_bm(self, vm):
        """Converts milligaussmeter voltage readings into uT"""
        return vm*100