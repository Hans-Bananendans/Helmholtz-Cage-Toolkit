
class InterfaceBoard:
    def __init__(self, config):
        self.config = config
        pass

    # ========== ADC functions ==========
    def setup_adc_channels(self):
        pass

    def sort_adc_channels(self, adc_channels: list):
        pass

    @staticmethod
    def adc_raw_to_volts(val_raw):
        pass

    def adc_read(self, channel_id: int):
        pass

    def adc_read_multi(self, channel_ids, invert=False):
        pass

    # ========== DAC functions ==========
    def setup_dac_channels(self):
        pass

    def sort_dac_channels(self, dac_channels: list):
        pass

    def dac_write_voltage(self, channel_ids, voltage):
        pass

    def dac_all_channels_zero(self):
        pass

    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)


# ===== PowerSupply class ============
class PowerSupply:
    def __init__(self, config, interface_board,
                 channelid_activate, channelid_cv, channelid_cc):
        self.config = config
        pass

    def tf_cc_inv(self, v):
        pass

    def tf_cv_inv(self, v):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def set_zero_output(self):
        pass

    def set_current_out(self, current_out, timeout=0):
        pass

    def set_voltage_out(self, voltage_out, timeout=0):
        pass

    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)


# ===== Magnetometer class ============

class Magnetometer:
    def __init__(self, config, interface_board, channelid_bx, channelid_by, channelid_bz):
        self.config = config
        pass

    def read(self, convert_to_b=True):
        pass

    def tf_vm_bm(self, vm):
        """Converts milligaussmeter voltage readings into uT"""
        return vm * 100

    def log(self, verbosity_level, string):
        """Prints string to console when verbosity is above a certain level"""
        if verbosity_level <= self.config["verbosity"]:
            print(string)