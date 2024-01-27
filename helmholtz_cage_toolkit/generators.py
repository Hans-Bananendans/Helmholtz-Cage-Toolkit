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


app = pg.mkQApp("Plotting Example")

win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
win.resize(1000, 600)
win.setWindowTitle('pyqtgraph example: Plotting')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)





# duration = 60           # [s]
# sample_rate = 10        # [Hz]
#
# predelay = 3.0
# postdelay = 1.0
#
# fbase = array(["sine", "sine", "sawtooth"])
#
# amplitude = array([250_000, 250_000, -100_000])
# frequency = array([1/duration, 1/duration, 1/duration-1E-6])
# phase = array([0.5, 0.0, 0.0]) * pi
# offset = array([0.0, 0.0, 100_000])
#
# fbase_noise = array(["gaussian", "gaussian", "gaussian"])
# noise_factor = array([0.0, 0.0, 0.0])

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
    sample_rate = g["sample_rate"]      # [Hz] Samples per second
    predelay = g["predelay"]            # [s] Dead time before set (common)
    postdelay = g["postdelay"]          # [s] Dead time after set (common)
    fbase = [g["fbaseX"],               # Generator base function
             g["fbaseY"],
             g["fbaseZ"]]
    amplitude = [g["amplitudeX"]*1000,  # [nT] Base function amplitude
                 g["amplitudeY"]*1000,
                 g["amplitudeZ"]*1000]
    frequency = [g["frequencyX"],       # [Hz] Base function frequency
                 g["frequencyY"],
                 g["frequencyZ"]]
    phase = [g["phaseX"],               # [rad] Base function phase angle
             g["phaseY"],
             g["phaseZ"]]
    offset = [g["offsetX"]*1000,        # [nT] Vertical offset
              g["offsetY"]*1000,
              g["offsetZ"]*1000]
    fbase_noise = [g["fbase_noiseX"],   # Noise base function
                   g["fbase_noiseY"],
                   g["fbase_noiseZ"]]
    noise_factor = [g["noise_factorX"], # Strength of noise as factor of base function amplitude
                    g["noise_factorY"],
                    g["noise_factorZ"]]


    # Generate time set
    t = linspace(0, int(duration), int(sample_rate * duration))
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

# def generator_cyclics(duration,             # [s] Set length (common)
#                       sample_rate,          # [Hz] Samples per second
#                       predelay,             # [s] Dead time before set (common)
#                       postdelay,            # [s] Dead time after set (common)
#                       fbase,                # Generator base function
#                       amplitude,            # [nT] Base function amplitude
#                       frequency,            # [Hz] Base function frequency
#                       phase,                # [rad] Base function phase angle
#                       offset,               # [nT] Vertical offset
#                       fbase_noise,          # Noise base function
#                       noise_factor,         # Strength of noise as factor of base function amplitude
#                       generate_alt=True     # Whether to generate alt set (for better plots)
#                       ):
#
#     t = linspace(0, duration, sample_rate * duration)
#     B = []
#
#     for i in range(3):
#         B.append(generator_cyclics_single(
#             t, fbase[i], amplitude[i], frequency[i], phase[i], offset[i],
#             fbase_noise=fbase_noise[i], noise_factor=noise_factor[i]))
#
#     # Generate alt sequences as input for more realistic plots
#     if generate_alt:
#         t_alt = repeat(t, 2)[1:]
#         B_alt = []
#         for i in range(3):
#             B_alt.append(repeat(B[i], 2)[:-1])
#
#     # Apply predelay and post-delay
#     if predelay > 0.0:
#         t += predelay                       # Move whole sequence forward
#         t = insert(t, [0], [0., t[0]])   # Insert two extra point at the start
#         for i in range(3):
#             B[i] = insert(B[i], [0], [0., 0.])   # Put these on the t-axis
#
#     if postdelay > 0.0:
#         t = append(t, [t[-1], t[-1] + postdelay])
#         for i in range(3):
#             B[i] = append(B[i], [0., 0.])
#
#
#     # Repeat the process for alt sequences, if needed
#     if generate_alt:
#         if predelay > 0.0:
#             t_alt += predelay
#             t_alt = insert(t_alt, [0], [0., t_alt[0]])
#             for i in range(3):
#                 B_alt[i] = insert(B_alt[i], [0], [0., 0.])
#
#         if show_actual:
#             t_alt = append(t_alt, [t_alt[-1], t_alt[-1] + postdelay])
#             for i in range(3):
#                 B_alt[i] = append(B_alt[i], [0., 0.])
#
#     if not generate_alt:
#         t_alt = None
#         B_alt = None
#
#     return t, B, t_alt, B_alt

