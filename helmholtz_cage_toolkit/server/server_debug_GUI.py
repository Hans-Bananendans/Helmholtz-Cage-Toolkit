import sys

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.server.server_config import server_config as config
from helmholtz_cage_toolkit.server.control_lib import *


# Helper subclasses for QLabel to facilitate neat one-liners later on
class QLabelCenter(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)


class QLabelRight(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignRight)


class QLabelLeft(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignLeft)


class QLabelCenterB(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel {font-weight: bold;}")


class QLabelRightB(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignRight)
        self.setStyleSheet("QLabel {font-weight: bold;}")


class QLabelLeftB(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("QLabel {font-weight: bold;}")


class DebugWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()

        # Load config
        self.config = config

        self.resize(960, 640)

        self.initialize_devices()

        layout0 = QGridLayout()

        self.layout_inputs = self.make_layout_inputs()
        self.layout_pinout = self.make_layout_pinout()
        self.layout_10 = self.make_layout_10()
        self.layout_biv = self.make_layout_biv()

        layout0.addLayout(self.layout_inputs, 0, 0)
        layout0.addLayout(self.layout_pinout, 0, 1)
        layout0.addLayout(self.layout_10, 1, 0)
        layout0.addLayout(self.layout_biv, 1, 1)


        centralwidget = QWidget()
        centralwidget.setLayout(layout0)
        self.setCentralWidget(centralwidget)



        # ==== TIMERS
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)

        # Make a menu bar (must be made after layout generation and timers)
        menubar = self.make_menubar()
        self.setMenuBar(menubar)


    def make_menubar(self):

        menubar = QMenuBar()

        menu_settings = menubar.addMenu("&Settings")

        # ====================================================================

        menu_settings.addSection("Pinout style")

        actgroup_pinout = QActionGroup(menu_settings)

        act_pinout_adcdac = QAction("Use ADC/DAC pinout", self)
        act_pinout_adcdac.setStatusTip(
            "Use pin numbers as listed on the ADC/DAC")
        act_pinout_adcdac.setActionGroup(actgroup_pinout)
        act_pinout_adcdac.setCheckable(True)
        act_pinout_adcdac.triggered.connect(
            lambda: self.set_pinout("adcdac"))
        menu_settings.addAction(act_pinout_adcdac)

        act_pinout_board = QAction("Use board pinout", self)
        act_pinout_board.setStatusTip(
            "Use pin numbers as numbered on the CN0554 board")
        act_pinout_board.setActionGroup(actgroup_pinout)
        act_pinout_board.setCheckable(True)
        act_pinout_board.triggered.connect(
            lambda: self.set_pinout("board"))
        menu_settings.addAction(act_pinout_board)

        # Default
        act_pinout_board.setChecked(True)
        self.set_pinout("board")

        # ====================================================================

        menu_settings.addSection("Update rate")

        actgroup_update = QActionGroup(menu_settings)

        act_update_stop = QAction("STOP", self)
        act_update_stop.setStatusTip(
            "Suspend the updating of values.")
        act_update_stop.setActionGroup(actgroup_update)
        act_update_stop.setCheckable(True)
        act_update_stop.triggered.connect(lambda: self.set_update_rate(-1))
        menu_settings.addAction(act_update_stop)

        act_update_01 = QAction("0.1 Hz", self)
        act_update_01.setStatusTip(
            "Update values and GUI every 10 seconds.")
        act_update_01.setActionGroup(actgroup_update)
        act_update_01.setCheckable(True)
        act_update_01.triggered.connect(lambda: self.set_update_rate(0.1))
        menu_settings.addAction(act_update_01)

        act_update_1 = QAction("1 Hz", self)
        act_update_1.setStatusTip(
            "Update values and GUI every second.")
        act_update_1.setActionGroup(actgroup_update)
        act_update_1.setCheckable(True)
        act_update_1.triggered.connect(lambda: self.set_update_rate(1))
        menu_settings.addAction(act_update_1)

        act_update_10 = QAction("10 Hz", self)
        act_update_10.setStatusTip(
            "Update values and GUI every 100 ms.")
        act_update_10.setActionGroup(actgroup_update)
        act_update_10.setCheckable(True)
        act_update_10.triggered.connect(lambda: self.set_update_rate(10))
        menu_settings.addAction(act_update_10)

        act_update_30 = QAction("30 Hz", self)
        act_update_30.setStatusTip(
            "Update values and GUI every 33 ms.")
        act_update_30.setActionGroup(actgroup_update)
        act_update_30.setCheckable(True)
        act_update_30.triggered.connect(lambda: self.set_update_rate(30))
        menu_settings.addAction(act_update_30)

        # Default: 1 Hz rate
        act_update_1.setChecked(True)
        self.set_update_rate(1)

        return menubar


    def make_layout_inputs(self):
        layout_inputs = QGridLayout()

        # Spacer
        layout_inputs.addWidget(QLabel(" "*84), 20, 0, 1, 7)

        self.button_reset = QPushButton("RESET ALL")
        self.button_reset.setStyleSheet("""QPushButton {font-size: 24px;}""")
        self.button_reset.clicked.connect(self.reset)
        layout_inputs.addWidget(self.button_reset, 0, 0, 1, 7)


        label_vx = QLabel("V_X")
        layout_inputs.addWidget(label_vx, 1, 0)
        self.le_vx = QLineEdit()
        self.le_vx.setPlaceholderText("V")
        layout_inputs.addWidget(self.le_vx, 1, 1)
        label_ix = QLabel("I_X")
        layout_inputs.addWidget(label_ix, 1, 3)
        self.le_ix = QLineEdit()
        self.le_ix.setPlaceholderText("mA")
        layout_inputs.addWidget(self.le_ix, 1, 4)
        self.button_polx = QPushButton("INV")
        self.button_polx.clicked.connect(lambda: self.set_polarity("x"))
        self.button_polx.setCheckable(True)
        self.button_polx.setChecked(False)
        layout_inputs.addWidget(self.button_polx, 1, 6)

        label_vy = QLabel("V_y")
        layout_inputs.addWidget(label_vy, 2, 0)
        self.le_vy = QLineEdit()
        self.le_vy.setPlaceholderText("V")
        layout_inputs.addWidget(self.le_vy, 2, 1)
        label_iy = QLabel("I_y")
        layout_inputs.addWidget(label_iy, 2, 3)
        self.le_iy = QLineEdit()
        self.le_iy.setPlaceholderText("mA")
        layout_inputs.addWidget(self.le_iy, 2, 4)
        self.button_poly = QPushButton("INV")
        self.button_poly.clicked.connect(lambda: self.set_polarity("y"))
        self.button_poly.setCheckable(True)
        self.button_poly.setChecked(False)
        layout_inputs.addWidget(self.button_poly, 2, 6)

        label_vz = QLabel("V_z")
        layout_inputs.addWidget(label_vz, 3, 0)
        self.le_vz = QLineEdit()
        self.le_vz.setPlaceholderText("V")
        layout_inputs.addWidget(self.le_vz, 3, 1)
        label_iz = QLabel("I_z")
        layout_inputs.addWidget(label_iz, 3, 3)
        self.le_iz = QLineEdit()
        self.le_iz.setPlaceholderText("mA")
        layout_inputs.addWidget(self.le_iz, 3, 4)
        self.button_polz = QPushButton("INV")
        self.button_polz.clicked.connect(lambda: self.set_polarity("z"))
        self.button_polz.setCheckable(True)
        self.button_polz.setChecked(False)
        layout_inputs.addWidget(self.button_polz, 3, 6)


        self.button_set_v = QPushButton("Set V")
        self.button_set_v.clicked.connect(self.set_v)
        layout_inputs.addWidget(self.button_set_v, 4, 0, 1, 2)

        self.button_set_i = QPushButton("Set I")
        self.button_set_i.clicked.connect(self.set_i)
        layout_inputs.addWidget(self.button_set_i, 4, 3, 1, 2)

        self.button_psu_enable = QPushButton("PSU enable")
        self.button_psu_enable.clicked.connect(self.enable_psu)
        self.button_psu_enable.setCheckable(True)
        self.button_psu_enable.setChecked(False)
        layout_inputs.addWidget(self.button_psu_enable, 4, 6)

        return layout_inputs


    def make_layout_pinout(self):
        layout_pinout = QGridLayout()

        # Top headers
        layout_pinout.addWidget(QLabelCenterB("DAC"), 0, 2, 1, 2)
        layout_pinout.addWidget(QLabelCenterB("ADC"), 0, 8, 1, 2)

        for i in (1, 4, 7, 10):
            layout_pinout.addWidget(QLabelCenter("     [mV]     "), 0, i)

        self.adc_vallabels = []
        self.dac_vallabels = []

        dict_pinnames = self.map_config_pinnames_dict()

        # Value labels
        for i in (4, 5, 6, 7, 9, 10, 11, 12):
            label_dac_l = QLabelRight("-9.999")
            label_dac_r = QLabelRight("-9.999")
            label_adc_l = QLabelRight("-9.999")
            label_adc_r = QLabelRight("")

            layout_pinout.addWidget(label_dac_l, i+1, 1)
            layout_pinout.addWidget(label_dac_r, i+1, 4)
            self.dac_vallabels.append(label_dac_l)
            self.dac_vallabels.append(label_dac_r)

            layout_pinout.addWidget(label_adc_l, i+1, 7)
            layout_pinout.addWidget(label_adc_r, i+1, 10)
            self.adc_vallabels.append(label_adc_l)
            self.adc_vallabels.append(label_adc_r)

        for i in range(15):
            # layout_pinout.addWidget(QLabelRight("Name"), i+1, 0)
            layout_pinout.addWidget(QLabelRightB(
                dict_pinnames["dac"][2*i],),
                i+1, 0)

            layout_pinout.addWidget(QLabelLeftB(
                dict_pinnames["dac"][2*i+1],),
                i+1, 5)
            # layout_pinout.addWidget(QLabelLeft("Name"), i+1, 5)
            # layout_pinout.addWidget(QLabelRight("Name"), i+1, 6)
            layout_pinout.addWidget(QLabelRightB(
                dict_pinnames["adc"][2*i],),
                i+1, 6)

            # layout_pinout.addWidget(QLabelLeft("Name"), i+1, 11)
            layout_pinout.addWidget(QLabelLeftB(
                dict_pinnames["adc"][2*i+1],),
                i+1, 11)


        self.adc_pinlabels = []
        self.dac_pinlabels = []

        for i in range(15):
            label_dac_l = QLabelCenterB(str(2*i))
            label_dac_r = QLabelCenterB(str(2*i+1))
            label_adc_l = QLabelCenterB(str(2*i))
            label_adc_r = QLabelCenterB(str(2*i+1))

            for label in (label_dac_l, label_dac_r, label_adc_l, label_adc_r):
                label.setAlignment(Qt.AlignCenter)
                label.setFrameStyle(QFrame.Box | QFrame.Plain)
                label.setLineWidth(3)

            layout_pinout.addWidget(label_dac_l, i+1, 2)
            layout_pinout.addWidget(label_dac_r, i+1, 3)
            self.dac_pinlabels.append(label_dac_l)
            self.dac_pinlabels.append(label_dac_r)

            layout_pinout.addWidget(label_adc_l, i+1, 8)
            layout_pinout.addWidget(label_adc_r, i+1, 9)
            self.adc_pinlabels.append(label_adc_l)
            self.adc_pinlabels.append(label_adc_r)

        layout_pinout.setRowStretch(17, 1)
        for col in (0, 5, 6, 11):
            layout_pinout.setColumnStretch(col, 2)
        # for col in (1, 4, 7, 10):
        #     layout_pinout.setColumnStretch(col, 1)
        layout_pinout.setVerticalSpacing(2)
        layout_pinout.setHorizontalSpacing(2)

        return layout_pinout


    def make_layout_10(self):
        layout_10 = QGridLayout()
        # label_layout10 = QLabel("layout_10")
        # label_layout10.setFrameStyle(QFrame.Box | QFrame.Plain)
        # label_layout10.setLineWidth(1)
        # layout_10.addWidget(label_layout10)
        return layout_10


    def make_layout_biv(self):
        layout_biv = QGridLayout()


        # self.labels_biv = [[0,]*3,]*6
        self.labels_biv = [
            [0.,0.,0.], [0.,0.,0.], [0.,0.,0.], [0.,0.,0.], [0.,0.,0.], [0.,0.,0.]
            ]

        print(self.labels_biv)

        for i in range(7):
            texth = ["", "Vvc [V]", "Vc [V]", "Vcc [V]", "Ic [mA]", "Im [mA]", "B [\u03bcT]"][i]
            if i == 6:
                layout_biv.addWidget(QLabelCenterB(texth), 0, i)
            else:
                layout_biv.addWidget(QLabelCenter(texth), 0, i)

        for i, string in enumerate(("X", "Y", "Z", "norm")):
            layout_biv.addWidget(QLabel(string), i+1, 0)

        # <header>   <Vvc>   <Vc>   <Vcc>   <Ic>   <Im>
        phs = ["-99.999", "-99.999", "-99.999", "9.999", "9.999", "-9999.999"]
        for i in range(0, 6):
            for j in range(0, 3):
                if i+1 == 6:
                    self.labels_biv[i][j] = QLabelCenterB(phs[i])
                else:
                    self.labels_biv[i][j] = QLabelCenter(phs[i])
                layout_biv.addWidget(self.labels_biv[i][j], j+1, i+1)

        # Norm of Bm
        self.label_b = QLabelCenterB("-9999.999")
        layout_biv.addWidget(self.label_b, 4, 6)

        for i, stretch in enumerate((1, 1, 1, 1, 1, 1, 1, 2)):
            layout_biv.setColumnStretch(i, stretch)

        # print(self.labels_biv)
        # print(type(self.labels_biv[1][1]))

        return layout_biv


    def map_config_pinnames_dict(self):
        """ Helper function that takes config entries with keys 'pin_adc_' and
        'pin_dac_', and maps the names of these pins onto a dict that has the
        board pin numbers as keys, and the assigned pin names as values.
        """

        # Dict whose keys are adc/dac pin numbers, and labels are empty strings
        pinnames = dict([
            ("dac", {i: "" for i in range(16)}),
            ("adc", {i: "" for i in range(16)})
        ])

        # Matching config "pin_" entries with entry in pinnames and copy name
        # for k, v in config.items():
        #     if k[0:4] == "pin_":
        #         pinnames[k[4:7]][v] = k[8:]
        for k, v in self.config.items():
            if k[0:8] == "pin_dac_":
                pinnames["dac"][v] = k[8:]
            elif k[0:8] == "pin_adc_":
                pinnames["adc"][2*v]   = k[8:]+"+"
                pinnames["adc"][2*v+1] = k[8:]+"-"

        # Make a larger dict for board pin numbers
        pinnames_board = dict([
            ("dac", {i: "" for i in range(0, 30)}) ,
            ("adc", {i: "" for i in range(0, 30)})
        ])

        # Map names of adc/dac pinnames:
        for i in range(8):
            pinnames_board["dac"][i+8] = pinnames["dac"][i]
            pinnames_board["dac"][i+18] = pinnames["dac"][i+8]

            pinnames_board["adc"][i+8] = pinnames["adc"][i]
            pinnames_board["adc"][i+18] = pinnames["adc"][i+8]

        # Map ground pins:
        for i in (16, 17, 26, 27):
            pinnames_board["dac"][i] = "GND"
            pinnames_board["adc"][i] = "GND"

        return pinnames_board


    def set_update_rate(self, rate: float):
        print(f"[DEBUG] set_update_rate({rate})")
        self.timer_update.stop()

        if rate > 0:
            self.timer_update.start(int(1000/rate))


    def set_pinout(self, style: str):
        print(f"[DEBUG] set_pinout({style})")

        if style == "adcdac":
            for i in range(30):
                if i in range(8, 16):
                    self.dac_pinlabels[i].setText(str(i-8))
                    self.adc_pinlabels[i].setText(str(i-8))
                elif i in range(18, 26):
                    self.dac_pinlabels[i].setText(str(i-10))
                    self.adc_pinlabels[i].setText(str(i-10))
                else:
                    self.dac_pinlabels[i].setText("")
                    self.adc_pinlabels[i].setText("")
        elif style == "board":
            for i in range(30):
                self.dac_pinlabels[i].setText(str(i))
                self.adc_pinlabels[i].setText(str(i))
        else:
            raise ValueError(
                f"Given style variable '{style}'. Allowed: 'adcdac', 'board'")

    def update(self):
        # t0 = time()

        # Read DAC outputs
        dac_outputs, timestamp = dac_get_voltage(self.dac_channels)
        # t1 = time()
        # Read ADC inputs
        adc_inputs, _ = adc_measurement(self.adc_channels)
        # t2 = time()
        for i, value in enumerate(dac_outputs):
            self.dac_vallabels[i].setText(str(int(dac_outputs[i])))

        # t3 = time()
        for i, value in enumerate(adc_inputs):
            self.adc_vallabels[2*i].setText("{:.3f}".format(adc_inputs[i]))
        # t4 = time()


        vvc_vals = [dac_outputs[config["pin_dac_supply_x_vvc"]]/1000, 
                    dac_outputs[config["pin_dac_supply_y_vvc"]]/1000, 
                    dac_outputs[config["pin_dac_supply_z_vvc"]]/1000]

        vcc_vals = [dac_outputs[config["pin_dac_supply_x_vcc"]]/1000, 
                    dac_outputs[config["pin_dac_supply_y_vcc"]]/1000, 
                    dac_outputs[config["pin_dac_supply_z_vcc"]]/1000]

        vc_vals = [0., 0., 0.]
        cc_vals = [0., 0., 0.]
        
        for i in range(3):
            vc_vals[i] = self.supplies[i].params_tf_vc[0]*vvc_vals[i] + self.supplies[i].params_tf_vc[1]
            cc_vals[i] = self.supplies[i].params_tf_cc[0]*vcc_vals[i] + self.supplies[i].params_tf_cc[1]
            if vc_vals[i] < 0:
                vc_vals[i] = 0.0
            if cc_vals[i] < 0:
                cc_vals[i] = 0.0

        # print("vvc_vals:", vvc_vals)
        # print("vc_vals:", vc_vals)
        # print("vcc_vals:", vcc_vals)
        # print("cc_vals:", cc_vals)

        for i in range(3):
            self.labels_biv[0][i].setText("{:.3f}".format(vvc_vals[i]))
            self.labels_biv[1][i].setText("{:.3f}".format(vc_vals[i]))
            self.labels_biv[2][i].setText("{:.3f}".format(vcc_vals[i]))
            self.labels_biv[3][i].setText("{:.3f}".format(cc_vals[i]))

            self.labels_biv[4][i].setText("TODO")


        # mV:mG to V:uT -> multiply by 100
        bvals = [adc_inputs[config["pin_adc_channel_bmx"]]*100, 
                 adc_inputs[config["pin_adc_channel_bmy"]]*100, 
                 adc_inputs[config["pin_adc_channel_bmz"]]*100]
        
        for i, bval in enumerate([bvals[0], bvals[1], bvals[2]]):
            self.labels_biv[5][i].setText("{:.2f}".format(bval))

        bnorm = (bvals[0]**2 + bvals[1]**2 + bvals[2]**2)**0.5
        self.label_b.setText("{:.2f}".format(bnorm))

        # print("update(): {} {} {} {} = {} ms".format(
        #     round((t1-t0)*1000, 1),
        #     round((t2-t1)*1000, 1),
        #     round((t3-t2)*1000, 1),
        #     round((t4-t3)*1000, 1),
        #     round((t4-t0)*1000, 1)
        # ))


    # def read_adcdac(self):
    #     # t0 = time()

    #     # Read DAC outputs
    #     dac_outputs, timestamp = dac_get_voltage(self.dac_channels)
    #     # t1 = time()
    #     # Read ADC inputs
    #     adc_inputs, _ = adc_measurement(self.adc_channels)
    #     # t2 = time()
    #     for i, value in enumerate(dac_outputs):
    #         self.dac_vallabels[i].setText(str(int(dac_outputs[i])))

    #     # t3 = time()
    #     for i, value in enumerate(adc_inputs):
    #         self.adc_vallabels[2*i].setText("{:.5f}".format(adc_inputs[i]))
    #     # t4 = time()

    #     # print("read_adcdac(): {} {} {} {} = {} ms".format(
    #     #     round((t1-t0)*1000, 1),
    #     #     round((t2-t1)*1000, 1),
    #     #     round((t3-t2)*1000, 1),
    #     #     round((t4-t3)*1000, 1),
    #     #     round((t4-t0)*1000, 1)
    #     # ))


    # def update_biv(self):

    #     bvals = [adc_inputs["pin_adc_channel_bmx"], adc_inputs["pin_adc_channel_bmx"], 
    #              self.adc_inputs["pin_adc_channel_bmx"]]
    #     for bval in []:

    #     self.labels_biv

    def reset(self):
        print("[DEBUG] read_reset()")
        for supply in (self.supply_x, self.supply_y, self.supply_z):
            supply.set_zero_output(verbose=6)
        for button in (self.button_polx, self.button_poly, self.button_polz):
            button.setChecked(False)
        print("SUCCESS")


    def initialize_devices(self):
        print("[DEBUG] initialize_devices()")

        _VERBOSE = 6
        self.cn0554_object = cn0554_setup()

        self.adc_channels = adc_channel_setup(self.cn0554_object, verbose=_VERBOSE)
        self.dac_channels = dac_channel_setup(self.cn0554_object, verbose=_VERBOSE)

        self.supply_x = PowerSupply(self.dac_channels[config["pin_dac_supply_x_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_x_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_x_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    r_load=config["r_load"],
                                    v_above=config["v_above"],
                                    i_above=config["i_above"],
                                    params_tf_vc=config["params_tf_vc_x"],
                                    params_tf_cc=config["params_tf_cc_x"],
                                    verbose=_VERBOSE)

        self.supply_y = PowerSupply(self.dac_channels[config["pin_dac_supply_y_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_y_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_y_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    r_load=config["r_load"],
                                    v_above=config["v_above"],
                                    i_above=config["i_above"],
                                    params_tf_vc=config["params_tf_vc_y"],
                                    params_tf_cc=config["params_tf_cc_y"],
                                    verbose=_VERBOSE)

        self.supply_z = PowerSupply(self.dac_channels[config["pin_dac_supply_z_vvc"]], 
                                    self.dac_channels[config["pin_dac_supply_z_vcc"]],
                                    self.dac_channels[config["pin_dac_supply_z_pol"]],
                                    vmax=config["vmax_supply"],
                                    imax=config["imax_supply"],
                                    vpol=config["vlevel_pol"],
                                    r_load=config["r_load"],
                                    v_above=config["v_above"],
                                    i_above=config["i_above"],
                                    params_tf_vc=config["params_tf_vc_z"],
                                    params_tf_cc=config["params_tf_cc_z"],
                                    verbose=_VERBOSE)
        self.supplies = (self.supply_x, self.supply_y, self.supply_z)

        self.psu_enable_pin = PSU_ENABLE(self.dac_channels[config["pin_dac_psu_enable"]],
                                         config["v_psu_enable"],
                                         verbose=_VERBOSE)


    def set_v(self):
        print(f"[DEBUG] set_v()")

        for i, le in enumerate([self.le_vx, self.le_vy, self.le_vz]):
            try:
                v_val = float(le.text())
            except:
                print(f"Error: Input '{le.text()}' could not be interpreted as float.")
                v_val = 0.0
            self.supplies[i].set_voltage_out(v_val)

    def set_i(self):
        print(f"[DEBUG] set_i()")
        
        for i, le in enumerate([self.le_ix, self.le_iy, self.le_iz]):
            try:
                i_val = float(le.text())/1000
            except:
                print(f"Error: Input '{le.text()}' could not be interpreted as float.")
                i_val = 0.0
            
            # Clip if value is too high
            if i_val > config["imax_supply"]:
                i_val = config["imax_supply"]

            self.supplies[i].set_current_out(i_val)

    def enable_psu(self):
        if self.button_psu_enable.isChecked() is True:
            self.psu_enable_pin.set(1)
        else:
            self.psu_enable_pin.set(0)
    
    def set_polarity(self, axis):
        print(f"[DEBUG] set_polarity({axis})")

        lookup = {
            "x": (self.supply_x, self.button_polx),
            "y": (self.supply_y, self.button_poly),
            "z": (self.supply_z, self.button_polz),
            }
        
        if axis not in ("x", "y", "z"):
            raise ValueError(f"Invalid axis '{axis}' given!")
        
        supply, button = lookup[axis]

        if button.isChecked() is True:
            supply.reverse_polarity(True)
        else:
            supply.reverse_polarity(False)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = DebugWindow(config)
    window.show()
    app.exec()