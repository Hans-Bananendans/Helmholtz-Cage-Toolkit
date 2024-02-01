"""
CommandWindow - layout0 (HBox)
│
├── layout_left (VBox)
│   ├── group_mode_controls
│   │   └── layout_mode_controls (Grid)
│   ├── group_offset_controls
│   │   └── layout_offset_controls (VBox)
│   │       ├── layout_offset_inputs (HBox)
│   │       └── layout_offset_buttons (HBox)
│   ├── group_record_controls
│   │   └── layout_record_controls (VBox)
│   │       ├── layout_record_fileselect (HBox)
│   │       └── layout_record_buttons (HBox)
│   └── group_play_controls
│       └── layout_play_controls (VBox)
│           ├── stacker_play_controls (QStackedLayout)
│           │   ├── layout_play_checks (Grid)
│           │   └── layout_play_stats (Grid)
│           └── layout_play_buttons (HBox)
│
└── layout_right (VBox)
    ├── stacker_right (QStackedLayout)
    │   ├── manual_controls (Grid)
    │   └── layout_schedule_envelope (HBox)
    │       └── schedule_envelope (GraphicsLayout)
    ├── group_bm_monitor
    │   └── layout_bm_monitor (HBox)
    └── layout_hhcplot (Grid)
        ├── HHCPlot YZ (GraphicsLayout)
        └── HHCPlot -XY (GraphicsLayout)
"""

import os
from time import time, sleep

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.datapool import DataPool
from helmholtz_cage_toolkit.cyclics_window import HHCPlot

class CommandWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool



        self.checks_icon_paths = (
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/wave_ffd200.svg",
            "./assets/icons/check_00aa00.svg",
        )

        # TODO Migrate to datapool
        self.checks = {
            "connection_up":
                {"text": ["Unconnected to device",
                          "<unimplemented>",
                          "Connected to device"],
                 "value": 0,
                 },
            "schedule_ready":
                {"text": ["No schedule ready on device",
                          "<unimplemented>",
                          "Schedule ready on device"],
                 "value": 0,
                 },
            "recording":
                {"text": ["No recording output selected!",
                          "Recording not on/armed",
                          "Ready to record data"],
                 "value": 1,
                 },
            "dummy_check1":
                {"text": ["dummy1 x",
                          "dummy1 ~",
                          "dummy1 tick"],
                 "value": 2,
                 },
            "dummy_check2":
                {"text": ["dummy2 x",
                          "dummy2 ~",
                          "dummy2 tick"],
                 "value": 1,
                 },
            "dummy_check3":
                {"text": ["dummy3 x",
                          "dummy3 ~",
                          "dummy3 tick"],
                 "value": 0,
                 },
        }


        layout_left = QVBoxLayout()

        group_mode_controls = self.make_group_mode_controls()
        group_offset_controls = self.make_group_offset_controls()
        group_record_controls = self.make_group_record_controls()
        group_play_controls = self.make_group_play_controls()

        for groupbox in (group_mode_controls, group_offset_controls,
                         group_record_controls, group_play_controls):
            groupbox.setStyleSheet(
                self.datapool.config["stylesheet_groupbox_smallmargins"]
            )
            layout_left.addWidget(groupbox)


        layout_right = QVBoxLayout()

        self.group_manual_input = GroupManualInput(self.datapool)
        layout_right.addWidget(self.group_manual_input)

        self.group_manual_input.do_update_biv_labels()

        dummy_widget = QLabel("DUMMY WIDGET")
        dummy_widget.setMinimumWidth(720)
        layout_right.addWidget(dummy_widget)


        layout0 = QHBoxLayout()
        layout0.addLayout(layout_left)
        layout0.addLayout(layout_right)

        self.setLayout(layout0)


    def make_group_mode_controls(self):
        layout_mode_controls = QGridLayout()

        self.button_panic_reset = QPushButton(
            # QIcon("./assets/icons/feather/x-octagon.svg"), "RESET")
            QIcon("./assets/icons/feather/x-circle.svg"), "RESET")
        self.button_panic_reset.setIconSize(QSize(24, 24))
        self.button_panic_reset.setStyleSheet("""
        QPushButton {font-size: 24px;}
        """)

        self.button_set_manual_mode = QPushButton(
            QIcon("./assets/icons/feather/edit-3.svg"), "Manual")
        self.button_set_play_mode = QPushButton(
            QIcon("./assets/icons/feather/film.svg"), "Schedule")

        layout_mode_controls.addWidget(self.button_panic_reset, 0, 0, 1, 2)
        layout_mode_controls.addWidget(self.button_set_manual_mode, 1, 0)
        layout_mode_controls.addWidget(self.button_set_play_mode, 1, 1)

        group_mode_controls = QGroupBox()
        group_mode_controls.setLayout(layout_mode_controls)
        group_mode_controls.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        return group_mode_controls

    def make_group_offset_controls(self):
        layout_offset_inputs = QHBoxLayout()

        layout_offset_inputs.addWidget(QLabel("Field vector to reject:"))

        self.le_brx = QLineEdit()
        self.le_bry = QLineEdit()
        self.le_brz = QLineEdit()

        for i, le in enumerate((self.le_brx, self.le_bry, self.le_brz)):
            # le.setMaximumWidth(72)
            le.setAlignment(Qt.AlignCenter)
            le.setPlaceholderText(("x", "y", "z")[i]+" [\u03bcT]")
            le.setText("0.0")
            layout_offset_inputs.addWidget(le)

        layout_offset_inputs.addWidget(QLabel("[\u03bcT]"))


        layout_offset_buttons = QHBoxLayout()

        self.button_set_br = QPushButton("Set")
        layout_offset_buttons.addWidget(self.button_set_br)

        self.button_br_from_bm = QPushButton(QIcon(
            "./assets/icons/feather/corner-left-up.svg"), "Take current B_M")
        layout_offset_buttons.addWidget(self.button_br_from_bm)


        layout_offset_controls = QVBoxLayout()

        # layout_offset_controls.addWidget(QLabel("Field vector to reject:"))
        layout_offset_controls.addLayout(layout_offset_inputs)
        layout_offset_controls.addLayout(layout_offset_buttons)

        group_offset_controls = QGroupBox("OFFSET CONTROLS")
        group_offset_controls.setLayout(layout_offset_controls)
        group_offset_controls.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        return group_offset_controls

    def make_group_record_controls(self):

        layout_record_fileselect = QHBoxLayout()

        layout_record_fileselect.addWidget(QLabel("Target file:"))

        self.le_record_file = QLineEdit()
        self.le_record_file.setReadOnly(True)
        self.le_record_file.setPlaceholderText("<no file selected>")
        layout_record_fileselect.addWidget(self.le_record_file)

        self.button_record_fileselect = QPushButton("...")
        self.button_record_fileselect.clicked.connect(self.do_set_target)
        layout_record_fileselect.addWidget(self.button_record_fileselect)

        layout_record_buttons = QHBoxLayout()

        self.button_record_start = QPushButton(
            QIcon("./assets/icons/feather/circle.svg"), "RECORD")
        # self.button_record_start.clicked.connect()  # TODO
        layout_record_buttons.addWidget(self.button_record_start)

        self.button_record_arm = QPushButton(
            QIcon("./assets/icons/feather/alert-triangle.svg"), "ARM")
        # self.button_record_arm.clicked.connect()  # TODO
        layout_record_buttons.addWidget(self.button_record_arm)

        layout_record_buttons.addWidget(QLabel("   Sample rate:"))

        self.le_record_rate = QLineEdit()
        self.le_record_rate.setAlignment(Qt.AlignCenter)
        self.le_record_rate.setMaximumWidth(64)
        self.le_record_rate.setPlaceholderText("<sample rate>")
        self.le_record_rate.setText("30")
        layout_record_buttons.addWidget(self.le_record_rate)

        layout_record_buttons.addWidget(QLabel("S/s"))


        layout_record_controls = QVBoxLayout()
        layout_record_controls.addLayout(layout_record_fileselect)
        layout_record_controls.addLayout(layout_record_buttons)

        group_record_controls = QGroupBox("RECORD CONTROLS")
        group_record_controls.setLayout(layout_record_controls)
        group_record_controls.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins"]
        )
        return group_record_controls

    def make_group_play_controls(self):

        self.stacker_play_controls = QStackedWidget()


        self.layout_play_checks = QGridLayout()

        # It's tricky to manipulate widgets by referring to them in their
        # layout, as this returns QWidgetItems, rather than the actual item.
        # So instead, gather widgets in a nested list stored in the class
        # instance, for easier reference.
        self.checks_widgets = []

        for i in range(len(self.checks)):
            # Nest new widget pair list into whole list
            self.checks_widgets.append([
                QSvgWidget("./assets/icons/feather/frown.svg"),
                QLabel("<init>")
            ])

            # Any widget pair pre-processing:
            self.checks_widgets[i][0].setFixedSize(QSize(20, 20))

            # Fill slots of grid up with dummy QSvgWidgets and QLabels:
            self.layout_play_checks.addWidget(self.checks_widgets[i][0], i, 0)
            self.layout_play_checks.addWidget(self.checks_widgets[i][1], i, 1)

        # Then propagate it again according to values in self.checks:
        self.do_update_check_widgets()

        widget_play_checks = QWidget()
        widget_play_checks.setLayout(self.layout_play_checks)

        #                                    index 0
        self.stacker_play_controls.addWidget(widget_play_checks)


        self.layout_play_stats = QGridLayout()

        self.label_play_status = QLabel("<init>")
        self.layout_play_stats.addWidget(QLabel("Status:"), 0, 0)
        self.layout_play_stats.addWidget(self.label_play_status, 0, 1)

        self.label_play_name = QLabel("<init>")
        self.layout_play_stats.addWidget(QLabel("Schedule:"), 1, 0)
        self.layout_play_stats.addWidget(self.label_play_name, 1, 1)

        self.label_play_step = QLabel("<init>")
        self.layout_play_stats.addWidget(QLabel("Step:"), 2, 0)
        self.layout_play_stats.addWidget(self.label_play_step, 2, 1)

        self.label_play_time = QLabel("<init>")
        self.layout_play_stats.addWidget(QLabel("Time:"), 3, 0)
        self.layout_play_stats.addWidget(self.label_play_time, 3, 1)

        # Assign proper values by calling update function:
        self.do_update_play_stats_labels()

        widget_play_stats = QWidget()
        widget_play_stats.setLayout(self.layout_play_stats)

        #                                    index 1
        self.stacker_play_controls.addWidget(widget_play_stats)


        layout_play_buttons = QHBoxLayout()

        self.button_check = QPushButton(
            QIcon("./assets/icons/feather/check-square.svg"), "Check")
        self.button_check.clicked.connect(self.run_checks)
        layout_play_buttons.addWidget(self.button_check)

        self.button_start_playback = QPushButton(
            QIcon("./assets/icons/feather/play.svg"), "PLAY")
        self.button_start_playback.setCheckable(True)
        self.button_start_playback.clicked.connect(self.do_start_playback)
        layout_play_buttons.addWidget(self.button_start_playback)


        layout_play_controls = QVBoxLayout()

        layout_play_controls.addWidget(QLabel("Checks:"))
        layout_play_controls.addWidget(self.stacker_play_controls)
        layout_play_controls.addLayout(layout_play_buttons)

        group_play_controls = QGroupBox("PLAY CONTROLS")
        group_play_controls.setLayout(layout_play_controls)

        return group_play_controls




    def do_update_check_widgets(self):
        i = 0
        for key, check_item in self.checks.items():
            # Update "icon" QSvgWidget:
            self.checks_widgets[i][0].load(
                self.checks_icon_paths[check_item["value"]])

            # Update QLabel:
            self.checks_widgets[i][1].setText(
                check_item["text"][check_item["value"]])
            if check_item["value"] == 0 and not self.checks_widgets[i][1].isEnabled():
                self.checks_widgets[i][1].setEnabled(True)
            elif check_item["value"] != 0 and self.checks_widgets[i][1].isEnabled():
                self.checks_widgets[i][1].setEnabled(False)

            # self.layout_play_checks.replaceWidget(
            #     self.layout_play_checks.itemAtPosition(i, 0),
            #     self.checks_icons[check_item["value"]])

            # self.layout_play_checks.itemAt(i).load(
            #     self.checks_icon_paths[check_item["value"]])

            # self.layout_play_checks.itemAtPosition(i, 0).load(
            #     self.checks_icon_paths[check_item["value"]])


            # label_icon = self.layout_play_checks.itemAtPosition(i, 0)
            # label_icon.setIcon(self.checks_icons[check_item["value"]])

            # Update text of related QLabel
            # label_text = self.layout_play_checks.itemAtPosition(i, 1)
            # label_text.setText(check_item["text"][check_item["value"]])
            i += 1

    def do_update_play_stats_labels(self):
        # TODO: Implement properly
        self.label_play_status.setText("0.0")
        self.label_play_name.setText("0.0")
        self.label_play_step.setText("0.0")
        self.label_play_time.setText("0.0")


    def run_checks(self):
        # TODO: Check conditions and set values of self.checks as
        #  appropriate, then run do_update_check_widgets
        print("[DEBUG] run_checks()")


    def do_set_target(self):
        # TODO IMPLEMENT
        print("[DEBUG] do_set_target()")

    def do_start_playback(self):
        # TODO IMPLEMENT
        print("[DEBUG] start_playback()")

        if self.button_start_playback.isChecked():

            # DO A TIME SYNC WITH SERVER

            # IF ARMED, START RECORDING

            # SEND START COMMAND

            self.button_start_playback.setIcon(
                QIcon("./assets/icons/feather/square.svg"))
            self.button_start_playback.setText("STOP")

            # SWAP TO PLAYBACK WINDOW:
            self.stacker_play_controls.setCurrentIndex(1)

            # START TIMER POLLING FOR SCHEDULE DATA AND UPDATING


        # STOP
        else:
            # Swap to checks window:
            self.stacker_play_controls.setCurrentIndex(0)

            self.do_post_playback()



    def do_post_playback(self):
        # TODO ANY EXTRA POST-PLAYBACK FUNCTIONS GO HERE
        self.button_start_playback.setEnabled(False)
        self.button_start_playback.setIcon(
            QIcon("./assets/icons/feather/refresh-ccw.svg"))
        self.button_start_playback.setText("RESETTING...")

        # DUMMY TIMER
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.do_enable_start_button)
        self.reset_timer.start(2000)


    def do_enable_start_button(self):
        self.button_start_playback.setEnabled(True)
        self.button_start_playback.setIcon(
            QIcon("./assets/icons/feather/play.svg"))
        self.button_start_playback.setText("PLAY")