# y = generator(t, amplitude[0], frequency[0], phase[0], fbase="square")
#
#
# if show_actual:
#     t_alt = repeat(t, 2)[1:]
#     y_alt = repeat(y, 2)[:-1]
#
#
# if predelay > 0.0:
#     t += predelay
#     t = insert(t, [0], [0., t[0]])
#     y = insert(y, [0], [0., 0.])
#
#     if show_actual:
#         t_alt += predelay
#         t_alt = insert(t_alt, [0], [0., t_alt[0]])
#         y_alt = insert(y_alt, [0], [0., 0.])
#
# if postdelay > 0.0:
#     t = append(t, [t[-1], t[-1]+postdelay])
#     y = append(y, [0., 0.])
#     if show_actual:
#         t_alt = append(t_alt, [t_alt[-1], t_alt[-1]+postdelay])
#         y_alt = append(y_alt, [0., 0.])


def detect_predelay(x):
    if 0.99*(x[1]-x[0]) > x[3]-x[2] and abs(x[2]-x[1]) < 1E-6:
        return x[1]-x[0]
    else:
        return 0.0

def detect_postdelay(x):
    if 0.99*(x[-1]-x[-2]) > x[-4]-x[-3] and abs(x[-2]-x[-3]) < 1E-6:
        return x[-1]-x[-2]
    else:
        return 0.0

def generate_2D_plots(t, B, show_actual=False, show_points=True):

    colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]

    # Detect predelay and postdelay, for more accurate staggered plots
    # Detection algorithms are not guaranteed to catch predelays
    predelay = False
    postdelay = False
    push = [0, -1]
    if detect_predelay(t) > 0.0:
        predelay = True
        push[0] = 2
    if detect_postdelay(t) > 0.0:
        postdelay = True
        push[1] = -2

    # Generate dataset by
    t_stag = repeat(t[push[0]:push[1]], 2)[1:]
    B_stag = array((repeat(B[0, push[0]:push[1]], 2)[:-1],
                    repeat(B[1, push[0]:push[1]], 2)[:-1],
                    repeat(B[2, push[0]:push[1]], 2)[:-1])
                   )

    plot_main = win.addPlot(title="Main plot")

    for i in range(3):
        if show_actual:
            # Staggered
            plot_main.plot(t_stag, B_stag[i], pen=colours[i])
            # Line patches for predelay
            if predelay:
                plot_main.plot([t[0],    t[1],    t_stag[0]],
                               [B[i, 0], B[i, 1], B_stag[i, 0]],
                               pen=colours[i])
            # Line patches for postdelay
            if postdelay:
                plot_main.plot([t_stag[-1],    t[-2],    t[-1]],
                               [B_stag[i, -1], B[i, -2], B[i, -1]],
                               pen=colours[i])
        else:
            plot_main.plot(t, B[i], pen=colours[i])

        if show_points:
            plot_main.plot(t, B[i],
                           pen=(0, 0, 0, 0),
                           symbolBrush=(0, 0, 0, 0),
                           symbolPen=colours[i],
                           symbol="o",
                           symbolSize=6)
    # plot_main.plot(t_interp, y_interp,
    #                pen=(255, 0, 0, 0),
    #                symbolBrush=(0, 0, 0, 0),
    #                symbolPen=(255, 120, 120, 200),
    #                symbol="o",
    #                symbolSize=6)

    plot_main.showGrid(x=True, y=True)

    return plot_main

def generate_schedule_segments(t, B):
    n = len(t)
    schedule = [[0, 0, 0., 0., 0., 0.], ]*n
    for i in range(n):
        schedule[i] = [i, n, round(t[i], 6),
                       round(B[0][i], 3), round(B[1][i], 3), round(B[2][i], 3)]

    return schedule
    # return list(column_stack(array((
    #     linspace(0, n-1, n, dtype=int),
    #     ones(n, dtype=int)*n,
    #     t,
    #     B[0],
    #     B[1],
    #     B[2]))))


