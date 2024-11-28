import os
import sys
import datetime

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.server.server_config import server_config as config
from helmholtz_cage_toolkit.server.control_lib import *
from helmholtz_cage_toolkit.server.databuffer import DataBuffer

from time import time
from numpy import sin, pi, linspace
from scipy.signal import sawtooth, square


class Controller:
    def __init__(self, config):

        self.initialize_devices()
        self.reset()

    def initialize_devices(self):
        print("[DEBUG] initialize_devices()")

        _VERBOSE = 6
        self.cn0554_object = cn0554_setup()

        self.adc_channels = adc_channel_setup(self.cn0554_object, verbose=_VERBOSE)
        print("ADC CHANNELS: ", type(self.adc_channels), self.adc_channels)
        self.dac_channels = dac_channel_setup(self.cn0554_object, verbose=_VERBOSE)

        self.magnetometer = Magnetometer(
            self.adc_channels[config["pin_adc_channel_bmx"]], 
            self.adc_channels[config["pin_adc_channel_bmy"]], 
            self.adc_channels[config["pin_adc_channel_bmz"]]
        )

        self.supply_x = PowerSupply(self.dac_channels[config["pin_dac_supply_x_act"]], 
                                    self.dac_channels[config["pin_dac_supply_x_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_x_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_x_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    params_tf_vc=config["params_tf_vc_x"],
                                    params_tf_cc=config["params_tf_cc_x"],
                                    verbose=_VERBOSE)

        self.supply_y = PowerSupply(self.dac_channels[config["pin_dac_supply_y_act"]], 
                                    self.dac_channels[config["pin_dac_supply_y_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_y_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_y_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    params_tf_vc=config["params_tf_vc_y"],
                                    params_tf_cc=config["params_tf_cc_y"],
                                    verbose=_VERBOSE)

        self.supply_z = PowerSupply(self.dac_channels[config["pin_dac_supply_z_act"]], 
                                    self.dac_channels[config["pin_dac_supply_z_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_z_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_z_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    params_tf_vc=config["params_tf_vc_z"],
                                    params_tf_cc=config["params_tf_cc_z"],
                                    verbose=_VERBOSE)
        self.supplies = (self.supply_x, self.supply_y, self.supply_z)
        

    def reset(self):
        print("[DEBUG] reset()")
        for supply in (self.supply_x, self.supply_y, self.supply_z):
            supply.set_zero_output(verbose=6)
        print("SUCCESS")



# class DataRecorder:
#     def __init__(self, 
#                  len_buffer=1024,
#                  default_name="output"):
#         self.len_buffer = len_buffer
#         self.default_name = default_name

#         self.initialize_buffer()


#     def initialize_buffer(self):
#         self.buffer = [None]*self.len_buffer


#     def add_datapoint(data: list):
#         line = ""
#         for item in data:
#             line += str(item) + ","
        

#     def generate_filename(self):
#         name = self.default_name.replace(" ", "_")
#         timestamp = str(datetime.utcfromtimestamp(time()).strftime("%Y-%m-%d_%H.%M.%S"))
#         filename = name + "_" + timestamp + ".dat"
#         return filename



if __name__ == "__main__":
    # Configure data recording
    filename = "data.csv"
    header = ["t", "Icx", "Icy", "Icz", "Bmx", "Bmy", "Bmz", "Px", "Py", "Pz"]

    do_record = False

    db = DataBuffer(
        header,
        filename=filename,
        sampling_rate=64,
        buffer_size=256)

    # Configure signal generator
    c = Controller(config)

    # psus = [0, 1, 2]
    psus = [1,]

    n = 1               #  [Hz]
    period = 20          #  [s]
    amplitude = 1       #  [A]
    offset = 0         #  [A]

    function = "square"

    sin_vals = []
    tri_vals = []
    saw_vals = []
    sq_vals = []

    control_interval = period/n

    times = linspace(0, 1, n, endpoint=False)

    for i in range(n):
        sin_vals.append(amplitude * sin(2*pi*i/n) + offset)
    
    sq_vals = list(amplitude*square(2*pi*times)+offset)
    # print("sq_vals", sq_vals, type(sq_vals))

    saw_vals = list(amplitude*sawtooth(2*pi*times, 1.0)+offset)
    # print("saw_vals", saw_vals, type(saw_vals))

    tri_vals = list(amplitude*sawtooth(2*pi*times, 0.5)+offset)
    # print("tri_vals", tri_vals, type(tri_vals))


    i = 0

    if function == "sine":
        f_vals = sin_vals
    elif function == "triangle":
        f_vals = tri_vals
    elif function == "square":
        f_vals = sq_vals
    elif function == "sawtooth":
        f_vals = saw_vals
    else:
        fvals = [0,]
        print("Error - Invalid function specified!")

    print("Running...")

    tm_prev = time()
    tc_prev = time()
    bi = 0  # Buffer entry index
    while True:
        try:
            now = time()

            # Save and initialize buffer if it is full
            if bi == db.buffer_size and do_record:
                db.save()
                db.init_buffer()
                bi = 0


            if (now-tm_prev) >= db.sampling_interval and do_record:
                db.buffer["t"][bi] = now
                db.buffer["Icx"][bi] = c.supplies[0].i
                db.buffer["Icy"][bi] = c.supplies[1].i
                db.buffer["Icz"][bi] = c.supplies[2].i

                db.buffer["Px"][bi] = c.supplies[0].pol
                db.buffer["Py"][bi] = c.supplies[1].pol
                db.buffer["Pz"][bi] = c.supplies[2].pol

                adc_inputs, _ = adc_measurement(c.adc_channels)
                bvals = [adc_inputs[config["pin_adc_channel_bmx"]]*100,
                         adc_inputs[config["pin_adc_channel_bmy"]]*100, 
                         adc_inputs[config["pin_adc_channel_bmz"]]*100]

                # Bm = c.magnetometer.read_B()
                db.buffer["Bmx"][bi] = bvals[0]
                db.buffer["Bmy"][bi] = bvals[1]
                db.buffer["Bmz"][bi] = bvals[2]

                bi += 1
                tm_prev = now

            if (now-tc_prev) >= control_interval:
                for psu_id in psus:
                    # c.supplies[psu_id].set_current_out(f_vals[i])
                    if f_vals[i] < 0.0:
                        c.supplies[psu_id].reverse_polarity(True)
                        # print("polarity REVERSED")
                    else:
                        c.supplies[psu_id].reverse_polarity(False)
                        # print("polarity NORMAL")

                    c.supplies[psu_id].set_current_out(abs(f_vals[i]))

                # print(f"Set current to {sin_vals[i]} A")
                i = divmod(i+1, n)[1]
                tc_prev = now
                

        except KeyboardInterrupt:
            c.reset()
            print("Graceful shutdown by KeyboardInterrupt")
            break
