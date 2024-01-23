# Scans through all ADC channels and prints their output

# Imports
import adi
import numpy as np
from time import time, sleep


# ===== InterfaceBoard class ============

class InterfaceBoard:
    def __init__(self, config):
        # Import config
        self.config = config

        # Instantiate a PyADI CN0554 object
        self.board = adi.cn0554()
        self.log(1, "InterfaceBoard: Instantiated PyADI CN0554 object")

        # Set up ADC channels
        self.adc_channels = self.setup_adc_channels()
        self.log(1, "InterfaceBoard: Initialized ADC channels")

        self.dac_channels = self.setup_dac_channels()
        self.log(1, "InterfaceBoard: Initialized DAC channels")

        # self.log(0, f"[DEBUG] self.dac_channels: {self.dac_channels}")

    # ========== ADC functions ==========
    def setup_adc_channels(self):
        self.log(1, "InterfaceBoard: Initializing ADC channels...")
        return self.sort_adc_channels(self.board.adc.channel)


    def sort_adc_channels(self, adc_channels: list):
        """
        Takes the list of PyADI ADC channels of the AD7124-8 and sorts it such
        that the channel numbers correspond to the list entry positions.
        """
        self.log(2, "InterfaceBoard: Sorting ADC channels...")
        adc_channels += [adc_channels.pop(1)]  # move voltage1011 to the back
        adc_channels += [adc_channels.pop(1)]  # move voltage1213 to the back
        adc_channels += [adc_channels.pop(1)]  # move voltage1415 to the back

        return adc_channels


    @staticmethod
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


    def adc_read(self, channel_id: int):
        """Perform a single measurement on a single ADC channel."""
        self.log(4, f"InterfaceBoard: Performing single read on ADC channel {channel_id}...")
        return self.adc_raw_to_volts(self.adc_channels[channel_id].raw)


    def adc_read_multi(self, channel_ids, invert=False):
        """
        Perform single measurements on all specified channels, and return
        the results, along with a unix timestamp.
        """
        self.log(4, f"InterfaceBoard: Attempting reads on ADC channels {channel_ids}...")
        measurement = []
        timestamp = time()
        if invert:
            for channel_id in channel_ids:
                measurement.append(-1*self.adc_read(channel_id))
        else:
            for channel_id in channel_ids:
                measurement.append(self.adc_read(channel_id))
        return measurement, timestamp


    # ========== DAC functions ==========
    def setup_dac_channels(self):
        """
        Takes a CN0554 object and returns a sorted list of its DAC channel objects.
        """
        self.log(1, "InterfaceBoard: Initializing DAC channels...")

        # Fetch DAC channel names
        dac_channel_names = self.board.dac.channel_names

        # Sort channels (move voltage10 through voltage15 to back of the list)
        dac_channel_names = self.sort_dac_channels(dac_channel_names)

        # Assemble a list with the instantiated channel objects
        dac_channels = []
        for i, name in enumerate(dac_channel_names):
            dac_channels.append(eval("self.board.dac." + str(name)))

        # Verbose feedback
        for chan in dac_channels:
            self.log(2, f"Initialized: {str(chan.name).ljust(9)} : {chan}")

        # Return list of instantiated channel objects
        return dac_channels


    def sort_dac_channels(self, dac_channels: list):
        """
        Takes the list of PyADI DAC channels of the LTC2688 and sorts it such
        that the channel numbers correspond to the list entry positions.
        """
        self.log(2, "InterfaceBoard: Sorting DAC channels...")
        for i in range(6):
            # Move voltage10 through voltage15 to back of the list
            dac_channels += [dac_channels.pop(2)]

        return dac_channels

    def dac_write_voltage(self, channel_ids, voltage):
        """
        Take one or multiple DAC channels, and set it to a specific voltage in [V]
        """

        self.log(4, f"InterfaceBoard: Writing {voltage} V to channels {channel_ids}...")

        # If a single channel entry is given without a list/array, put it in one.
        if type(channel_ids) not in (list, tuple, np.ndarray):
            channel_ids = [channel_ids]

        # Disallow values outside of [0, vmax] VDC
        vmax = self.config["vmax_dac"]
        if voltage > vmax or voltage < 0:
            raise ValueError(f"Error: dac_write_voltage() only accepts [0, {vmax}] V!")

        # Map voltage value to corresponding raw value
        offset = -32768
        scale = 0.457763671E-3
        # Last terms are a quick and dirty calibration correction
        value_raw = int(((voltage / scale) - offset) + voltage + 1.5)

        # Safety measure:
        # Hard-clipping raw values to preventing overvoltage
        if value_raw < 32768:
            value_raw = 32768
        if value_raw > 43697:
            value_raw = 43697

        # Apply value to channels
        for channel_id in channel_ids:
            self.dac_channels[channel_id].raw = value_raw
            self.log(2, f"dac_write_voltage() Set dac channel {channel_id} to {voltage} V ({value_raw})")


    def dac_all_channels_zero(self):
        """
        Convenience function to set all specified DAC channels to zero volt output.
        """
        for channel_id in range(16):
            self.dac_write_voltage(self.dac_channels, 0.0)
            # self.dac_write_voltage(channel_id, 0.0)

        self.log(2, "set_channels_zero(): Set all DAC channels to 0 V")


    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        
        # print(f"[DEBUG] verbosity_level: {verbosity_level} -- config verbosity: {self.config['verbosity']}")
        if verbosity_level <= self.config["verbosity"]:
            print(string)