# Interpolate

# print("Detected predelay:", detect_predelay(x))
# print("Detected postdelay:", detect_postdelay(x))

# factor = 10
# t_interp = linspace(t[0], t[-1], len(t)*factor)
# y_interp = interp(t_interp, t, y)
#
#
# plot_main = win.addPlot(title="Main plot")
# if show_actual:
#     plot_main.plot(t_alt, y_alt, pen=(255, 0, 0, 255))
# else:
#     plot_main.plot(t, y, pen=(255, 0, 0, 255))
#
#
# plot_main.plot(t, y,
#                pen=(255, 0, 0, 0),
#                symbolBrush=(0, 0, 0, 0),
#                symbolPen=(255, 0, 0, 255),
#                symbol="o",
#                symbolSize=6)
# plot_main.plot(t_interp, y_interp,
#                pen=(255, 0, 0, 0),
#                symbolBrush=(0, 0, 0, 0),
#                symbolPen=(255, 120, 120, 200),
#                symbol="o",
#                symbolSize=6)
# plot_main.showGrid(x=True, y=True)


# x2 = linspace(-100, 100, 1000)
# data2 = sin(x2) / x2
# p1 = win.addPlot(title="Region Selection")
# p1.plot(data2, pen=(255, 255, 255, 200))
# lr = pg.LinearRegionItem([400, 700])
# lr.setZValue(-10)
# p1.addItem(lr)
#
# win.nextRow()
#
# p2 = win.addPlot(title="Zoom on selected region")
# p2.plot(data2)
# def updatePlot():
#     p2.setXRange(*lr.getRegion(), padding=0)
# def updateRegion():
#     lr.setRegion(p2.getViewBox().viewRange()[0])
# lr.sigRegionChanged.connect(updatePlot)
# p2.sigXRangeChanged.connect(updateRegion)
# updatePlot()


def initialize_file(filename, header, overwrite=False):
    try:
        with open(filename, 'x') as output_file:
            pass
    except FileExistsError:
        if overwrite is False:
            print("File already exists! Creation cancelled")
            return -1
        else:
            pass
    with open(filename, 'w') as output_file:
        output_file.write(header)
    output_file.close()
    return 0