class GroupManualInput(QGroupBox):
    def __init__(self, datapool):
        super().__init__("Manual input")

        self.datapool = datapool

        self.setStyleSheet(self.datapool.config["stylesheet_groupbox_smallmargins"])

        layout0 = QGridLayout()
        layout0.setHorizontalSpacing(8)

        self.biv_labels = []  # Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id

        styles = ["QLabel {color: #ffaaaa;}", "QLabel {color: #aaffaa;}",
                  "QLabel {color: #aaaaff;}", "QLabel {}"]

        for i, var in enumerate(
                ["Bc", "Br", "Bo", "Bm", "Bd", "Vc", "Ic", "Im", "Id"]):
            varlist = []
            for j in range(4):
                if i >= 5 and j == 3:
                    label = QLabel("")  # Empty summed voltage and current entries
                else:
                    label = QLabel("<{}_{}>".format(var, ("x", "y", "z", "T")[j]))
                    # label.setMaximumWidth(84)
                    label.setAlignment(Qt.AlignRight)
                    label.setStyleSheet(styles[j])  # Add colour if needed
                varlist.append(label)
            self.biv_labels.append(varlist)

        header_text = ["Bc", "Br", "Bo", "Bm", "Bd", "Vc", "Ic", "Im", "Id"]
        header_units = ["\u03bcT"]*5 + ["V"] + ["mA"]*3
        header_labels = []
        for i in range(len(header_text)):
            label = QLabel("{}\n[{}]".format(header_text[i], header_units[i]))
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumWidth(64)
            header_labels.append(label)

        self.combo_input = QComboBox()
        self.combo_input.setMinimumWidth(96)
        self.combo_input.addItems(["Bc [\u03bcT]", "Bc [nT]", "Ic [mA]"])

        self.le_inputs = [QLineEdit("0.0"), QLineEdit("0.0"), QLineEdit("0.0")]
        for i, le in enumerate(self.le_inputs):
            le.setMaxLength(9)
            le.setPlaceholderText(("x value", "y value", "z value")[i])
            le.setAlignment(Qt.AlignCenter)

        self.button_submit = QPushButton("Submit")

        # ==== Putting widgets into layout

        # Input column:
        layout0.addWidget(self.combo_input, 0, 0)
        for j in range(3):
            layout0.addWidget(self.le_inputs[j], j+1, 0)
        layout0.addWidget(self.button_submit, 4, 0)

        # Header labels
        for i in range(9):
            layout0.addWidget(header_labels[i], 0, i+1)
        # Value labels
        for i in range(9):
            for j in range(4):
                layout0.addWidget(self.biv_labels[i][j], j+1, i+1)

        self.setLayout(layout0)

    def do_update_biv_labels(self):
        print("[DEBUG] GroupManualInput.do_update_biv_labels()")
        # Mapping biv_labels: Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id
        # Bo = Bc-Br
        # Bd = Bo-Bm
        # Id = Ic-Im

        # DUMMIES
        self.Bc = [50., 50., 50.]
        self.Br = [-5., 2.5, -45.]
        self.Bm = [70., 70., 70.]
        self.Vc = [60.0, 60.0, 60.0]
        self.Ic = [1200., 1200., 1200.]
        self.Im = [1400., 1400., 1400.]

        t0 = time()  # [TIMING]

        # Calculating values (~5 us)
        bc, br, bm = self.Bc, self.Br, self.Bm
        vc, ic, im = self.Vc, self.Ic, self.Im
        Bc = [bc[0], bc[1], bc[2],
              (bc[0]**2 + bc[1]**2 + bc[2]**2)**(1/2)]
        Br = [br[0], br[1], br[2],
              (br[0]**2 + br[1]**2 + br[2]**2)**(1/2)]
        Bm = [bm[0], bm[1], bm[2],
              (bm[0]**2 + bm[1]**2 + bm[2]**2)**(1/2)]

        Bo = [Bc[0]-Br[0], Bc[1]-Br[1], Bc[2]-Br[2],
              ((Bc[0]-Br[0])**2 + (Bc[1]-Br[1])**2 + (Bc[2]-Br[2])**2)**(1/2)]
        Bd = [Bo[0]-Bm[0], Bo[1]-Bm[1], Bo[2]-Bm[2],
              ((Bo[0]-Bm[0])**2 + (Bo[1]-Bm[1])**2 + (Bo[2]-Bm[2])**2)**(1/2)]

        Vc = [vc[0], vc[1], vc[2], 0]
        Ic = [ic[0], ic[1], ic[2], 0]
        Im = [im[0], im[1], im[2], 0]
        Id = [Ic[0]-Im[0], Ic[1]-Im[1], Ic[2]-Im[2], 0]

        t1 = time()  # [TIMING]

        # Mapping values to labels:
        for i, p in enumerate((Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id)):
            for j in range(4):
                if i >= 5 and j == 3:
                    # skip summed entries for voltage and current
                    pass
                else:
                    self.biv_labels[i][j].setText("{:.3f}".format(p[j]))

        t2 = time() # [TIMING]
        print("update_biv_labels calc:", round((t1-t0)*1E6), "us")  # [TIMING]
        print("update_biv_labels updt:", round((t2-t1)*1E6), "us")  # [TIMING]