# ===== PowerSupply class ============

class PowerSupply:
    """
    Class for abstracting the configuration of a BK Precision 1685B power supply 
    through three LMC2688 DAC channels.
    """
    def __init__(self, config, interface_board,
                 channelid_activate, channelid_cv, channelid_cc):
        # Import config
        self.config = config

        self.ib = interface_board

        self.channelid_activate = channelid_activate
        self.channelid_cv = channelid_cv
        self.channelid_cc = channelid_cc

        self.vmax_dac = self.config["vmax_dac"]
        self.vmax_supply = self.config["vmax_supply"]
        self.imax_supply = self.config["imax_supply"]

        # Provide power to the internal +5VDC pin on the power supply
        self.activate()

        # Always set channels to zero at the start
        self.set_zero_output()


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


    def activate(self):
        """
        Activates control of the given power supply through the activation
        DAC channel.
        """
        self.ib.dac_write_voltage(self.channelid_activate, self.vmax_dac)
        self.log(1, f"PowerSupply: Activated power supply {self}")


    def deactivate(self):
        """
        Deactivates control of the given power supply through the activation
        DAC channel.
        """

        # First set outputs to zero
        self.set_zero_output()
        
        # Then set internal +5VDC channel to zero
        self.ib.dac_write_voltage(self.channelid_activate, 0.0)

        self.log(1, f"PowerSupply: Deactivated power supply {self}")


    def set_zero_output(self):
        self.ib.dac_write_voltage([self.channelid_cv, self.channelid_cc], 0.0)


    def set_current_out(self, current_out, timeout=0):
        """
        Sets a specific output current on the power supply using the current
        control channel. The output voltage limit is set to maximum, so that 
        the power supply itself picks the appropriate voltage to achieve the 
        desired output current.
        
        current_out         Desired output current in [A]
        timeout             Specify a time [s] after which the set current
                            returns to zero. If set to 0, timeout is disabled.
        """
        # Set voltage channel to max
        self.ib.dac_write_voltage(self.channelid_cv, self.tf_cv_inv(self.vmax_supply))
        # Set current as desired
        self.ib.dac_write_voltage(self.channelid_cc, self.tf_cc_inv(current_out))

        # TODO: Remove timeout functionality in favour of an application-driven
        # TODO:  threaded alternative (non-blocking alternatives to sleep()).
        if timeout > 0:
            sleep(timeout)
            self.set_zero_output()
            self.log(2, f"Timed shut-off after {timeout} s")


    def set_voltage_out(self, voltage_out, timeout=0):
        """
        Sets a specific output voltage on the power supply using the voltage
        control channel. The output current limit is set to maximum, so that 
        the power supply itself picks the appropriate current to achieve the 
        desired output voltage.
        
        voltage_out         Desired output voltage in [V]
        timeout             Specify a time [s] after which the set current
                            returns to zero. If set to 0, timeout is disabled.
        """
        # Set current channel to max
        self.ib.dac_write_voltage(self.channelid_cc, self.tf_cc_inv(self.imax_supply))
        # Set voltage as desired
        self.ib.dac_write_voltage(self.channelid_cv, self.tf_cv_inv(voltage_out))

        # TODO: Remove timeout functionality in favour of an application-driven
        # TODO:  threaded alternative (non-blocking alternatives to sleep()).
        if timeout > 0:
            sleep(timeout)
            self.set_zero_output()
            self.log(2, f"Timed shut-off after {timeout} s")


    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)


# ===== Magnetometer class ============

class Magnetometer:
    """
    Class for abstracting the configuration of an AlphaLab analog
    milligaussmeter through three differential AD7124-8 DAC channels.
    """
    def __init__(self, config, interface_board, channelid_bx, channelid_by, channelid_bz):
        # Import config
        self.config = config

        self.ib = interface_board

        self.channelid_bx = channelid_bx
        self.channelid_by = channelid_by
        self.channelid_bz = channelid_bz
        self.channelids = (self.channelid_bx, self.channelid_by, self.channelid_bz)


    def read(self, convert_to_b=True):

        m = self.ib.adc_read_multi(self.channelids, invert=True)

        self.log(4, f"Performing measurement (convert to B: {convert_to_b})")
        if convert_to_b:
            return [self.tf_vm_bm(vm) for vm in m[0]], m[1]
        else:
            return m


    def tf_vm_bm(self, vm):
        """Converts milligaussmeter voltage readings into uT"""
        return vm*100


    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)