cyclics_generator_params = {
    "duration": 10,
    "sample_rate": 1,
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



# def generate_header_cyclics(
#     filename, duration, sample_rate, predelay, postdelay,
#     fbase, amplitude, frequency, phase, offset,
#     fbase_noise, noise_factor):
#
#     paramlist = ["duration", "sample_rate", "predelay", "postdelay",
#                  "fbaseX",          "fbaseY",           "fbaseZ",
#                  "amplitudeX",      "amplitudeY",       "amplitudeZ",
#                  "frequencyX",      "frequencyY",       "frequencyZ",
#                  "phaseX",          "phaseY",           "phaseZ",
#                  "offsetX",         "offsetY",          "offsetZ",
#                  "fbase_noiseX",    "fbase_noiseY",     "fbase_noiseZ",
#                  "noise_factorX",   "noise_factorY",    "noise_factorZ",
#                  ]
#     vallist = [duration, sample_rate, predelay, postdelay,
#                fbase[0],        fbase[1],           fbase[2],
#                amplitude[0],    amplitude[1],       amplitude[2],
#                frequency[0],    frequency[1],       frequency[2],
#                phase[0],        phase[1],           phase[2],
#                offset[0],       offset[1],          offset[2],
#                fbase_noise[0],  fbase_noise[1],     fbase_noise[2],
#                noise_factor[0], noise_factor[1],    noise_factor[2]]
#
#     paramstring = ""
#     valstring = ""
#     [paramstring+item for item in paramlist]
#
#
#
#     return "!BSCH\n{}\n{}\n{}\n\n\n\n\n\n{}\n".format(
#         filename.strip("." + filename.split(".")[-1]),
#         "generator=cyclics",
#         ",".join(paramlist),
#         ",".join(str(item) for item in vallist),
#         "#"*32
#     )

def generate_header(filename, generator, generation_parameters):

    return "!BSCH\n{}\n{}\n{}\n\n\n\n\n\n{}\n".format(
        filename.strip("." + filename.split(".")[-1]),
        "generator={}".format(generator),
        str(generation_parameters),
        "#"*32
    )

def write_bsch_file(filename, schedule, overwrite=False):
    with open(filename, 'a') as output_file:
        for segment in schedule:
            print(type(segment), len(segment), segment)
            output_file.write(",".join(str(val) for val in segment))
            output_file.write("\n")
    output_file.close()
    return 0


def read_bsch_file(filename):
    # TODO: Should headerless files be supported? Seems like a lot of hassle
    # for little gain.
    #
    header_length = 10
    with open(filename, 'r') as bsch_file:
        flag = (bsch_file.readline()).strip("\n")
        schedule_name = (bsch_file.readline()).strip("\n")
        generator = bsch_file.readline().strip("\n").split("=")[-1]
        generation_parameters = literal_eval(bsch_file.readline())
        for i in range(5):
            bsch_file.readline()
        end_of_header = (bsch_file.readline()).strip("\n")

        # for i, item in enumerate((flag, schedule_name, generator, generation_parameters, end_of_header)):
        #     print(i, ":", item, type(item))

        # Checks
        if flag != "!BSCH":
            raise AssertionError(f"While loading '{filename}', header flag !BSCH not found. Are you sure it is a valid .bsch file?")

        if end_of_header != "#"*32:
            raise AssertionError(f"While loading '{filename}', could not find end of header. Are you sure it is a valid .bsch file?")

        recognised_generators = ("cyclics", "orbital")
        if generator not in recognised_generators:
            raise AssertionError(f"While loading '{filename}', encountered unknown generator name {generator}. Currently supported generators: {recognised_generators}")

        raw_schedule = bsch_file.readlines()
        n = len(raw_schedule)
        # print(raw_schedule, type(raw_schedule), len(raw_schedule))

        t = empty(n)
        B = empty((n, 3))
        for i, line in enumerate(raw_schedule):
            stringvals = line.strip("\n").split(",")
            t[i] = stringvals[2]
            B[i, :] = array((stringvals[3], stringvals[4], stringvals[5]))
        B = column_stack(B)

    bsch_file.close()

    return t, B, schedule_name, generator, generation_parameters

# ============================================================================

my_params = {
    "duration": 600,
    "sample_rate": 0.1,
    "predelay": 0.0,
    "postdelay": 0.0,
    "fbaseX": "sine",
    "fbaseY": "sine",
    "fbaseZ": "linear",
    "amplitudeX": 100_000,
    "amplitudeY": 100_000,
    "amplitudeZ": 200_000,
    "frequencyX": 1/10,
    "frequencyY": 1/10,
    "frequencyZ": 0,
    "phaseX": 0.5*pi,
    "phaseY": 0.0,
    "phaseZ": 0.0,
    "offsetX": 0.0,
    "offsetY": 0.0,
    "offsetZ": -100_000,
    "fbase_noiseX": "gaussian",
    "fbase_noiseY": "gaussian",
    "fbase_noiseZ": "gaussian",
    "noise_factorX": 0.0,
    "noise_factorY": 0.0,
    "noise_factorZ": 0.0,
}



show_actual = True
t0 = time()
t, B = generator_cyclics(my_params)


print(f"Generation time: {round((time()-t0)*1E6, 3)} us")

schedule = generate_schedule_segments(t, B)

filename = "myschedule2.bsch"
generator = "cyclics"
headerstring = generate_header(filename, generator, my_params)

initialize_file(filename, headerstring, overwrite=True)
write_bsch_file(filename, schedule)


plot = generate_2D_plots(t, B, show_actual=show_actual, show_points=False)

t_test, B_test, schedule_name_test, generator_test, generation_parameters_test = read_bsch_file(filename)

#
# print("t:", t_test == t.round(6))
# print("B:", B_test[0] == B[0].round(3))
# print("schedule_name:", schedule_name_test == filename[:-5])
# print("generator:", generator_test == "cyclics")
# print("generation_parameters:", generation_parameters_test == my_params)


if __name__ == '__main__':
    pg.exec()