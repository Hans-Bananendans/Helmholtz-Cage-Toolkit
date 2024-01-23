# Helmholtz-Cage-Toolkit
Toolkit for large Helmholtz cage test setups, primarily aimed at testing spacecraft

## What is this?
This repository contains a set of tools for building, validating, and operating a large Helmholtz cage test setup. It is developed as part of thesis work for a MSc in Space Engineering. 

## Why was this developed?
In recent years, hundreds of nanosatellites are launched into space. CubeSats are a popular form factor for these missions, due to their versatility, low technological threshold, and developed market of commercial components. However, whilst the CubeSat standard has existed for over a decade, many CubeSat missions still experience major problems, or end in mission failure. This is particularly so for CubeSat missions by universities and hobbyists/amateurs, which have a relatively high rate of failure.

As part of a literature study, the author of this repository attempted to identify the root causes of these mission failures. Whilst it was difficult to prove many of the suspected root causes definitively, it was revealed that there have been several CubeSat missions in the past that ended in trouble/failure because of insufficient magnetic testing, as there was insufficient time and/or budget for this.

The MSc thesis work of the author therefore investigated not only how to better test these missions, but also how to make these tests _easier_, bearing in mind that for many low-budget CubeSat missions, much of the test hardware is developed in-house also. The aim of the work is therefore to lower the threshold for comprehensive magnetic testing of low-budget CubeSat missions, as this may result in fewer missions ending in failure. The **Helmholtz Cage Toolkit** plays an important role in addressing this.

In essence, this toolkit allows you to take a set of Helmholtz coil pairs, and some general hardware, and connect these together to form a test setup. The toolkit was developed with flexibility as one of its core requirements. As such, the software itself is agnostic to what operating system it is used with, so long as it can run a Python interpreter and interface with the hardware. Some additional drivers and conversion is probably needed to make it work with a particular set of hardware, but since the Helmholtz Cage Toolkit is also designed to be fairly modular, this should pose a relatively approachable challenge.

This 

## Usage
This repository is best cloned into an instantiated `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then clone the repository and install the requirements:
```bash
git clone https://github.com/Hans-Bananendans/Helmholtz-Cage-Toolkit.git
pip install -r ./requirements.txt
```

## Dependencies
This software uses the following dependencies:
 * ~~[PySide6](https://pypi.org/project/PySide6/)~~ (coming soon, for now PyQt5)
 * [PyQtGraph 0.13.3](https://www.pyqtgraph.org/)
 * [Qt-Material](https://qt-material.readthedocs.io/en/latest/)
 * [Numpy](https://numpy.org/)

as well a number of other dependencies, all of which can be found in `requirements.txt`.


## Attributions
Some icons were sourced from the excellent [Feather](https://feathericons.com/) collection.


## License
<a rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png" /></a><br />
The contents of this repository are licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), except where indicated otherwise.

