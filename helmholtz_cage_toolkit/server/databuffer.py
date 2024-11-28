import os
import numpy as np
from time import time

class DataBuffer:
    """Data buffer object for convenient data recording"""
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

        # self.data_fmt = ["%f",]*len(self.header)

        self.init_datafile()
        self.init_buffer()
    

    def init_datafile(self):
        """Create a new CSV file and write header"""
        with open(self.filepath, "w") as file:
            file.write(",".join(self.header) + "\n")


    def init_buffer(self):
        """Create an empty buffer"""
        self.buffer = {}
        for item in self.header:
            self.buffer[item] = np.zeros(self.buffer_size)


    def save(self, VERBOSE=True):
        """Any data that has been written to the buffer will be saved to the output file"""
        if VERBOSE:
            t0 = time()

        data = []
        for key in self.buffer.keys():
            data.append(self.buffer[key])
        with open(self.filepath, "a") as file:
            np.savetxt(file, np.array(data).transpose(), fmt="%f", delimiter=",")
        if VERBOSE:
            print(f"Saved buffer in {time()-t0} s ({self.sampling_rate} Hz, buffer size {self.buffer_size})")
