import sys

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.server.server_config import server_config as config


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
        self.setAlignment(Qt.AlignLeft)
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
        self.layout_b = self.make_layout_b()
        self.layout_vi = self.make_layout_vi()

        layout0.addLayout(self.layout_inputs, 0, 0)
        layout0.addLayout(self.layout_pinout, 0, 1)
        layout0.addLayout(self.layout_b, 1, 0)
        layout0.addLayout(self.layout_vi, 1, 1)


        centralwidget = QWidget()
        centralwidget.setLayout(layout0)
        self.setCentralWidget(centralwidget)



        # ==== TIMERS
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.read_adcdac)


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

        # Default
        act_update_01.setChecked(True)
        self.set_update_rate(0.1)

        return menubar


    def make_layout_inputs(self):
        layout_inputs = QGridLayout()

        # Spacer
        layout_inputs.addWidget(QLabel(" "*84), 20, 0, 1, 7)

        self.button_reset = QPushButton("RESET ALL")
        self.button_reset.setStyleSheet("""QPushButton {font-size: 24px;}""")
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



        return layout_inputs


    def make_layout_pinout(self):
        layout_pinout = QGridLayout()

        # Top headers
        layout_pinout.addWidget(QLabelCenterB("DAC"), 0, 2, 1, 2)
        layout_pinout.addWidget(QLabelCenterB("ADC"), 0, 8, 1, 2)

        for i in (1, 4, 7, 10):
            layout_pinout.addWidget(QLabelCenter("     [V]     "), 0, i)

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


    def make_layout_b(self):
        layout_b = QGridLayout()
        layout_b.addWidget(QLabel("layout_b"))
        return layout_b

    def make_layout_vi(self):
        layout_vi = QGridLayout()
        layout_vi.addWidget(QLabel("layout_vi"))
        return layout_vi


    def map_config_pinnames_dict(self):
        """ Helper function that takes config entries with keys 'pin_adc_' and
        'pin_adc_', and maps the names of these pins onto a dict that has the
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
            ("dac", {i: "" for i in range(0, 30)}),
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

    def read_adcdac(self):
        print("[DEBUG] read_adcdac()") # TODO IMPLEMENT

    def initialize_devices(self):
        print("[DEBUG] read_adcdac()") # TODO IMPLEMENT

    def set_v(self):
        print(f"[DEBUG] set_v()") # TODO IMPLEMENT

    def set_i(self):
        print(f"[DEBUG] set_i()") # TODO IMPLEMENT

    def set_polarity(self, axis):
        print(f"[DEBUG] set_polarity({axis})") # TODO IMPLEMENT

        # DISTINGUISH BETWEEN CLICKED STATE


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = DebugWindow(config)
    window.show()
    app.exec()