# Helmholtz-Cage-Toolkit
Toolkit for large Helmholtz cage test setups, primarily aimed at testing spacecraft.


## What is this?
This repository contains a set of tools for building, validating, and operating a large Helmholtz cage test setup. It is developed as part of [MSc thesis work](https://repository.tudelft.nl/record/uuid:06836d7a-800f-44f2-8513-cf1c6be283f1) in Space Engineering.


## Why was this developed?
In recent years, hundreds of nanosatellites are launched into space. CubeSats are a popular form factor for these missions, due to their versatility, low technological threshold, and developed market of commercial components. However, whilst the CubeSat standard has existed for over a decade, many CubeSat missions still experience major problems, or end in mission failure. This is particularly so for CubeSat missions by universities and hobbyists/amateurs, which have a relatively high rate of failure.

As part of a literature study, the author of this repository attempted to identify the root causes of these mission failures. Whilst it was difficult to prove many of the suspected root causes definitively, it was revealed that there have been several CubeSat missions in the past that ended in trouble/failure because of insufficient magnetic testing, as there was insufficient time and/or budget for this.

The MSc thesis work of the author therefore investigated not only how to better test these missions, but also how to make these tests _easier_, bearing in mind that for many low-budget CubeSat missions, much of the test hardware is developed in-house also. The aim of the work is therefore to lower the threshold for comprehensive magnetic testing of low-budget CubeSat missions, as this may result in fewer missions ending in failure. The **Helmholtz Cage Toolkit** plays an important role in addressing this.

In essence, this toolkit allows you to take a set of Helmholtz coil pairs, and some general hardware, and connect these together to form a test setup. The toolkit was developed with flexibility as one of its core requirements. As such, the software itself is agnostic to what operating system it is used with, so long as it can run a Python interpreter and interface with the hardware. Some additional drivers and conversion is probably needed to make it work with a particular set of hardware, but since the Helmholtz Cage Toolkit is also designed to be fairly modular, this should pose a relatively approachable challenge.


## Development status
The contents of this repository are being developed full-time, and are therefore in a state of flux. If you plan on using this repository in the near future, it should be mentioned that its contents may still change rapidly in the weeks to come.


## Usage
This repository is best cloned into an instantiated `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then clone the repository and install it as a package, using `setup.py`:
```bash
git clone https://github.com/Hans-Bananendans/Helmholtz-Cage-Toolkit.git
pip install .
```

## Dependencies
This software uses the following dependencies:
 * [PyQt5 5.15](https://pypi.org/project/PyQt5/) (migration to PySide6 has been suspended for now, due to significant performance degradation.)
 * [Qt-Material](https://qt-material.readthedocs.io/en/latest/)
 * [PyQtGraph 0.13.3](https://www.pyqtgraph.org/)
 * [PyOpenGL 3.1.7](https://pypi.org/project/pyopengl/)
 * [Numpy](https://numpy.org/)
 * [SciPy](https://pypi.org/project/scipy/)
 * [pyIGRF](https://pypi.org/project/pyigrf/)
 * [pyadi-iio](https://pypi.org/project/pyadi-iio/)

as well a number of other dependencies, all of which can be found in `setup.py`.

Note: it may be that your version of pyIGRF cannot load the model parameters. This is a [known bug with the package](https://github.com/zzyztyy/pyIGRF/issues/14), and may be fixed in the future. For the moment, you can fork it and easily patch it yourself.

## Screenshots

![alt text](helmholtz_cage_toolkit/extras/screenshot_command_manual_0.2.png?raw=true)
Command interface for controlling the Helmholtz cage in a server-client setup. Currently "manual mode" is selected, which allows the user to manually set input field vectors, and specify a constant field vector to reject.
___

![alt text](helmholtz_cage_toolkit/extras/screenshot_command_play_0.2.png?raw=true)
Command interface in "play mode", in which pre-defined schedules can be played on the remote device, whilst measurement data is coming in.
___

![alt text](helmholtz_cage_toolkit/extras/screenshot_cyclics_0.2.png?raw=true)
User interface for one of the generators that can be used to generate time-dependent inputs to the Helmholtz cage setup.
___

![alt text](helmholtz_cage_toolkit/extras/screenshot_connectionwindow_0.2.png?raw=true)
Overview interface containing details about the TCP connection between client and server, as well as controls to transfer schedule data to the remote device.
___

![alt text](helmholtz_cage_toolkit/extras/screenshot_orbital_0.2.png?raw=true)
Early look at user interface of another input generators, which propagates a low Earth orbit (LEO) over time and acquires the local magnetic field data in the body frame of a simulated satellite. The local field is simulated using the IGRF.
![alt text](helmholtz_cage_toolkit/extras/screenshot_orbital_cage3d_0.2.png?raw=true)
The local field data can then be converted to the satellite body frame and then to software instructions for the Helmholtz cage system.
___

![alt text](helmholtz_cage_toolkit/extras/file_content.png?raw=true)
File layout of the most important code files.
___

![alt text](helmholtz_cage_toolkit/extras/scc_packets.png?raw=true)
Anatomy of the TCP packets for the SCC codec, included in the ```/scc/``` folder.
___

## Attributions
Some icons were sourced from the excellent [Feather](https://feathericons.com/) collection.


## License
<a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png" /></a><br />
The contents of this repository are licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), except where indicated otherwise.

