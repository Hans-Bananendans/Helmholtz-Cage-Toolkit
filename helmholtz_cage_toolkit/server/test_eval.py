""" test_eval

A small GUI tool that visualizes the performance of the Helmholtz cage
in tracking a magnetic schedule. It takes an output data file as input.
The column headers of this file should be:
t,Icx,Icy,Icz,Bmx,Bmy,Bmz,Bcx,Bcy,Bcz
"""

# Imports
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg
from copy import deepcopy
from numpy.lib.recfunctions import append_fields, merge_arrays
from scipy.signal import savgol_filter
from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.config import config
from helmholtz_cage_toolkit.file_handling import load_filedialog

from qt_material import apply_stylesheet

from helmholtz_cage_toolkit.pg3d import (
    PGFrame3D,
    plotframe2,
)

from pyqtgraph.opengl import (
    GLGridItem,
    GLLinePlotItem,
    GLMeshItem,
    GLScatterPlotItem,
    GLViewWidget,
    MeshData,
)

class TestEvalWindowMain(QMainWindow):
    def __init__(self, config_file) -> None:
        super().__init__()

        # Load config
        self.config = config_file

        self.setWindowIcon(QIcon("../assets/icons/icon2c.png"))
        self.resize(1600, 900)      # Default w x h dimensions

        # Data objects
        self.data = None
        self.data2 = None
        self.data_filename = None
        self.Bc_dt = None
        self.Bc_ddt = None
        self.Bm_dt = None
        self.Bm_ddt = None
        self.Ec_xyz = np.empty([1,3])    # Command error (absolute)
        self.Ec = None
        self.Emax_xyz = None
        self.Emax = None
        self.Erms_xyz = None
        self.Erms = None
        self.Eangle = None
        self.Eanglemax = 1
        self.Eanglerms = 0

        self.Eangle2 = None
        self.Eanglemax2 = None
        self.Eanglerms2 = None

        self.skip_start = 0.6           # [s] Set start time to skip (to discard start-up transients)
        self.do_delay_correction = True
        self.manifold_colour_angle = True   # Use angle error to colour 3D manifold, else use field error
        self.command_delay = 0.100      # [s] Set desired command delay
        self.csd = 0                    # [S] Set 0 samples as default command delay

        # Tab widgets and layouts
        self.envelopetab = EnvelopeTab(self)
        self.errortab1 = ErrorTab1(self)
        self.errortab2 = ErrorTab2(self)
        self.derivtab1 = DerivTab1(self)
        # self.derivtab2 = DerivTab1(self)
        self.currenttab1 = CurrentTab1(self)
        self.cage3dtab = Cage3DTab(self, self.config, self.data)

        self.plottabs = QTabWidget()
        self.plottabs.addTab(self.envelopetab, "Envelope plot")
        self.plottabs.addTab(self.errortab1, "Error plot 1")
        self.plottabs.addTab(self.errortab2, "Error plot 2")
        self.plottabs.addTab(self.derivtab1, "Deriv plot")
        self.plottabs.addTab(self.currenttab1, "Current plot")

        # self.plottabs.addTab(self.derivtab2, "Deriv plot 2")
        self.plottabs.addTab(self.cage3dtab, "Cage plot")
        self.setCentralWidget(self.plottabs)

        # Make a menu bar
        menubar = self.create_menubar()
        self.setMenuBar(menubar)

    def create_menubar(self):
        menubar = QMenuBar()
        menu_file = menubar.addMenu("&File")
        menu_show = menubar.addMenu("&Show")

        act_load = QAction(
            QIcon("../assets/icons/feather/folder.svg"),
            "&Load test data...", self)
        act_load.setStatusTip("Load data from a previous test")
        act_load.triggered.connect(self.load_file)
        act_load.setCheckable(False)
        act_load.setShortcut(QKeySequence("Ctrl+o"))
        menu_file.addAction(act_load)

        act_load2 = QAction(
            QIcon("../assets/icons/feather/folder.svg"),
            "&Load filtered test data...", self)
        act_load2.setStatusTip("Load filtered data after post-processing")
        act_load2.triggered.connect(self.load_file2)
        act_load2.setCheckable(False)
        menu_file.addAction(act_load2)

        act_clear = QAction(
            QIcon("../assets/icons/feather/trash.svg"),
            "&Clear internal data...", self)
        act_clear.setStatusTip("Clear all previously loaded test data")
        act_clear.triggered.connect(self.clearData)
        act_clear.setCheckable(False)
        act_clear.setShortcut(QKeySequence("Ctrl+D"))
        menu_file.addAction(act_clear)


        menu_show.addSection("Cage plot data") # Doesn't display text in qt_material
        actgroup_cageplot_data = QActionGroup(menu_show)

        act_cageplot_nonedata = QAction("Command only", self)
        act_cageplot_nonedata.setActionGroup(actgroup_cageplot_data)
        act_cageplot_nonedata.setStatusTip("Show only Bc data in the cage plot")
        act_cageplot_nonedata.triggered.connect(
            lambda: self.set_cageplot_data(0)
        )
        act_cageplot_nonedata.setCheckable(True)
        menu_show.addAction(act_cageplot_nonedata)

        act_cageplot_data1 = QAction("Raw Bm data", self)
        act_cageplot_data1.setActionGroup(actgroup_cageplot_data)
        act_cageplot_data1.setStatusTip("Show Bc and raw Bm data in the cage plot")
        act_cageplot_data1.triggered.connect(
            lambda: self.set_cageplot_data(1)
        )
        act_cageplot_data1.setCheckable(True)
        menu_show.addAction(act_cageplot_data1)

        act_cageplot_data2 = QAction("Improved Bm data", self)
        act_cageplot_data2.setActionGroup(actgroup_cageplot_data)
        act_cageplot_data2.setStatusTip("Show Bc and improved Bm data in the cage plot")
        act_cageplot_data2.triggered.connect(
            lambda: self.set_cageplot_data(2)
        )
        act_cageplot_data2.setCheckable(True)
        menu_show.addAction(act_cageplot_data2)

        act_cageplot_data1.setChecked(True)

        return menubar


    def load_file(self):
        # Load dialog box
        filename = QFileDialog.getOpenFileName(
            parent=None,
            caption="Select a test data file",
            directory=os.getcwd(),
            filter="Test data file (*.dat);; All files (*.*)",
            initialFilter="Test data file (*.dat)"
        )[0]
        if filename == "":
            print(f"No file selected!")
            return

        self.data_filename = filename

        self.data = np.empty(0)    # Delete old data first
        try:
            print(f"Loading {filename}...")
            self.data = np.genfromtxt(filename, delimiter=',', names=True)

            # Remove trailing zero entries
            if self.data["t"][-1] == 0:
                # len0 = len(self.data["t"])
                i = 1
                while self.data["t"][i] != 0:
                    i += 1
                n_zerolines = len(self.data["t"]) - i
                print(f"Truncating {n_zerolines} zero lines from the end")
                self.data = np.genfromtxt(filename, delimiter=",", names=True, skip_footer=n_zerolines)

            # Measure sample time in dataset
            sample_time = np.mean(self.data["t"][1:8] - self.data["t"][0:7])
            print(f"Sample rate: {round(1/sample_time, 2)} S/s")
            assert (sample_time > 0.0)

            if self.do_delay_correction:
                # Implement command delay by measuring the sample rate and shifting by ~150 ms equivalent
                csd_float = np.round(self.command_delay / sample_time)
                self.csd = int(csd_float)
                print(f"Found sample rate of {np.round(1/sample_time, 2)} S/s")
                print(f"Correcting propagation delay by shifting Bc data by {csd_float} -> {self.csd} samples")
                # Shift Bc data
                self.data["Bcx"][self.csd:] = self.data["Bcx"][:-self.csd]
                self.data["Bcy"][self.csd:] = self.data["Bcy"][:-self.csd]
                self.data["Bcz"][self.csd:] = self.data["Bcz"][:-self.csd]
                # self.data["Icx"][self.csd:] = self.data["Icx"][:-self.csd]
                # self.data["Icy"][self.csd:] = self.data["Icy"][:-self.csd]
                # self.data["Icz"][self.csd:] = self.data["Icz"][:-self.csd]
                try:    # TODO this is here to have temporary compatibility with old datasets
                    self.data["Imx"][self.csd:] = self.data["Imx"][:-self.csd]
                    self.data["Imy"][self.csd:] = self.data["Imy"][:-self.csd]
                    self.data["Imz"][self.csd:] = self.data["Imz"][:-self.csd]
                except:
                    pass

                self.data = self.data[:-self.csd]
            else:
                print("Skipping propagation delay correction...")

            if self.skip_start > 0:
                samples_to_skip = int(np.round(self.skip_start / sample_time))
                print(f"Discarding first {samples_to_skip} samples to filter start-up transients")
                self.data = self.data[samples_to_skip:]

            print(f"steps = {len(self.data['t'])}")
            print(f"t length = {np.round(self.data['t'][-1], 1)} s")
            print(f"Bcx steps = {len(self.data['Bcx'])}   (last: {self.data['Bcx'][-1]} uT)")
            print(f"Bcy steps = {len(self.data['Bcy'])}   (last: {self.data['Bcy'][-1]} uT)")
            print(f"Bcz steps = {len(self.data['Bcz'])}   (last: {self.data['Bcz'][-1]} uT)")
            print(f"Bmx steps = {len(self.data['Bmx'])}   (last: {self.data['Bmx'][-1]} uT)")
            print(f"Bmy steps = {len(self.data['Bmy'])}   (last: {self.data['Bmy'][-1]} uT)")
            print(f"Bmz steps = {len(self.data['Bmz'])}   (last: {self.data['Bmz'][-1]} uT)\n")
        except:
            print(f"Error during loading of file '{filename}'!\n")

        self.setWindowTitle(filename)

        self.doDataAnalysis()

        self.envelopetab.envelope_plot.generate_plot(self.data)

        self.errortab1.error_plot_abs.generate_plot(self.data, self.Ec_xyz, self.Ec, filter_val=24)
        self.errortab1.envelope_plot.generate_plot(self.data)

        self.errortab2.error_plot_ang.generate_plot(self.data, self.Eangle, self.Eanglerms)
        self.errortab2.envelope_plot.generate_plot(self.data)

        self.derivtab1.deriv_plot.generate_plot(self.data, self.Ec_xyz, self.Ec, filter_val=24)

        self.currenttab1.current_plot.generate_plot(self.data, self.Ec_xyz, self.Ec, filter_val=24)


        self.cage3dtab.clear()
        self.cage3dtab.draw_statics()
        self.cage3dtab.draw_simdata()


    def set_cageplot_data(self, data_index: int):
        if data_index == 1:
            self.cage3dtab.clear()
            self.cage3dtab.draw_statics()
            self.cage3dtab.draw_simdata(data_index = 1)
        elif data_index == 2:
            self.cage3dtab.clear()
            self.cage3dtab.draw_statics()
            self.cage3dtab.draw_simdata(data_index = 2)
        else:
            self.cage3dtab.clear()
            self.cage3dtab.draw_statics()
            self.cage3dtab.draw_simdata(data_index = 0)


    def load_file2(self):
        # Load dialog box
        filename = QFileDialog.getOpenFileName(
            parent=None,
            caption="Select a filtered test data file",
            directory=os.getcwd(),
            filter="Test data file (*.dat);; All files (*.*)",
            initialFilter="Test data file (*.dat)"
        )[0]
        if filename == "":
            print(f"No file selected!")
            return

        # self.data = np.empty(0)    # Delete old data first
        try:
            print(f"Loading {filename}...")
            data2 = np.genfromtxt(filename, delimiter=',', names=True)

            # Remove trailing zero entries
            if data2["t"][-1] == 0:
                # len0 = len(self.data["t"])
                i = 1
                while data2["t"][i] != 0:
                    i += 1
                n_zerolines = len(data2["t"]) - i
                print(f"Truncating {n_zerolines} zero lines from the end")
                data2 = np.genfromtxt(filename, delimiter=",", names=True, skip_footer=n_zerolines)

            # Measure sample time in dataset
            sample_time = np.mean(data2["t"][1:8] - data2["t"][0:7])
            print(f"Sample rate: {round(1/sample_time, 2)} S/s")
            assert (sample_time > 0.0)

            # if self.do_delay_correction:
            #     # Implement command delay by measuring the sample rate and shifting by ~150 ms equivalent
            #     csd_float = np.round(self.command_delay / sample_time)
            #     self.csd = int(csd_float)
            #     print(f"Found sample rate of {np.round(1/sample_time, 2)} S/s")
            #     print(f"Correcting propagation delay by shifting Bc data by {csd_float} -> {self.csd} samples")
            #     # Shift Bc data
            #     data2["Bcx"][self.csd:] = data2["Bcx"][:-self.csd]
            #     data2["Bcy"][self.csd:] = data2["Bcy"][:-self.csd]
            #     data2["Bcz"][self.csd:] = data2["Bcz"][:-self.csd]
            #     # self.data["Icx"][self.csd:] = self.data["Icx"][:-self.csd]
            #     # self.data["Icy"][self.csd:] = self.data["Icy"][:-self.csd]
            #     # self.data["Icz"][self.csd:] = self.data["Icz"][:-self.csd]
            #     data2 = data2[:-self.csd]
            # else:
            #     print("Skipping propagation delay correction...")

            # if self.skip_start > 0:
            #     samples_to_skip = int(np.round(self.skip_start / sample_time))
            #     print(f"Discarding first {samples_to_skip} samples to filter start-up transients")
            #     data2 = data2[samples_to_skip:]

            # print(f"steps = {len(self.data['t'])}")
            # print(f"t length = {np.round(self.data['t'][-1], 1)} s")
            # print(f"Bcx steps = {len(self.data['Bcx'])}   (last: {self.data['Bcx'][-1]} uT)")
            # print(f"Bcy steps = {len(self.data['Bcy'])}   (last: {self.data['Bcy'][-1]} uT)")
            # print(f"Bcz steps = {len(self.data['Bcz'])}   (last: {self.data['Bcz'][-1]} uT)")
            # print(f"Bmx steps = {len(self.data['Bmx'])}   (last: {self.data['Bmx'][-1]} uT)")
            # print(f"Bmy steps = {len(self.data['Bmy'])}   (last: {self.data['Bmy'][-1]} uT)")
            # print(f"Bmz steps = {len(self.data['Bmz'])}   (last: {self.data['Bmz'][-1]} uT)\n")
        except:
            print(f"Error during loading of file '{filename}'!\n")

        Bc2 = np.array([data2["Bcx"], data2["Bcy"], data2["Bcz"]])
        Bm2 = np.array([data2["Bmx"], data2["Bmy"], data2["Bmz"]])
        self.doDataAnalysis2(Bc2, Bm2)

        self.errortab2.error_plot_ang.generate_plot2(self.data, self.Eangle, self.Eanglerms, self.Eangle2, self.Eanglerms2)
        #
        # self.cage3dtab.clear()
        # self.cage3dtab.draw_statics()
        # self.cage3dtab.draw_simdata()

        self.data2 = data2

    def clearData(self):
        self.envelopetab.envelope_plot.plot_obj.clearPlots()

        self.errortab1.error_plot_abs.plot_obj.clearPlots()
        self.errortab1.envelope_plot.plot_obj.clearPlots()

        # self.errortab2.error_plot_abs.plot_obj.clearPlots()
        self.errortab2.error_plot_ang.plot_obj.clearPlots()
        self.errortab2.envelope_plot.plot_obj.clearPlots()

        self.derivtab1.deriv_plot.plot_obj_t.clearPlots()
        self.derivtab1.deriv_plot.plot_obj_dt.clearPlots()
        self.derivtab1.deriv_plot.plot_obj_e.clearPlots()

        self.currenttab1.current_plot.plot_obj_t.clearPlots()
        self.currenttab1.current_plot.plot_obj_i.clearPlots()
        self.currenttab1.current_plot.plot_obj_e.clearPlots()

        self.cage3dtab.clear()
        self.cage3dtab.draw_statics()

        self.data = None

    def doDataAnalysis(self):
        sample_time = np.mean(self.data["t"][1:8] - self.data["t"][0:7])

        # self.Bc_dt = np.array(
        derivs = np.zeros(len(self.data["t"]), dtype=[
            ("Bcx_dt", "<f8"),
            ("Bcy_dt", "<f8"),
            ("Bcz_dt", "<f8"),
            ("Bcx_ddt", "<f8"),
            ("Bcy_ddt", "<f8"),
            ("Bcz_ddt", "<f8"),
            ("Bmx_dt", "<f8"),
            ("Bmy_dt", "<f8"),
            ("Bmz_dt", "<f8"),
            ("Bmx_ddt", "<f8"),
            ("Bmy_ddt", "<f8"),
            ("Bmz_ddt", "<f8"),
        ])
        for i in range(1, len(self.data["t"])):
            dt = self.data["t"][i]-self.data["t"][i-1]
            derivs["Bcx_dt"][i] = (self.data["Bcx"][i] - self.data["Bcx"][i-1]) / dt
            derivs["Bcy_dt"][i] = (self.data["Bcy"][i] - self.data["Bcy"][i-1]) / dt
            derivs["Bcz_dt"][i] = (self.data["Bcz"][i] - self.data["Bcz"][i-1]) / dt
            derivs["Bmx_dt"][i] = (self.data["Bmx"][i] - self.data["Bmx"][i-1]) / dt
            derivs["Bmy_dt"][i] = (self.data["Bmy"][i] - self.data["Bmy"][i-1]) / dt
            derivs["Bmz_dt"][i] = (self.data["Bmz"][i] - self.data["Bmz"][i-1]) / dt
        for i in range(2, len(self.data["t"])):
            dt = self.data["t"][i]-self.data["t"][i-1]
            derivs["Bcx_ddt"][i] = (derivs["Bcx_dt"][i] - derivs["Bcx_dt"][i-1]) / dt
            derivs["Bcy_ddt"][i] = (derivs["Bcy_dt"][i] - derivs["Bcy_dt"][i-1]) / dt
            derivs["Bcz_ddt"][i] = (derivs["Bcz_dt"][i] - derivs["Bcz_dt"][i-1]) / dt
            derivs["Bmx_ddt"][i] = (derivs["Bmx_dt"][i] - derivs["Bmx_dt"][i-1]) / dt
            derivs["Bmy_ddt"][i] = (derivs["Bmy_dt"][i] - derivs["Bmy_dt"][i-1]) / dt
            derivs["Bmz_ddt"][i] = (derivs["Bmz_dt"][i] - derivs["Bmz_dt"][i-1]) / dt

        # derivs_dtypes = ["<f8"]*12,
        # derivs_names = [
        #     "Bcx_dt", "Bcy_dt", "Bcz_dt",
        #     "Bcx_ddt","Bcy_ddt","Bcz_ddt",
        #     "Bmx_dt", "Bmy_dt", "Bmz_dt",
        #     "Bmx_ddt","Bmy_ddt","Bmz_ddt"
        # ]

        # # Merge derivs with data
        # append_fields(
        #     self.data,
        #     derivs_names,
        #     derivs,
        #     # derivs_dtypes
        # )
        self.data = merge_arrays((self.data, derivs), flatten=True)

        # Component vectors of Ec
        self.Ec_xyz = np.array([
            self.data["Bmx"] - self.data["Bcx"],
            self.data["Bmy"] - self.data["Bcy"],
            self.data["Bmz"] - self.data["Bcz"],
        ])

        # Ec vector obtained by combining three axial components
        self.Ec = np.sqrt(self.Ec_xyz[0]**2 + self.Ec_xyz[1]**2 + self.Ec_xyz[2]**2)

        # Maximum absolute error (uT) for each cardinal component of Ec
        self.Emax_xyz = np.array([
            float(round(max(np.abs(self.Ec_xyz[0])), 3)),
            float(round(max(np.abs(self.Ec_xyz[1])), 3)),
            float(round(max(np.abs(self.Ec_xyz[2])), 3)),
        ])

        # Maximum absolute error (uT) for the Ec error vector
        self.Emax = max(self.Ec)

        # RMS error of all three cardinal components of Ec
        self.Erms_xyz = np.array([
            float(round(np.sqrt(np.mean(self.Ec_xyz[0]**2)), 3)),
            float(round(np.sqrt(np.mean(self.Ec_xyz[1]**2)), 3)),
            float(round(np.sqrt(np.mean(self.Ec_xyz[2]**2)), 3)),
        ])

        # RMS error expressed as a single number by taking abs(Erms_xyz).
        # This is functionally equivalent to taking the RMS of the absolute error vector:
        #   abs(Erms_xyz) = RMS(Ec)
        self.Erms = np.sqrt(self.Erms_xyz[0]**2 + self.Erms_xyz[1]**2 + self.Erms_xyz[2]**2)

        print(f"Max absolute error (x/y/z):     {self.Emax_xyz[0]} / {self.Emax_xyz[1]} / {self.Emax_xyz[2]}  ({round(self.Emax,3)}) \u03BCT")
        print(f"RMS error (x/y/z):              {self.Erms_xyz[0]} / {self.Erms_xyz[1]} / {self.Erms_xyz[2]}  ({round(self.Erms, 3)}) \u03BCT")

        self.Eangle = np.empty_like(self.Ec)
        for i in range(len(self.Eangle)):
            vc = np.array([self.data["Bcx"][i], self.data["Bcy"][i], self.data["Bcz"][i]])
            vm = np.array([self.data["Bmx"][i], self.data["Bmy"][i], self.data["Bmz"][i]])
            vdot = np.dot(vc / np.linalg.norm(vc), vm / np.linalg.norm(vm))
            self.Eangle[i] = 180 / np.pi * np.arccos(vdot)
        self.Eanglemax = max(self.Eangle)
        self.Eanglerms = np.sqrt(np.mean(np.square(self.Eangle)))

        print(f"Max angle error:                {float(round(self.Eanglemax,2))}\u00B0")
        print(f"RMS angle error:                {float(round(self.Eanglerms,2))}\u00B0")

    def doDataAnalysis2(self, Bc2, Bm2):
        sample_time = np.mean(self.data["t"][1:8] - self.data["t"][0:7])

        # Component vectors of Ec
        Ec_xyz2 = np.array([
            Bm2[0] - Bc2[0],
            Bm2[1] - Bc2[1],
            Bm2[2] - Bc2[2],
        ])

        # Ec vector obtained by combining three axial components
        Ec2 = np.sqrt(Ec_xyz2[0]**2 + Ec_xyz2[1]**2 + Ec_xyz2[2]**2)

        # Maximum absolute error (uT) for each cardinal component of Ec
        Emax_xyz2 = np.array([
            float(round(np.max(np.abs(Ec_xyz2[0])), 3)),
            float(round(np.max(np.abs(Ec_xyz2[1])), 3)),
            float(round(np.max(np.abs(Ec_xyz2[2])), 3)),
        ])

        # Maximum absolute error (uT) for the Ec error vector
        Emax2 = np.max(Ec2)

        # RMS error of all three cardinal components of Ec
        Erms_xyz2 = np.array([
            float(np.round(np.sqrt(np.mean(Ec_xyz2[0]**2)), 3)),
            float(np.round(np.sqrt(np.mean(Ec_xyz2[1]**2)), 3)),
            float(np.round(np.sqrt(np.mean(Ec_xyz2[2]**2)), 3)),
        ])

        # RMS error expressed as a single number by taking abs(Erms_xyz).
        # This is functionally equivalent to taking the RMS of the absolute error vector:
        #   abs(Erms_xyz) = RMS(Ec)
        Erms2 = np.sqrt(Erms_xyz2[0]**2 + Erms_xyz2[1]**2 + Erms_xyz2[2]**2)

        print(f"\n ==== FILTERED DATA ====")
        print(f"Max absolute error (x/y/z):     {Emax_xyz2[0]} / {Emax_xyz2[1]} / {Emax_xyz2[2]}  ({round(Emax2,3)}) \u03BCT")
        print(f"RMS error (x/y/z):              {Erms_xyz2[0]} / {Erms_xyz2[1]} / {Erms_xyz2[2]}  ({round(Erms2,3)}) \u03BCT")

        self.Eangle2 = np.empty_like(self.Ec)
        for i in range(len(self.Eangle2)):
            vc = np.array([Bc2[0][i], Bc2[1][i], Bc2[2][i]])
            vm = np.array([Bm2[0][i], Bm2[1][i], Bm2[2][i]])
            vdot = np.dot(vc / np.linalg.norm(vc), vm / np.linalg.norm(vm))
            self.Eangle2[i] = 180 / np.pi * np.arccos(vdot)
        self.Eanglemax2 = max(self.Eangle2)
        self.Eanglerms2 = np.sqrt(np.mean(np.square(self.Eangle2)))

        print(f"Max angle error:                {float(round(self.Eanglemax2,2))}\u00B0")
        print(f"RMS angle error:                {float(round(self.Eanglerms2,2))}\u00B0")

        print(f"\n ==== UNFILTERED/FILTERED DATA COMPARISON ====")
        print(f"{self.data_filename}")
        print(f"Max error:          {round(self.Emax,3)} \u03BCT -> {round(Emax2,3)} \u03BCT  ({-float(round(100*(1-Emax2/self.Emax),1))}%)")
        print(f"RMS error:          {round(self.Erms,3)} \u03BCT -> {round(Erms2,3)} \u03BCT  ({-float(round(100*(1-Erms2/self.Erms),1))}%)")

        print(f"Max angle error:    {float(round(self.Eanglemax,2))}\u00B0 -> {float(round(self.Eanglemax2,2))}\u00B0 ({-float(round(100*(1-self.Eanglemax2/self.Eanglemax),1))}%)")
        print(f"RMS angle error:    {float(round(self.Eanglerms,2))}\u00B0 -> {float(round(self.Eanglerms2,2))}\u00B0 ({-float(round(100*(1-self.Eanglerms2/self.Eanglerms),1))}%)")



class EnvelopeTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.mw = parent

        self.envelope_plot = BcBmEnvelopePlot()

        layout0 = QVBoxLayout()
        layout0.addWidget(self.envelope_plot)
        self.setLayout(layout0)
        # TOP LAYOUT

class ErrorTab1(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.mw = parent

        self.envelope_plot = BcBmEnvelopePlot()
        self.error_plot_abs = ErrorPlotAbs()

        layout0 = QVBoxLayout()
        layout0.addWidget(self.envelope_plot)
        layout0.addWidget(self.error_plot_abs)

        # layout0.addWidget(QLabel("Test"))
        self.setLayout(layout0)
        # TOP LAYOUT

        # self.envelope_plot.generate_envelope_plot(self.mw.data)

class ErrorTab2(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.mw = parent

        self.envelope_plot = BcBmEnvelopePlot()
        self.error_plot_ang = ErrorPlotAngle()

        layout0 = QVBoxLayout()
        layout0.addWidget(self.envelope_plot)
        layout0.addWidget(self.error_plot_ang)

        # layout0.addWidget(QLabel("Test"))
        self.setLayout(layout0)
        # TOP LAYOUT

        # self.envelope_plot.generate_envelope_plot(self.mw.data)

class DerivTab1(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.mw = parent

        # self.envelope_plot = BcBmEnvelopePlot()
        self.deriv_plot = DerivPlot()
        # self.error_plot_abs = ErrorPlotAbs()

        layout0 = QVBoxLayout()
        # layout0.addWidget(self.envelope_plot)
        layout0.addWidget(self.deriv_plot)
        # layout0.addWidget(self.error_plot_abs)

        # layout0.addWidget(QLabel("Test"))
        self.setLayout(layout0)
        # TOP LAYOUT

        # self.envelope_plot.generate_envelope_plot(self.mw.data)

class CurrentTab1(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.mw = parent

        # self.envelope_plot = BcBmEnvelopePlot()
        self.current_plot = CurrentPlot()
        # self.error_plot_abs = ErrorPlotAbs()

        layout0 = QVBoxLayout()
        # layout0.addWidget(self.envelope_plot)
        layout0.addWidget(self.current_plot)
        # layout0.addWidget(self.error_plot_abs)

        # layout0.addWidget(QLabel("Test"))
        self.setLayout(layout0)
        # TOP LAYOUT

        # self.envelope_plot.generate_envelope_plot(self.mw.data)





class DerivPlot(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj_t = self.addPlot(row=0, col=0)
        self.plot_obj_dt = self.addPlot(row=1, col=0)
        self.plot_obj_e = self.addPlot(row=2, col=0)

        self.resize(720, 360)

        self.plot_obj_t.showGrid(x=True, y=True)
        self.plot_obj_t.showAxis('bottom', True)
        self.plot_obj_t.showAxis('left', True)
        self.plot_obj_t.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_t.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj_t.getAxis("left").setScale(scale=1E-6)

        self.plot_obj_dt.showGrid(x=True, y=True)
        self.plot_obj_dt.showAxis('bottom', True)
        self.plot_obj_dt.showAxis('left', True)
        self.plot_obj_dt.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_dt.getAxis("left").setLabel(text="dB/dt", units="T/s")
        self.plot_obj_dt.getAxis("left").setScale(scale=1E-6)

        self.plot_obj_e.showGrid(x=True, y=True)
        self.plot_obj_e.showAxis('bottom', True)
        self.plot_obj_e.showAxis('left', True)
        self.plot_obj_e.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_e.getAxis("left").setLabel(text="Abs error", units="T")
        self.plot_obj_e.getAxis("left").setScale(scale=1E-6)

        # Add a more prominent zero axis
        self.zeroaxis_t = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_t.addItem(self.zeroaxis_t)
        self.zeroaxis_dt = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_dt.addItem(self.zeroaxis_dt)
        self.zeroaxis_e = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_e.addItem(self.zeroaxis_e)

        self.plot_obj_dt.setXLink(self.plot_obj_t)
        self.plot_obj_e.setXLink(self.plot_obj_t)

        # self.vline = pg.InfiniteLine(angle=90, movable=False,
        #                              pen=pg.mkPen("c", width=2),)
        # self.vline.setZValue(10)
        # self.plot_obj.addItem(self.vline, ignoreBounds=True)

        # if data:
        #     self.generate_plot(data)

    def generate_plot(self, data, Ecabs, Ecmag, filter_val: int = 0):
        t = data["t"]
        Bc = array([
            data["Bcx"],
            data["Bcy"],
            data["Bcz"],
        ])
        Bm = array([
            data["Bmx"],
            data["Bmy"],
            data["Bmz"],
        ])
        Bc_dt = array([
            data["Bcx_dt"],
            data["Bcy_dt"],
            data["Bcz_dt"],
        ])
        Bm_dt = array([
            data["Bmx_dt"],
            data["Bmy_dt"],
            data["Bmz_dt"],
        ])

        Bc_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
        Bc_colours_line = [(255, 0, 0, 64), (0, 255, 0, 64), (0, 0, 255, 64)]
        Bm_colours = [(255, 0, 128, 255), (128, 255, 0, 255), (0, 128, 255, 255)]

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        Bc_stag = array((repeat(Bc[0, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[1, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[2, push[0]:push[1]], 2)[:-1],
                         ))

        self.plot_obj_t.clearPlots()
        self.plot_obj_dt.clearPlots()
        self.plot_obj_e.clearPlots()


        # ========= ENVELOPE PLOT ==========
        for i in range(3):
            # Staggered line
            self.plot_obj_t.plot(
                t_stag,
                Bc_stag[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj_t.plot(
                t,
                Bm[i],
                pen=pg.mkPen(Bm_colours[i], width=1)
            )
            self.plot_obj_t.plot(
                t, Bc[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )
            # else:
            #     self.plot_obj.plot(t, Bc[i], pen=Bc_colours[i])
            #
            # if show_points:
            #     self.plot_obj.plot(t, Bc[i],
            #                        pen=(0, 0, 0, 0),
            #                        symbolBrush=(0, 0, 0, 0),
            #                        symbolPen=Bc_colours[i],
            #                        symbol="o",
            #                        symbolSize=6)


        # ========= DT PLOT ==========
        for i in range(3):
            # Staggered line
            self.plot_obj_dt.plot(
                t,
                Bc_dt[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj_dt.plot(
                t,
                Bm_dt[i],
                pen=pg.mkPen(Bm_colours[i], width=1)
            )
            self.plot_obj_dt.plot(
                t, Bc_dt[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )
            # else:
            #     self.plot_obj.plot(t, Bc[i], pen=Bc_colours[i])
            #
            # if show_points:
            #     self.plot_obj.plot(t, Bc[i],
            #                        pen=(0, 0, 0, 0),
            #                        symbolBrush=(0, 0, 0, 0),
            #                        symbolPen=Bc_colours[i],
            #                        symbol="o",
            #                        symbolSize=6)

        # ========= ERROR PLOT ==========
        # If filter window is set 3 or more, apply a Savitsky-Golay filter to
        # the data to smooth out the noisy nature of it.
        if filter_val <= 2:
            Ecmag1 = Ecmag
            Ecabs1 = Ecabs
        else:
            order = int(np.floor(filter_val/2))
            Ecmag1 = savgol_filter(Ecmag, filter_val, order)
            Ecabs1 = np.empty_like(Ecabs)
            for i in range(3):
                Ecabs1[i] = savgol_filter(Ecabs[i], filter_val, order)

        self.plot_obj_e.plot(
            t,
            Ecmag1,
            pen=pg.mkPen((228, 228, 228, 255), width=3)
        )

        for i in range(3):
            # Staggered line
            self.plot_obj_e.plot(
                t,
                Ecabs1[i],
                pen=pg.mkPen(Bc_colours[i], width=2)
            )

class CurrentPlot(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj_t = self.addPlot(row=0, col=0)
        self.plot_obj_i = self.addPlot(row=1, col=0)        # Current from PSU
        # self.plot_obj_is = self.addPlot(row=2, col=0)       # Current by shunt resistors
        self.plot_obj_e = self.addPlot(row=3, col=0)

        self.resize(720, 360)

        self.plot_obj_t.showGrid(x=True, y=True)
        self.plot_obj_t.showAxis('bottom', True)
        self.plot_obj_t.showAxis('left', True)
        self.plot_obj_t.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_t.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj_t.getAxis("left").setScale(scale=1E-6)

        self.plot_obj_i.showGrid(x=True, y=True)
        self.plot_obj_i.showAxis('bottom', True)
        self.plot_obj_i.showAxis('left', True)
        self.plot_obj_i.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_i.getAxis("left").setLabel(text="I", units="A")
        # self.plot_obj_i.getAxis("left").setLabel(text="I (PSU internal)", units="A")

        # self.plot_obj_is.showGrid(x=True, y=True)
        # self.plot_obj_is.showAxis('bottom', True)
        # self.plot_obj_is.showAxis('left', True)
        # self.plot_obj_is.getAxis("bottom").setLabel(text="Time", units="s")
        # self.plot_obj_is.getAxis("left").setLabel(text="I (companion board)", units="A")

        self.plot_obj_e.showGrid(x=True, y=True)
        self.plot_obj_e.showAxis('bottom', True)
        self.plot_obj_e.showAxis('left', True)
        self.plot_obj_e.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj_e.getAxis("left").setLabel(text="Abs error", units="T")
        self.plot_obj_e.getAxis("left").setScale(scale=1E-6)

        # Add a more prominent zero axis
        self.zeroaxis_t = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_t.addItem(self.zeroaxis_t)
        self.zeroaxis_i = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_i.addItem(self.zeroaxis_i)
        # self.zeroaxis_is = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        # self.plot_obj_is.addItem(self.zeroaxis_is)
        self.zeroaxis_e = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj_e.addItem(self.zeroaxis_e)

        self.plot_obj_i.setXLink(self.plot_obj_t)
        # self.plot_obj_is.setXLink(self.plot_obj_t)
        self.plot_obj_e.setXLink(self.plot_obj_t)

        # self.vline = pg.InfiniteLine(angle=90, movable=False,
        #                              pen=pg.mkPen("c", width=2),)
        # self.vline.setZValue(10)
        # self.plot_obj.addItem(self.vline, ignoreBounds=True)

        # if data:
        #     self.generate_plot(data)

    def generate_plot(self, data, Ecabs, Ecmag, filter_val: int = 0):
        t = data["t"]
        Bc = array([
            data["Bcx"],
            data["Bcy"],
            data["Bcz"],
        ])
        Bm = array([
            data["Bmx"],
            data["Bmy"],
            data["Bmz"],
        ])
        Ic = array([
            data["Icx"],
            data["Icy"],
            data["Icz"],
        ])

        printim = False
        try:  # TODO this is here to have temporary compatibility with old datasets
            Is = array([
                data["Imx"],
                data["Imy"],
                data["Imz"],
            ])
            printim = True
        except:
            pass

        Bc_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
        Bc_colours_line = [(255, 0, 0, 64), (0, 255, 0, 64), (0, 0, 255, 64)]
        Bm_colours = [(255, 0, 128, 255), (128, 255, 0, 255), (0, 128, 255, 255)]

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        Bc_stag = array((repeat(Bc[0, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[1, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[2, push[0]:push[1]], 2)[:-1],
                         ))

        self.plot_obj_t.clearPlots()
        self.plot_obj_i.clearPlots()
        # self.plot_obj_is.clearPlots()
        self.plot_obj_e.clearPlots()


        # ========= ENVELOPE PLOT ==========
        for i in range(3):
            # Staggered line
            self.plot_obj_t.plot(
                t_stag,
                Bc_stag[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj_t.plot(
                t,
                Bm[i],
                pen=pg.mkPen(Bm_colours[i], width=1)
            )
            self.plot_obj_t.plot(
                t, Bc[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )

        # ========= Ic CURRENT PLOT ==========
        for i in range(3):
            # Staggered line
            self.plot_obj_i.plot(
                t,
                Ic[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj_i.plot(
                t, Ic[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )

        # ========= Is CURRENT PLOT ==========
        if printim:
            for i in range(3):
                # Staggered line
                self.plot_obj_i.plot(
                    t,
                    Is[i],
                    pen=pg.mkPen(Bm_colours[i], width=1),
                )
                self.plot_obj_i.plot(
                    t, Is[i],
                    pen=(0, 0, 0, 0),
                    symbolBrush=(0, 0, 0, 0),
                    symbolPen=Bm_colours[i],
                    symbol="o",
                    symbolSize=2.5
                )

        # ========= ERROR PLOT ==========
        # If filter window is set 3 or more, apply a Savitsky-Golay filter to
        # the data to smooth out the noisy nature of it.
        if filter_val <= 2:
            Ecmag1 = Ecmag
            Ecabs1 = Ecabs
        else:
            order = int(np.floor(filter_val/2))
            Ecmag1 = savgol_filter(Ecmag, filter_val, order)
            Ecabs1 = np.empty_like(Ecabs)
            for i in range(3):
                Ecabs1[i] = savgol_filter(Ecabs[i], filter_val, order)

        self.plot_obj_e.plot(
            t,
            Ecmag1,
            pen=pg.mkPen((228, 228, 228, 255), width=3)
        )

        for i in range(3):
            # Staggered line
            self.plot_obj_e.plot(
                t,
                Ecabs1[i],
                pen=pg.mkPen(Bc_colours[i], width=2)
            )


# class CurrentPlot(pg.GraphicsLayoutWidget):
#     def __init__(self):
#         super().__init__()
#
#         self.plot_obj_t = self.addPlot(row=0, col=0)
#         self.plot_obj_i = self.addPlot(row=1, col=0)        # Current from PSU
#         # self.plot_obj_is = self.addPlot(row=2, col=0)       # Current by shunt resistors
#         self.plot_obj_e = self.addPlot(row=3, col=0)
#
#         self.resize(720, 360)
#
#         self.plot_obj_t.showGrid(x=True, y=True)
#         self.plot_obj_t.showAxis('bottom', True)
#         self.plot_obj_t.showAxis('left', True)
#         self.plot_obj_t.getAxis("bottom").setLabel(text="Time", units="s")
#         self.plot_obj_t.getAxis("left").setLabel(text="B", units="T")
#         self.plot_obj_t.getAxis("left").setScale(scale=1E-6)
#
#         self.plot_obj_i.showGrid(x=True, y=True)
#         self.plot_obj_i.showAxis('bottom', True)
#         self.plot_obj_i.showAxis('left', True)
#         self.plot_obj_i.getAxis("bottom").setLabel(text="Time", units="s")
#         self.plot_obj_i.getAxis("left").setLabel(text="I", units="A")
#         # self.plot_obj_i.getAxis("left").setLabel(text="I (PSU internal)", units="A")
#
#         # self.plot_obj_is.showGrid(x=True, y=True)
#         # self.plot_obj_is.showAxis('bottom', True)
#         # self.plot_obj_is.showAxis('left', True)
#         # self.plot_obj_is.getAxis("bottom").setLabel(text="Time", units="s")
#         # self.plot_obj_is.getAxis("left").setLabel(text="I (companion board)", units="A")
#
#         self.plot_obj_e.showGrid(x=True, y=True)
#         self.plot_obj_e.showAxis('bottom', True)
#         self.plot_obj_e.showAxis('left', True)
#         self.plot_obj_e.getAxis("bottom").setLabel(text="Time", units="s")
#         self.plot_obj_e.getAxis("left").setLabel(text="Abs error", units="T")
#         self.plot_obj_e.getAxis("left").setScale(scale=1E-6)
#
#         # Add a more prominent zero axis
#         self.zeroaxis_t = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
#         self.plot_obj_t.addItem(self.zeroaxis_t)
#         self.zeroaxis_i = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
#         self.plot_obj_i.addItem(self.zeroaxis_i)
#         # self.zeroaxis_is = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
#         # self.plot_obj_is.addItem(self.zeroaxis_is)
#         self.zeroaxis_e = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
#         self.plot_obj_e.addItem(self.zeroaxis_e)
#
#         self.plot_obj_i.setXLink(self.plot_obj_t)
#         # self.plot_obj_is.setXLink(self.plot_obj_t)
#         self.plot_obj_e.setXLink(self.plot_obj_t)
#
#         # self.vline = pg.InfiniteLine(angle=90, movable=False,
#         #                              pen=pg.mkPen("c", width=2),)
#         # self.vline.setZValue(10)
#         # self.plot_obj.addItem(self.vline, ignoreBounds=True)
#
#         # if data:
#         #     self.generate_plot(data)
#
#     def generate_plot(self, data, Ecabs, Ecmag, filter_val: int = 0):
#         t = data["t"]
#         Bc = array([
#             data["Bcx"],
#             data["Bcy"],
#             data["Bcz"],
#         ])
#         Bm = array([
#             data["Bmx"],
#             data["Bmy"],
#             data["Bmz"],
#         ])
#         Ic = array([
#             data["Icx"],
#             data["Icy"],
#             data["Icz"],
#         ])
#
#         printim = False
#         try:  # TODO this is here to have temporary compatibility with old datasets
#             Is = array([
#                 data["Imx"],
#                 data["Imy"],
#                 data["Imz"],
#             ])
#             printim = True
#         except:
#             pass
#
#         Bc_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
#         Bc_colours_line = [(255, 0, 0, 64), (0, 255, 0, 64), (0, 0, 255, 64)]
#         Bm_colours = [(255, 0, 128, 255), (128, 255, 0, 255), (0, 128, 255, 255)]
#
#         # Generate staggered dataset by copying using repeat and then shifting
#         push = [0, -1]
#         t_stag = repeat(t[push[0]:push[1]], 2)[1:]
#         Bc_stag = array((repeat(Bc[0, push[0]:push[1]], 2)[:-1],
#                          repeat(Bc[1, push[0]:push[1]], 2)[:-1],
#                          repeat(Bc[2, push[0]:push[1]], 2)[:-1],
#                          ))
#
#         self.plot_obj_t.clearPlots()
#         self.plot_obj_i.clearPlots()
#         # self.plot_obj_is.clearPlots()
#         self.plot_obj_e.clearPlots()
#
#
#         # ========= ENVELOPE PLOT ==========
#         for i in range(3):
#             # Staggered line
#             self.plot_obj_t.plot(
#                 t_stag,
#                 Bc_stag[i],
#                 pen=pg.mkPen(Bc_colours_line[i], width=1),
#             )
#             self.plot_obj_t.plot(
#                 t,
#                 Bm[i],
#                 pen=pg.mkPen(Bm_colours[i], width=1)
#             )
#             self.plot_obj_t.plot(
#                 t, Bc[i],
#                 pen=(0, 0, 0, 0),
#                 symbolBrush=(0, 0, 0, 0),
#                 symbolPen=Bc_colours[i],
#                 symbol="o",
#                 symbolSize=2.5
#             )
#
#         # ========= Ic CURRENT PLOT ==========
#         for i in range(3):
#             # Staggered line
#             self.plot_obj_i.plot(
#                 t,
#                 Ic[i],
#                 pen=pg.mkPen(Bc_colours_line[i], width=1),
#             )
#             self.plot_obj_i.plot(
#                 t, Ic[i],
#                 pen=(0, 0, 0, 0),
#                 symbolBrush=(0, 0, 0, 0),
#                 symbolPen=Bc_colours[i],
#                 symbol="o",
#                 symbolSize=2.5
#             )
#
#         # ========= Is CURRENT PLOT ==========
#         if printim:
#             for i in range(3):
#                 # Staggered line
#                 self.plot_obj_i.plot(
#                     t,
#                     Is[i],
#                     pen=pg.mkPen(Bm_colours[i], width=1),
#                 )
#                 self.plot_obj_i.plot(
#                     t, Is[i],
#                     pen=(0, 0, 0, 0),
#                     symbolBrush=(0, 0, 0, 0),
#                     symbolPen=Bm_colours[i],
#                     symbol="o",
#                     symbolSize=2.5
#                 )
#
#         # ========= ERROR PLOT ==========
#         # If filter window is set 3 or more, apply a Savitsky-Golay filter to
#         # the data to smooth out the noisy nature of it.
#         if filter_val <= 2:
#             Ecmag1 = Ecmag
#             Ecabs1 = Ecabs
#         else:
#             order = int(np.floor(filter_val/2))
#             Ecmag1 = savgol_filter(Ecmag, filter_val, order)
#             Ecabs1 = np.empty_like(Ecabs)
#             for i in range(3):
#                 Ecabs1[i] = savgol_filter(Ecabs[i], filter_val, order)
#
#         self.plot_obj_e.plot(
#             t,
#             Ecmag1,
#             pen=pg.mkPen((228, 228, 228, 255), width=3)
#         )
#
#         for i in range(3):
#             # Staggered line
#             self.plot_obj_e.plot(
#                 t,
#                 Ecabs1[i],
#                 pen=pg.mkPen(Bc_colours[i], width=2)
#             )


class BcBmEnvelopePlot(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="B", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-6)

        # Add a more prominent zero axis
        self.zeroaxis = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj.addItem(self.zeroaxis)

        # self.vline = pg.InfiniteLine(angle=90, movable=False,
        #                              pen=pg.mkPen("c", width=2),)
        # self.vline.setZValue(10)
        # self.plot_obj.addItem(self.vline, ignoreBounds=True)

        # if data:
        #     self.generate_plot(data)

    def generate_plot(self, data, show_actual=True, show_points=False):
        t = data["t"]
        Bc = array([
            data["Bcx"],
            data["Bcy"],
            data["Bcz"],
        ])
        Bm = array([
            data["Bmx"],
            data["Bmy"],
            data["Bmz"],
        ])
        Bc_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
        Bc_colours_line = [(255, 0, 0, 64), (0, 255, 0, 64), (0, 0, 255, 64)]
        # Bm_colours = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]
        Bm_colours = [(255, 0, 128, 255), (128, 255, 0, 255), (0, 128, 255, 255)]

        # Generate staggered dataset by copying using repeat and then shifting
        push = [0, -1]
        t_stag = repeat(t[push[0]:push[1]], 2)[1:]
        Bc_stag = array((repeat(Bc[0, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[1, push[0]:push[1]], 2)[:-1],
                         repeat(Bc[2, push[0]:push[1]], 2)[:-1],
                         ))
        # Bm_stag = array((repeat(Bm[0, push[0]:push[1]], 2)[:-1],
        #                  repeat(Bm[1, push[0]:push[1]], 2)[:-1],
        #                  repeat(Bm[2, push[0]:push[1]], 2)[:-1],
        #                  ))

        self.plot_obj.clearPlots()

        for i in range(3):
            # Staggered line
            self.plot_obj.plot(
                t_stag,
                Bc_stag[i],
                pen=pg.mkPen(Bc_colours_line[i], width=1),
            )
            self.plot_obj.plot(
                t,
                Bm[i],
                pen=pg.mkPen(Bm_colours[i], width=1)
            )
            self.plot_obj.plot(
                t, Bc[i],
                pen=(0, 0, 0, 0),
                symbolBrush=(0, 0, 0, 0),
                symbolPen=Bc_colours[i],
                symbol="o",
                symbolSize=2.5
            )
            # else:
            #     self.plot_obj.plot(t, Bc[i], pen=Bc_colours[i])
            #
            # if show_points:
            #     self.plot_obj.plot(t, Bc[i],
            #                        pen=(0, 0, 0, 0),
            #                        symbolBrush=(0, 0, 0, 0),
            #                        symbolPen=Bc_colours[i],
            #                        symbol="o",
            #                        symbolSize=6)

class ErrorPlotAbs(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="Ec_abs", units="T")
        self.plot_obj.getAxis("left").setScale(scale=1E-6)

        # Add a more prominent zero axis
        self.zeroaxis = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj.addItem(self.zeroaxis)


    def generate_plot(self, data, Ecabs, Ecmag, filter_val: int = 0):
        t = data["t"]

        Ec_colours = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128)]
        # Ec_colours = [(255, 0, 128, 255), (64, 255, 0, 255), (0, 128, 255, 255)]


        # If filter window is set 3 or more, apply a Savitsky-Golay filter to
        # the data to smooth out the noisy nature of it.
        if filter_val <= 2:
            Ecmag1 = Ecmag
            Ecabs1 = Ecabs
        else:
            order = int(np.floor(filter_val/2))
            Ecmag1 = savgol_filter(Ecmag, filter_val, order)
            Ecabs1 = np.empty_like(Ecabs)
            for i in range(3):
                Ecabs1[i] = savgol_filter(Ecabs[i], filter_val, order)

        self.plot_obj.clearPlots()

        self.plot_obj.plot(
            t,
            Ecmag1,
            pen=pg.mkPen((228, 228, 228, 255), width=3)
        )

        for i in range(3):
            # Staggered line
            self.plot_obj.plot(
                t,
                Ecabs1[i],
                pen=pg.mkPen(Ec_colours[i], width=2)
            )

class ErrorPlotAngle(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__()

        self.plot_obj = self.addPlot(row=0, col=0)
        self.resize(720, 360)
        self.plot_obj.showGrid(x=True, y=True)
        self.plot_obj.showAxis('bottom', True)
        self.plot_obj.showAxis('left', True)
        self.plot_obj.getAxis("bottom").setLabel(text="Time", units="s")
        self.plot_obj.getAxis("left").setLabel(text="E_angle", units="\u00B0")
        self.plot_obj.getAxis("left").setScale(scale=1)

        # Add a more prominent zero axis
        self.zeroaxis = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen((255,255,255,255), width=2))
        self.plot_obj.addItem(self.zeroaxis)

    def generate_plot(self, data, Eangle, Eanglemean):
        t = data["t"]
        # dur = t[-1]-t[0]
        self.plot_obj.clearPlots()

        # lineColour = (255, 228, 0, 192)   # Yellow
        # lineColour = (255, 87, 0, 192)   # Dark orange
        lineColour = (255, 100, 0, 255)   # Light orange
        # Average line
        self.plot_obj.plot(
            # np.array([t[0]-0.02*dur, t[-1]+0.02*dur]),
            np.array([t[0], t[-1]]),

            np.array([Eanglemean, Eanglemean]),
            pen=pg.mkPen(lineColour, width=3)
        )

        self.plot_obj.plot(
            t,
            Eangle,
            pen=pg.mkPen(lineColour, width=2)
        )

    def generate_plot2(self, data, Eangle, Eanglemean, Eangle2, Eanglemean2):
        t = data["t"]
        # dur = t[-1]-t[0]
        self.plot_obj.clearPlots()

        lineColour = (255, 100, 0, 255)   # Light orange
        lineColour2 = (0, 192, 255, 255)   # Light blue
        # lineColour2 = (0, 255, 32, 192)   # Light green

        # Average line
        self.plot_obj.plot(
            # np.array([t[0]-0.02*dur, t[-1]+0.02*dur]),
            np.array([t[0], t[-1]]),

            np.array([Eanglemean, Eanglemean]),
            pen=pg.mkPen(lineColour, width=3)
        )
        self.plot_obj.plot(
            # np.array([t[0]-0.02*dur, t[-1]+0.02*dur]),
            np.array([t[0], t[-1]]),

            np.array([Eanglemean2, Eanglemean2]),
            pen=pg.mkPen(lineColour2, width=3)
        )

        self.plot_obj.plot(
            t,
            Eangle,
            pen=pg.mkPen(lineColour, width=2)
        )
        self.plot_obj.plot(
            t,
            Eangle2,
            pen=pg.mkPen(lineColour2, width=2)
        )


class Cage3DTab(GLViewWidget):
    def __init__(self, parent, config, data):
        super().__init__()

        # print("[DEBUG] Cage3DPlot.__init__() called")
        self.mw = parent
        self.data = data
        self.config = config
        self.resize(720, 360)

        # Shorthands for common config settings
        self.ps = self.config["c3dcw_plotscale"]  # Plot scale
        self.c = self.config["ov_plotcolours"]
        self.aa = self.config["ov_use_antialiasing"]
        self.zo = self.config["c3dcw_cage_dimensions"]["z_offset"] * self.ps
        self.zov = array([0.0, 0.0, self.zo])
        self.linescale = 1

        print("zov 0 ", self.zov)

        self.tail_length = self.config["c3dcw_tail_length"]

        self.opts["center"] = QVector3D(0, 0, self.zo)
        self.setCameraPosition(distance=5*self.ps, azimuth=-20, elevation=25)
        # self.setCameraPosition(distance=5*self.ps, pos=(0, 0, 2.5*self.ps))

        self.max_b_absvals = np.array([200, 200, 200])
        self.draw_statics()


    def draw_statics(self):

        """Draws static objects into the GLViewWidget. Static objects are
        objects whose plots are independent of the schedule or simulation data,
        and so they ideally are drawn only once.
        """

        # print("[DEBUG] Cage3DPlot.draw_statics() called")

        # Generate grid
        self.make_xy_grid()

        # Generate frame tripod_components
        self.make_tripod_b()

        # Generate cage structure components
        self.make_cage_structure()

        # Generate satellite model
        self.make_satellite_model()

    def draw_simdata(self, data_index = 1):
        max_b_absvals = [
            max(abs(min(self.mw.data2["Bcx"])), abs(max(self.mw.data2["Bcx"]))),
            max(abs(min(self.mw.data2["Bcy"])), abs(max(self.mw.data2["Bcy"]))),
            max(abs(min(self.mw.data2["Bcz"])), abs(max(self.mw.data2["Bcz"]))),
        ]

        self.linescale = 0.85 * (100/max(max_b_absvals))
        # print(f"[DEBUG] B_abs_max: {max(max_b_absvals)}")
        # print(f"[DEBUG] LINE SCALE set to {self.linescale}")

        if self.mw.data is None:     # If simdata is not generated yet, skip plotting
            return 0

        self.make_lineplot_Bc()
        if data_index in [1, 2]:
            self.make_lineplot_Bm(data_index, normalize_value=0)
        # self.make_linespokes()

    def make_xy_grid(self):
        # Add horizontal grid
        self.xy_grid = GLGridItem(antialias=self.aa)
        self.xy_grid.setColor((255, 255, 255, 24))
        self.xy_grid.setSize(x=2*self.ps, y=2*self.ps)
        self.xy_grid.setSpacing(x=int(self.ps/10), y=int(self.ps/10))  # Comment out this line at your peril...
        self.xy_grid.setDepthValue(20)  # Ensure grid is drawn after most other features

        if self.config["c3d_draw"]["xy_grid"]:
            self.addItem(self.xy_grid)

    def make_tripod_b(self):
        self.frame_b = PGFrame3D(o=self.zov)
        self.tripod_b = plotframe2(
            self.frame_b,
            plotscale=0.25 * self.ps, alpha=0.8, antialias=self.aa
        )
        if self.config["c3d_draw"]["tripod_b"]:
            for item in self.tripod_b:
                self.addItem(item)

    def make_cage_structure(self):
        self.cage_structure = []

        scale = self.ps
        dim_x = self.config["c3d_cage_dimensions"]["x"]
        dim_y = self.config["c3d_cage_dimensions"]["y"]
        dim_z = self.config["c3d_cage_dimensions"]["z"]
        dim_t = self.config["c3d_cage_dimensions"]["t"]
        s = self.config["c3d_cage_dimensions"]["spacing"]

        m = [1, 1, -1, -1, 1, 1]

        alpha = self.config["c3d_cage_alpha"]

        # Make an array containing all corners of the cage structure, and
        # repeat the first entry at the end to "close" it when plotting.

        # X-coils
        x_coil_pos = array(
            [[dim_x * s / 2, m[i] * dim_x / 2, m[i + 1] * dim_x / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        x_coil_neg = 1 * x_coil_pos  # 1 * array is a poor man's deepcopy()
        x_coil_neg[:, 0] = -1 * x_coil_neg[:, 0]

        self.cage_structure.append(GLLinePlotItem(
            pos=x_coil_pos,
            color=(0.5, 0, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=x_coil_neg,
            color=(0.5, 0, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))


        # Y-coils
        y_coil_pos = array(
            [[m[i] * dim_y / 2, dim_y * s / 2, m[i + 1] * dim_y / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        y_coil_neg = 1 * y_coil_pos
        y_coil_neg[:, 1] = -1 * y_coil_neg[:, 1]

        self.cage_structure.append(GLLinePlotItem(
            pos=y_coil_pos,
            color=(0, 0.5, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=y_coil_neg,
            color=(0, 0.5, 0, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))


        # Z-coils
        z_coil_pos = array(
            [[m[i] * dim_z / 2, m[i + 1] * dim_z / 2, dim_z * s / 2 + self.zo/self.ps] for i in range(5)]
        )*scale
        z_coil_neg = 1 * z_coil_pos
        z_coil_neg[:, 2] = (-1 * (z_coil_neg[:, 2] - self.zo/self.ps*scale)) + self.zo/self.ps*scale

        self.cage_structure.append(GLLinePlotItem(
            pos=z_coil_pos,
            color=(0.15, 0.15, 0.5, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))
        self.cage_structure.append(GLLinePlotItem(
            pos=z_coil_neg,
            color=(0.15, 0.15, 0.5, alpha),
            width=5,
            antialias=self.config["ov_use_antialiasing"]
        ))

        if self.config["c3d_draw"]["cage_structure"]:
            for element in self.cage_structure:
                self.addItem(element)

    def make_satellite_model(self):
        [x_dim, y_dim, z_dim, x, y, z] = \
        [self.config["c3d_satellite_model"][item] for item in
         ["x_dim", "y_dim", "z_dim", "x", "y", "z"]]
        corners = array([
            [ x_dim / 2,  y_dim / 2, -z_dim / 2],
            [ x_dim / 2, -y_dim / 2, -z_dim / 2],
            [-x_dim / 2, -y_dim / 2, -z_dim / 2],
            [-x_dim / 2,  y_dim / 2, -z_dim / 2],
            [ x_dim / 2,  y_dim / 2,  z_dim / 2],
            [ x_dim / 2, -y_dim / 2,  z_dim / 2],
            [-x_dim / 2, -y_dim / 2,  z_dim / 2],
            [-x_dim / 2,  y_dim / 2,  z_dim / 2],
        ]) * self.ps

        points = []
        for i in range(8):
            points.append(corners[i])
            points.append(corners[(i+4) % 8])
            points.append(corners[i])
            if i == 3:
                points.append(corners[0])
            if i == 7:
                points.append(corners[4])

        points = array(points)

        for i, point in enumerate(points):
            points[i] = point + array([x, y, z])*self.ps + self.zov
        #
        # # Offset all the data for plotting purposes
        # for i in range(len(points)):
        #     points[i][2] = points[i][2]+self.zo

        self.satellite_model = GLLinePlotItem(
            pos=points,
            # color=self.c[self.config["c3d_preferred_colour"]],
            color=(1.0, 0.5, 0.0, 0.4),
            width=3,
            antialias=self.config["ov_use_antialiasing"]
        )
        self.satellite_model.setDepthValue(0)

        if self.config["c3d_draw"]["satellite_model"]:
            self.addItem(self.satellite_model)

    def make_lineplot_Bc(self):

        points = np.array([
            self.mw.data["Bcx"],
            self.mw.data["Bcy"],
            self.mw.data["Bcz"],
        ]).transpose() * self.linescale

        # print("/n [DEBUG] Bc[0:10], Bc[-10:]")
        # print(points[:][0:10], "\n")
        # print(points[:][-10:], "\n")

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.config["c3d_preferred_colour"]],
            color=(1, 1, 1, 0.25),
            width=2,
            antialias=self.config["ov_use_antialiasing"]
        )
        self.lineplot.setDepthValue(1)

        if self.config["c3d_draw"]["lineplot"]:
            self.addItem(self.lineplot)

    def make_lineplot_Bm(self, data_index = 1, normalize_value: float = 0.0):
        # Ecabs = self.mw.Ecabs
        # Ecmag = np.sqrt(Ecabs[0]**2 + Ecabs[1]**2 + Ecabs[2]**2)
        # Ecmax = max(Ecmag)
        # Ecnorm = Ecmag/Ecmax

        # print("Ecmax: ", Ecmax)
        Enorm = None

        if self.mw.manifold_colour_angle:
            if normalize_value <= 0:  # Normalize to Ecmax
                Emax = self.mw.Eanglemax
                Enorm = self.mw.Eangle / Emax
            else:
                Enorm = self.mw.Eangle / normalize_value
        else:
            if normalize_value <= 0:  # Normalize to Ecmax
                Emax = max(self.mw.Ecmag)
                Enorm = self.mw.Ecmag / Emax
            else:
                Enorm = self.mw.Ecmag / normalize_value

        colour_array = np.array([
            Enorm,
            1 - Enorm,
            np.zeros(len(Enorm)),
            np.zeros(len(Enorm)) + 0.75,
        ]).transpose()

        # colour_array = [
        #     Ecnorm.tolist(),
        #     (1 - Ecnorm).tolist(),
        #     (np.ones(len(Ecnorm))).tolist(),
        #     (np.zeros(len(Ecnorm)) + 0.25).tolist(),
        # ]

        points = np.array([
            self.mw.data["Bmx"],
            self.mw.data["Bmy"],
            self.mw.data["Bmz"],
        ]).transpose() * self.linescale

        if data_index == 2:
            points = np.array([
                self.mw.data2["Bmx"],
                self.mw.data2["Bmy"],
                self.mw.data2["Bmz"],
            ]).transpose() * self.linescale
        # print("/n [DEBUG] Bm[0:10], Bm[-10:]")
        # print(points[:][0:10], "\n")
        # print(points[:][-10:], "\n")

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo

        self.lineplot = GLLinePlotItem(
            pos=points,
            # color=self.c[self.config["c3d_preferred_colour"]],
            # color=[Ecnorm, 1-Ecnorm, np.full(1.), np.full((0.25)],
            color=colour_array,
            # color=(1.0, 0.3, 0.0, 0.25),
            width=2,
            antialias=self.config["ov_use_antialiasing"]
        )
        self.lineplot.setDepthValue(1)

        if self.config["c3d_draw"]["lineplot"]:
            self.addItem(self.lineplot)

    def make_linespokes(self):
        # Add all line spokes as one long line, so it fits in one big GLLinePlotItem,
        # which is MUCH more efficient than making one for each spoke.
        ppoints = np.array([
            self.mw.data["Bcx"],
            self.mw.data["Bcy"],
            self.mw.data["Bcz"],
        ]).transpose()

        for i in range(len(ppoints)):
            ppoints[i][2] = ppoints[i][2]+self.zo

        points = []
        for i in range(len(self.mw.data["t"])):
            points.append(ppoints[i])
            points.append(3/4*ppoints[i])
            points.append(ppoints[i])

        # Offset all the data for plotting purposes
        for i in range(len(points)):
            points[i][2] = points[i][2]+self.zo/2

        self.linespokes = GLLinePlotItem(
            pos=points,
            color=(0.5, 0.5, 0.5, 0.1),
            antialias=self.config["ov_use_antialiasing"],
            width=1)
        self.linespokes.setDepthValue(0)

        if self.config["c3d_draw"]["linespokes"]:
            self.addItem(self.linespokes)

        return None


if __name__ == "__main__":

    app = QApplication(sys.argv)

    theme_file = "dark_teal.xml"
    apply_stylesheet(app, theme=theme_file)

    window = TestEvalWindowMain(config)
    window.show()
    app.exec()