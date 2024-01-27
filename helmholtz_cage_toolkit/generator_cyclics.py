from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
)

from time import time, sleep
from numpy import (
    pi, array, sin,
    zeros, ones, empty, linspace,
    repeat, insert, append, column_stack,
    interp,
)
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from scipy.signal import sawtooth, square
from numpy.random import normal, uniform
from ast import literal_eval


def generator_cyclics_single(x,
                             fbase: str,
                             amplitude,
                             frequency,
                             phase,
                             offset,
                             fbase_noise: str = "gaussian",
                             noise_factor: float = 0.0
                             ):
    # Noise generation
    if noise_factor != 0.0:
        if fbase_noise == "gaussian":
            fnoise = normal(loc=0.0, scale=1.0, size=len(x)) * noise_factor * amplitude
        elif fbase_noise == "uniform":
            fnoise = uniform(low=-1.0, high=1.0, size=len(x)) * noise_factor * amplitude
        else:
            raise ValueError("Tried to pass invalid fbase_noise '{fbase_noise}'!")
    else:
        fnoise = zeros(len(x))

    # Function generation (noise is applied to the output (post, not pre))
    if fbase == "constant":
        return ones(len(x))*offset + fnoise
    elif fbase == "linear":
        return amplitude/(x[-1]-x[0]) * x + offset + fnoise
    elif fbase == "sine":
        return amplitude * sin(2 * pi * frequency * x + phase) + offset + fnoise
    elif fbase == "sawtooth":
        return amplitude * sawtooth(2 * pi * frequency * x + phase, width=1) + offset + fnoise
    elif fbase == "triangle":
        return amplitude * sawtooth(2 * pi * frequency * x + phase, width=0.5) + offset + fnoise
    elif fbase == "square":
        return amplitude * square(2 * pi * frequency * x + phase) + offset + fnoise
    else:
        raise ValueError("Tried to pass invalid fbase '{fbase}'!")


def generator_cyclics(generation_parameters):

    # Assemble parameters
    g = generation_parameters  # Shorthand

    duration = g["duration"]            # [s] Set length (common)
    resolution = g["resolution"]        # [Hz] Samples per second
    predelay = g["predelay"]            # [s] Dead time before set (common)
    postdelay = g["postdelay"]          # [s] Dead time after set (common)
    fbase = [g["fbaseX"],               # Generator base function
             g["fbaseY"],
             g["fbaseZ"]]
    amplitude = [g["amplitudeX"]*1000,  # [uT->nT] Base function amplitude
                 g["amplitudeY"]*1000,
                 g["amplitudeZ"]*1000]
    frequency = [g["frequencyX"],       # [Hz] Base function frequency
                 g["frequencyY"],
                 g["frequencyZ"]]
    phase = [g["phaseX"]*-pi,           # [pi rad] Base function phase angle
             g["phaseY"]*-pi,
             g["phaseZ"]*-pi]
    offset = [g["offsetX"]*1000,        # [uT->nT] Vertical offset
              g["offsetY"]*1000,
              g["offsetZ"]*1000]
    fbase_noise = [g["fbase_noiseX"],   # Noise base function
                   g["fbase_noiseY"],
                   g["fbase_noiseZ"]]
    noise_factor = [g["noise_factorX"], # Strength of noise as factor of base function amplitude
                    g["noise_factorY"],
                    g["noise_factorZ"]]


    # Generate time set
    t = linspace(0, int(duration), int(resolution * duration))
    B = []

    for i in range(3):
        B.append(generator_cyclics_single(
            t, fbase[i], amplitude[i], frequency[i], phase[i], offset[i],
            fbase_noise=fbase_noise[i], noise_factor=noise_factor[i]))

    # Apply predelay and post-delay
    if predelay > 0.0:
        t += predelay                       # Move whole sequence forward
        t = insert(t, [0], [0., t[0]])   # Insert two extra point at the start
        for i in range(3):
            B[i] = insert(B[i], [0], [0., 0.])   # Put these on the t-axis

    if postdelay > 0.0:
        t = append(t, [t[-1], t[-1] + postdelay])
        for i in range(3):
            B[i] = append(B[i], [0., 0.])

    return t, array(B)


# cyclics_generation_parameters = {
#     "duration": 10,
#     "resolution": 1,
#     "predelay": 0.0,
#     "postdelay": 0.0,
#     "fbaseX": "constant",
#     "fbaseY": "constant",
#     "fbaseZ": "constant",
#     "amplitudeX": 1.0,
#     "amplitudeY": 1.0,
#     "amplitudeZ": 1.0,
#     "frequencyX": 0.1,
#     "frequencyY": 0.1,
#     "frequencyZ": 0.1,
#     "phaseX": 0.0,
#     "phaseY": 0.0,
#     "phaseZ": 0.0,
#     "offsetX": 0.0,
#     "offsetY": 0.0,
#     "offsetZ": 0.0,
#     "fbase_noiseX": "gaussian",
#     "fbase_noiseY": "gaussian",
#     "fbase_noiseZ": "gaussian",
#     "noise_factorX": 0.0,
#     "noise_factorY": 0.0,
#     "noise_factorZ": 0.0,
# }


cyclics_generation_parameters = {
    "duration": 10,
    "resolution": 10,
    "predelay": 0.0,
    "postdelay": 0.0,
    "fbaseX": "constant",
    "fbaseY": "constant",
    "fbaseZ": "constant",
    "amplitudeX": 1.0,
    "amplitudeY": 1.0,
    "amplitudeZ": 1.0,
    "frequencyX": 0.1,
    "frequencyY": 0.1,
    "frequencyZ": 0.1,
    "phaseX": 0.0,
    "phaseY": 0.0,
    "phaseZ": 0.0,
    "offsetX": 0.0,
    "offsetY": 0.0,
    "offsetZ": 0.0,
    "fbase_noiseX": "gaussian",
    "fbase_noiseY": "gaussian",
    "fbase_noiseZ": "gaussian",
    "noise_factorX": 0.0,
    "noise_factorY": 0.0,
    "noise_factorZ": 0.0,
}
