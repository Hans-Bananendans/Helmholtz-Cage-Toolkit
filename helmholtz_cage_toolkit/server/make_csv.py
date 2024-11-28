import os
import csv
import numpy as np
from time import time

class DataBuffer:
    def __init__(self, header, 
                 filename="data.csv",
                 sampling_rate=100,
                 buffer_size=200):
        self.header = header

        self.path = os.getcwd()
        self.filename = filename
        self.filepath = os.path.join(self.path, self.filename)

        self.sampling_rate = sampling_rate
        self.sampling_interval = 1/self.sampling_rate

        self.buffer_size = buffer_size

        self.init_datafile()
        self.init_buffer()
    

    def init_datafile(self):
        """Create a new CSV file and write header"""
        with open(self.filepath, "w") as file:
            file.write(",".join(self.header) + "\n")


    # def save_data(self, data):
        
    #     with open(self.filepath, "a") as file:
    #         np.savetxt(file, data, fmt="%f", delimiter=",")

    # def init_buffer_old(size, dtype, header):
    #     if len(dtype) != len(header):
    #         raise ValueError("dtype and header not of same length!")
        
    #     dtype_spec = []
    #     for i in range(len(dtype)):
    #         dtype_spec.append((header[i], dtype[i]))
    #     return np.empty((size, len(header)), dtype=dtype_spec)

    def init_buffer(self):
        self.buffer = {}
        for item in self.header:
            self.buffer[item] = np.zeros(self.buffer_size)

    def save(self, VERBOSE=True):
        if VERBOSE:
            t0 = time()

        data = []
        for key in self.buffer.keys():
            data.append(self.buffer[key])

        with open(self.filepath, "a") as file:
            np.savetxt(file, np.array(data).transpose(), fmt="%f", delimiter=",")
        if VERBOSE:
            print(f"Saved buffer in {time()-t0} s ({self.sampling_rate} Hz, buffer size {self.buffer_size})")


# ==== Pre-formatting =========================================

filename = "dummy_data.csv"


# Make header
header = ["t", "Icx", "Icy", "Icz", "Bmx", "Bmy", "Bmz", "Rx", "Ry", "Rz"]
# header = ["t", "x"]


# sampling_rate = 100
# buffer_size = sampling_rate * 4

db = DataBuffer(header, filename=filename)
buffer = db.buffer


t_prev = time()

i = 0
while i < db.buffer_size:
    now = time()
    if (now-t_prev) >= db.sampling_interval:
        buffer["t"][i] = now
        buffer["Bmx"][i] = 10*np.sin(i)
        t_prev = now
        i += 1

db.save()