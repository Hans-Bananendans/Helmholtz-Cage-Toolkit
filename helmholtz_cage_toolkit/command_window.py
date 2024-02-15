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
from copy import deepcopy
from time import time, sleep

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.datapool import DataPool
from helmholtz_cage_toolkit.hhcplot import HHCPlot, HHCPlotArrow
from helmholtz_cage_toolkit.utilities import IGRF_from_UNIX
from helmholtz_cage_toolkit.envelope_plot import EnvelopePlot
import helmholtz_cage_toolkit.client_functions as cf

class CommandWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool

        self.datapool.command_window = self



        # ==== TIMERS
        self.timer_HHCPlot_refresh = QTimer()
        self.timer_HHCPlot_refresh.timeout.connect(self.do_refresh_HHCPlots)

        self.timer_values_refresh = QTimer()
        self.timer_values_refresh.timeout.connect(self.do_refresh_values)

        self.timer_playback_tracker = QTimer()
        self.timer_playback_tracker.timeout.connect(self.do_playback_tracking)

        self.t_playstart = 0.

        # ==== LEFT LAYOUT
        layout_left = QVBoxLayout()

        self.group_mode_controls = self.make_group_mode_controls()
        self.group_offset_controls = self.make_group_offset_controls()
        self.group_record_controls = self.make_group_record_controls()
        self.group_play_controls = self.make_group_play_controls()

        for groupbox in (self.group_mode_controls, self.group_offset_controls,
                         self.group_record_controls, self.group_play_controls):
            groupbox.setStyleSheet(
                self.datapool.config["stylesheet_groupbox_smallmargins"]
            )
            layout_left.addWidget(groupbox)


        # ==== RIGHT LAYOUT
        layout_right = QVBoxLayout()

        self.stacker_right = QStackedWidget()
        # self.stacker_right.setSizePolicy(
        #     QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.stacker_right.setMaximumHeight(356)

        label_disconnected = QLabel("\n\nNO CONNECTION TO DEVICE...\n\n")
        label_disconnected.setStyleSheet("""QLabel {font-size: 24px;}""")
        label_disconnected.setAlignment(Qt.AlignCenter)
        layout_label_disconnected = QVBoxLayout()
        layout_label_disconnected.addWidget(label_disconnected)
        group_label_disconnected = QGroupBox()
        group_label_disconnected.setLayout(layout_label_disconnected)
        self.stacker_right.addWidget(group_label_disconnected)    # INDEX 0

        # Construct Manual Input groupbox
        self.group_manual_input = GroupManualInput(self.datapool)
        # Update the labels once to flush init values
        self.group_manual_input.do_update_biv_labels()
        # Add to stacked widget
        self.stacker_right.addWidget(self.group_manual_input)   # INDEX 1

        # Add envelope plot to stacker widget
        dummy_widget = QLabel("DUMMY ENVELOPE PLOT")
        self.envelope_plot = EnvelopePlot(datapool)
        self.stacker_right.addWidget(self.envelope_plot)   # INDEX 2

        # Add stacker to the parent layout
        layout_right.addWidget(self.stacker_right)


        # Construct large Bm number display bar layout
        layout_bm_display = self.make_layout_bm_display()
        # Update once to flush init values
        self.do_update_bm_display()

        # Add to parent layout
        layout_right.addLayout(layout_bm_display)


        # Create a grid layout for the HHCPlots
        self.layout_hhcplots = QGridLayout()

        # Constructing two instances of HHCPlots. First look in config to see
        # if arrow tips should be plotted (disabled gives better performance)
        et = self.datapool.config["enable_arrow_tips"]

        # Create four instances of HHCPlotArrow to give to the constructor of
        # HHCPlot. The order of the array arrows_yz will also dictate in which
        # order the arrows will be plotted and referenced once connected to a
        # HHCPlot instance.
        arrows_yz = []
        for item in ("Bm", "Bc", "Br", "Bo"):
            arrows_yz.append(HHCPlotArrow(
                color=self.datapool.config[f"plotcolor_{item}"], enable_tip=et,
            ))

        # Construct HHCPlot instance for YZ plot
        self.hhcplot_yz = HHCPlot( datapool, arrows_yz, direction="YZ")

        # Same idea but now for -XY plot
        arrows_xy = []
        for item in ("Bm", "Bc", "Br", "Bo"):
            arrows_xy.append(HHCPlotArrow(
                color=self.datapool.config[f"plotcolor_{item}"], enable_tip=et,
            ))
        self.hhcplot_xy = HHCPlot(datapool, arrows_xy, direction="mXY")


        print("hhcplot_yz instance: ", self.hhcplot_yz)
        for i, arrow in enumerate(self.hhcplot_yz.arrows):
            print(f"arrow_yz_{i}: {arrow}")

        print("hhcplot_xy instance: ", self.hhcplot_xy)
        for i, arrow in enumerate(self.hhcplot_xy.arrows):
            print(f"arrow_xy_{i}: {arrow}")




        self.layout_hhcplots.addWidget(self.hhcplot_yz, 0, 0)
        self.layout_hhcplots.addWidget(self.hhcplot_xy, 0, 1)

        # self.layout_hhcplots.sizeHint(QSize(720, 360))
        # Add to parent layout
        layout_right.addLayout(self.layout_hhcplots)

        # Debug operations # TODO CLEAN UP
        breset = [[0., ]*3, ]*4

        self.hhcplot_yz.update_arrows(breset)
        self.hhcplot_xy.update_arrows(breset)

        # btests = [[[10_000, 90_000, 10_000, ], [-10_000, -90_000, -10_000, ], ],
        #           [[20_000, 80_000, 20_000, ], [-20_000, -80_000, -20_000, ], ],
        #           [[30_000, 70_000, 30_000, ], [-30_000, -70_000, -30_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [-40_000, -60_000, -40_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [     0.,      0.,      0., ], ],
        #           [[40_000, 60_000, 40_000, ], [     0.,      0.,      0., ], ],
        #           [[40_000, 60_000, 40_000, ], [     0.,      0.,      0., ], ], ]

        # btests = [[[10_000, 90_000, 10_000, ], [10_000, 90_000, 10_000, ], ],
        #           [[20_000, 80_000, 20_000, ], [20_000, 80_000, 20_000, ], ],
        #           [[30_000, 70_000, 30_000, ], [30_000, 70_000, 30_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [40_000, 60_000, 40_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [40_000, 60_000, 40_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [40_000, 60_000, 40_000, ], ],
        #           [[40_000, 60_000, 40_000, ], [40_000, 60_000, 40_000, ], ], ]

        # for btest in btests:
        #     self.hhcplot_yz.update_arrows_unoptimized(btest)
        #     self.hhcplot_xy.update_arrows_unoptimized(btest)
        #
        # breset = [[0., ]*3, ]*2
        #
        # self.hhcplot_yz.update_arrows(breset)
        # self.hhcplot_xy.update_arrows(breset)

        # for btest in btests:
        #     self.hhcplot_yz.update_arrows(btest)
        #     self.hhcplot_xy.update_arrows(btest)
        #
        #
        # schedtest = [[0, 1, 2, 3, 4, ],
        #              [5, 5, 5, 5, 5, ],
        #              [0., 1., 2., 3., 4., ],
        #              [50_000,  50_000, -50_000, -50_000,      0.],
        #              [50_000, -50_000, -50_000,  50_000,      0.],
        #              [     0, -10_000, -20_000, -30_000, -40_000], ]
        #
        #
        # self.hhcplot_yz.plot_ghosts(schedtest)
        # self.hhcplot_xy.plot_ghosts(schedtest)


        # ==== Bottom layout
        layout0 = QHBoxLayout()
        layout0.addLayout(layout_left)
        layout0.addLayout(layout_right)

        self.setLayout(layout0)

        self.groups_to_enable_on_connect = (
            self.group_mode_controls,
            self.group_offset_controls,
            self.group_record_controls,
            self.group_play_controls,
            self.group_manual_input
        )

        # Set disabled until connected
        self.do_on_disconnected()

        self.do_select_mode("manual")  # Default start in manual mode




    def make_group_mode_controls(self):
        layout_mode_controls = QGridLayout()

        self.button_total_reset = QPushButton(
            # QIcon("./assets/icons/feather/x-octagon.svg"), "RESET")
            QIcon("./assets/icons/feather/x-circle.svg"), "TOTAL RESET")
        self.button_total_reset.setIconSize(QSize(24, 24))
        self.button_total_reset.setStyleSheet("""
        QPushButton {font-size: 24px;}
        """)
        self.button_total_reset.clicked.connect(self.do_total_reset)

        self.button_set_manual_mode = QPushButton(
            QIcon("./assets/icons/feather/edit-3.svg"), "Manual")
        self.button_set_manual_mode.clicked.connect(
            lambda: self.do_select_mode("manual")
        )

        self.button_set_play_mode = QPushButton(
            QIcon("./assets/icons/feather/film.svg"), "Schedule")
        self.button_set_play_mode.clicked.connect(
            lambda: self.do_select_mode("play")
        )

        layout_mode_controls.addWidget(self.button_total_reset, 0, 0, 1, 2)
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

        self.button_submit_br = QPushButton("Submit")
        self.button_submit_br.clicked.connect(self.do_submit_Br)
        layout_offset_buttons.addWidget(self.button_submit_br)

        self.button_reset_br = QPushButton("Reset")
        self.button_reset_br.clicked.connect(self.do_reset_Br)
        layout_offset_buttons.addWidget(self.button_reset_br)

        self.button_br_from_local_emf = QPushButton("Local EMF")
        self.button_br_from_local_emf.clicked.connect(self.do_br_from_local_emf)
        layout_offset_buttons.addWidget(self.button_br_from_local_emf)

        # Generate local_emf value based on config data
        if self.datapool.config["local_EMF"] is None:
            try:
                self.local_emf = IGRF_from_UNIX(
                    self.datapool.config["local_latitude"],
                    self.datapool.config["local_longitude"],
                    self.datapool.config["local_altitude"]/1000,   # m to km
                    time(),
                    rotation_matrix=self.datapool.config["R_ENU_cageframe"]
                )
            except: # noqa TODO Improve exception handling
                self.button_br_from_local_emf.setEnabled(False)
                self.button_br_from_local_emf.setText("UNAVAILABLE")
                print("[WARNING] Local EMF could not be calculated. Button 'Br from local EMF' disabled")
        else:
            if len(self.datapool.config["local_EMF"]) != 3:
                self.button_br_from_local_emf.setEnabled(False)
                self.button_br_from_local_emf.setText("UNAVAILABLE")
                print("[WARNING] Local EMF could not be calculated. Button 'Br from local EMF' disabled")
            else:
                self.local_emf(self.datapool.config["local_EMF"])

        self.button_br_from_bm = QPushButton(QIcon(
            "./assets/icons/feather/corner-left-up.svg"), "Current B_M")
        self.button_br_from_bm.clicked.connect(self.do_Br_from_Bm)
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

        self.checks_icon_paths = (
            "./assets/icons/check_00aa00.svg",
            "./assets/icons/wave_ffd200.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
            "./assets/icons/x_bb0000.svg",
        )


        self.stacker_play_controls = QStackedWidget()

        self.layout_play_checks = QGridLayout()

        # It's tricky to manipulate widgets by referring to them in their
        # layout, as this returns QWidgetItems, rather than the actual widget
        # instance. So instead, gather widgets in a nested list stored in the
        # class instance, for easier reference.
        self.checks_widgets = []

        for i in range(len(self.datapool.checks)):
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

        # Then propagate it again according to values in self.datapool.checks:
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

    def make_layout_bm_display(self):

        layout_bm_display = QGridLayout()
        layout_bm_display.setHorizontalSpacing(0)

        label_bm_header = QLabel("Bm\n\u03bcT")
        label_bm_header.setStyleSheet(self.datapool.config["stylesheet_label_bmheader_small"])
        label_bm_header.setMaximumWidth(32)
        layout_bm_display.addWidget(label_bm_header, 0, 0)

        label_bmx_large = QLabel("-9999")
        label_bmx_large.setStyleSheet(self.datapool.config["stylesheet_label_bmx_large"])
        # label_bmx_large.setAlignment(Qt.AlignRight)

        label_bmx_small = QLabel(".999")
        label_bmx_small.setStyleSheet(self.datapool.config["stylesheet_label_bmx_small"])
        label_bmx_small.setAlignment(Qt.AlignLeft)

        label_bmy_large = QLabel("-9999")
        label_bmy_large.setStyleSheet(self.datapool.config["stylesheet_label_bmy_large"])
        # label_bmy_large.setAlignment(Qt.AlignRight)

        label_bmy_small = QLabel(".999")
        label_bmy_small.setStyleSheet(self.datapool.config["stylesheet_label_bmy_small"])
        # label_bmy_small.setAlignment(Qt.AlignLeft)

        label_bmz_large = QLabel("-9999")
        label_bmz_large.setStyleSheet(self.datapool.config["stylesheet_label_bmz_large"])
        # label_bmz_large.setAlignment(Qt.AlignRight)

        label_bmz_small = QLabel(".999")
        label_bmz_small.setStyleSheet(self.datapool.config["stylesheet_label_bmz_small"])
        # label_bmz_small.setAlignment(Qt.AlignLeft)

        label_bm_large = QLabel("-9999")
        label_bm_large.setStyleSheet(self.datapool.config["stylesheet_label_bm_large"])
        # label_bm_large.setAlignment(Qt.AlignRight)

        label_bm_small = QLabel(".999")
        label_bm_small.setStyleSheet(self.datapool.config["stylesheet_label_bm_small"])
        # label_bm_small.setAlignment(Qt.AlignLeft)

        self.labels_bm_display = []

        for i, label in enumerate((label_bmx_large, label_bmx_small,
                                   label_bmy_large, label_bmy_small,
                                   label_bmz_large, label_bmz_small,
                                   label_bm_large, label_bm_small,)):

            if divmod(i, 2)[1] == 1:
                label.setAlignment(Qt.AlignLeft)
                label.setMaximumWidth(48)
            else:
                label.setAlignment(Qt.AlignRight)
                label.setMinimumWidth(108)

            self.labels_bm_display.append(label)

            layout_bm_display.addWidget(label, 0, i+1)

        return layout_bm_display

    def do_refresh_HHCPlots(self):
        Bm = self.datapool.Bm
        Bc = self.datapool.Bc
        Br = self.datapool.Br
        Bo = [Bc[0]-Br[0], Bc[1]-Br[1], Bc[2]-Br[2]]

        self.hhcplot_xy.update_arrows([Bm, Bc, Br, Bo])
        self.hhcplot_yz.update_arrows([Bm, Bc, Br, Bo])


    def do_refresh_values(self):
        self.do_update_bm_display()
        self.group_manual_input.do_update_biv_labels()


    def on_schedule_refresh(self):
        # XYZ lines in envelope plot
        for item in self.envelope_plot.plot_obj.dataItems:
            item.clear()

        # Ghosts in HHC plots:
        for item in [self.hhcplot_yz.plot_obj.dataItems[-1],
                     self.hhcplot_xy.plot_obj.dataItems[-1]]:
            item.clear()

        # Refresh envelope plot
        self.envelope_plot.generate_envelope_plot()

        # Refresh path ghosts on HHC plots
        self.hhcplot_yz.plot_ghosts(self.datapool.schedule)
        self.hhcplot_xy.plot_ghosts(self.datapool.schedule)

    def do_update_bm_display(self):
        # Bm = [-12345.678, -1.0, -98.765]  TODO REMOVE
        Bm = self.datapool.Bm
        Bm = [Bm[0]/1000, Bm[1]/1000, Bm[2]/1000]  # Convert to uT

        Bm_abs = (Bm[0]**2 + Bm[1]**2 + Bm[2]**2)**(1/2)

        for i, bval in enumerate((Bm[0], Bm[1], Bm[2], Bm_abs)):
            # Pretty quick way (1.3 us per set) to convert a float into two
            # string segments, one with up to 5 characters above the decimal
            # separator, and the other part with the decimal separator and up
            # to three decimal values. It
            left_text, right_text = str(float(bval)).split(".")
            self.labels_bm_display[2*i].setText(left_text[-6:])
            self.labels_bm_display[2*i+1].setText(("."+right_text+"000")[:4])

    def do_update_check_widgets(self):
        i = 0
        for key, check_item in self.datapool.checks.items():
            # Update "icon" QSvgWidget:
            self.checks_widgets[i][0].load(
                self.checks_icon_paths[check_item["value"]])

            # Update QLabel:
            self.checks_widgets[i][1].setText(
                check_item["text"][check_item["value"]])
            if check_item["value"] != 0 and not self.checks_widgets[i][1].isEnabled():
                self.checks_widgets[i][1].setEnabled(True)
            elif check_item["value"] == 0 and self.checks_widgets[i][1].isEnabled():
                self.checks_widgets[i][1].setEnabled(False)

            i += 1

    def do_update_play_stats_labels(self):
        # TODO: Implement properly
        self.label_play_status.setText("0.0")
        self.label_play_name.setText("0.0")
        self.label_play_step.setText("0.0")
        self.label_play_time.setText("0.0")

    def do_total_reset(self):
        # Order of business:
        # 1. Switch to manual mode (-> call self.do_select_mode("manual", skip_confirm=True)
        self.do_select_mode("manual", skip_confirm=True)

        # 2. Set Br to 0 by calling self.reset_Br()
        self.do_reset_Br()

        # 3. Command Bc to 0 by calling self.datapool.do_set_Bc([0., 0., 0.])
        self.datapool.do_set_Bc([0., 0., 0.])

        # 4. Update fields in manual_input to reflect 0. 0. 0.
        for le in self.group_manual_input.le_inputs:
            le.setText("0.0")

        # 5. Feedback to terminal
        print("TOTAL RESET executed successfully.")


    def do_submit_Br(self):
        print("[DEBUG] do_submit_Br()")
        Br = [0., 0., 0.]
        for i, le in enumerate((self.le_brx, self.le_bry, self.le_brz)):
            Br[i] = 1000*float(le.text())
        self.datapool.do_set_Br(Br)


    def do_reset_Br(self):
        print("[DEBUG] do_reset_Br()")
        self.datapool.do_set_Br([0., 0., 0.])
        for le in (self.le_brx, self.le_bry, self.le_brz):
            le.setText("0.0")


    def do_br_from_local_emf(self):
        print("[DEBUG] do_br_from_local_emf()")
        self.datapool.do_set_Br(self.local_emf)
        for i, le in enumerate((self.le_brx, self.le_bry, self.le_brz)):
            le.setText(str(round(self.local_emf[i]/1000, 3)))

    def do_Br_from_Bm(self):
        print("[DEBUG] do_Br_from_Bm()")
        Bm = self.datapool.Bm
        self.datapool.do_set_Br(Bm)
        for i, le in enumerate((self.le_brx, self.le_bry, self.le_brz)):
            le.setText(str(round(Bm[i]/1000, 3)))


    def run_checks(self):
        # TODO: Check conditions and set values of self.checks as
        #  appropriate, then run do_update_check_widgets
        print("[DEBUG] run_checks()")


    def do_select_mode(self, mode, skip_confirm=False):
        if mode == "play" and self.datapool.socket_connected:
            cf.activate_play_mode(self.datapool.socket, self.datapool.ds)
            self.datapool.command_mode = "play"
            self.button_set_play_mode.setEnabled(False)
            self.button_set_manual_mode.setEnabled(True)

            self.stacker_right.setCurrentIndex(2)

        elif mode == "manual" and self.datapool.socket_connected:
            # TODO: IF PLAYING, THEN STOP BEFORE SETTING MAYBE WITH CONFIRMATION POPUP

            cf.deactivate_play_mode(self.datapool.socket, self.datapool.ds)
            self.datapool.command_mode = "manual"
            self.button_set_play_mode.setEnabled(True)
            self.button_set_manual_mode.setEnabled(False)

            self.stacker_right.setCurrentIndex(1)

        # Contingency for correct mode but no connection: just skip
        elif mode in ("manual", "play") and not self.datapool.socket_connected:
            pass

        else:
            raise AssertionError(f"Given invalid mode '{mode}'!")


    # def do_activate_play_mode(self):
    #     print("[DEBUG] do_activate_play_mode()")
    #     if self.datapool.socket_connected:
    #         cf.activate_play_mode(self.datapool.socket, self.datapool.ds)
    #         self.datapool.command_mode = "play"
    #
    #
    # def do_activate_manual_mode(self):
    #     print("[DEBUG] do_activate_manual_mode()")
    #     if self.datapool.socket_connected:
    #         cf.deactivate_play_mode(self.datapool.socket, self.datapool.ds)
    #         self.datapool.command_mode = "manual"


    def do_on_connected(self):
        print("[DEBUG] do_on_connected()")

        for group in self.groups_to_enable_on_connect:
            group.setEnabled(True)

        self.timer_values_refresh.start(
            int(1000/self.datapool.config["CW_values_refresh_rate"])
        )
        self.timer_HHCPlot_refresh.start(
            int(1000/self.datapool.config["CW_HHCPlots_refresh_rate"])
        )

        self.do_select_mode("manual")

    def do_on_disconnected(self):
        print("[DEBUG] do_on_disconnected()")

        self.timer_values_refresh.stop()
        self.timer_HHCPlot_refresh.stop()

        self.stacker_right.setCurrentIndex(0)

        for group in self.groups_to_enable_on_connect:
            group.setEnabled(False)

    def do_set_target(self):
        # TODO IMPLEMENT
        print("[DEBUG] do_set_target()")

    def do_start_playback(self):
        # TODO IMPLEMENT
        print("[DEBUG] start_playback()")

        if self.button_start_playback.isChecked():
            print("PLAYBACK START")

            # DO A TIME SYNC WITH SERVER

            # IF ARMED, START RECORDING

            # Send START playback command to server
            self.datapool.do_start_playback()

            self.button_start_playback.setIcon(
                QIcon("./assets/icons/feather/square.svg"))
            self.button_start_playback.setText("STOP")

            # SWAP TO PLAYBACK WINDOW:
            self.stacker_play_controls.setCurrentIndex(1)

            # START TIMER POLLING FOR SCHEDULE DATA AND UPDATING
            self.timer_playback_tracker.start(
                self.datapool.config["tracking_timer_period"]
            )

        # STOP
        else:
            # Send STOP playback command to server
            print("PLAYBACK STOP")
            self.datapool.do_stop_playback()
            self.timer_playback_tracker.stop()

            self.do_post_playback()


    def do_post_playback(self):
        # TODO ANY EXTRA POST-PLAYBACK FUNCTIONS GO HERE
        # Swap to checks window:
        self.stacker_play_controls.setCurrentIndex(0)

        self.button_start_playback.setEnabled(False)
        self.button_start_playback.setIcon(
            QIcon("./assets/icons/feather/refresh-ccw.svg"))
        self.button_start_playback.setText("RESETTING...")

        self.timer_playback_tracker.stop()
        self.envelope_plot.vline.setPos(0.0)

        # DUMMY TIMER
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.do_enable_start_button)
        self.reset_timer.start(2000)




    def do_playback_tracking(self):
        # if self.datapool.server_play_status or whatever is "playing" or whatever
        self.envelope_plot.vline.setPos(time()-self.datapool.t_playstart)



    def do_enable_start_button(self):
        self.button_start_playback.setEnabled(True)
        self.button_start_playback.setIcon(
            QIcon("./assets/icons/feather/play.svg"))
        self.button_start_playback.setText("PLAY")



# class HHCPlotCommandWindow(HHCPlot):
#     def __init__(self, datapool, **kwargs):
#         super().__init__(datapool, **kwargs)
#
#     def create_arrows(self):
#         arrows = []
#
#         arrow_Bm = HHCPlotArrow(color=self.datapool.config["plotcolor_Bm"],
#                                 enable_tip=True)
#         arrows.append(arrow_Bm)
#
#         arrow_Bc = HHCPlotArrow(color=self.datapool.config["plotcolor_Bc"],
#                                 enable_tip=True)
#         arrows.append(arrow_Bc)
#
#         arrow_Br = HHCPlotArrow(color=self.datapool.config["plotcolor_Br"],
#                                 enable_tip=True)
#         arrows.append(arrow_Br)
#
#         arrow_Bo = HHCPlotArrow(color=self.datapool.config["plotcolor_Bo"],
#                                 enable_tip=True)
#         arrows.append(arrow_Bo)
#
#         return arrows



class GroupManualInput(QGroupBox):
    def __init__(self, datapool):
        super().__init__("Manual input")

        self.datapool = datapool

        self.setStyleSheet(self.datapool.config["stylesheet_groupbox_smallmargins"])
        self.setMaximumHeight(220)


        layout0 = QGridLayout()
        layout0.setHorizontalSpacing(8)
        layout0.setSizeConstraint(QLayout.SetMinimumSize)

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
        self.combo_input.addItems(["Bc [\u03bcT]", "Bc [nT]"])

        self.le_inputs = [QLineEdit("0.0"), QLineEdit("0.0"), QLineEdit("0.0")]
        for i, le in enumerate(self.le_inputs):
            le.setMaxLength(9)
            le.setPlaceholderText(("x value", "y value", "z value")[i])
            le.setAlignment(Qt.AlignCenter)

        self.button_submit_Bc = QPushButton("Submit")
        self.button_submit_Bc.clicked.connect(self.do_submit_Bc)

        # ==== Putting widgets into layout

        # Input column:
        layout0.addWidget(self.combo_input, 0, 0)
        for j in range(3):
            layout0.addWidget(self.le_inputs[j], j+1, 0)
        layout0.addWidget(self.button_submit_Bc, 4, 0)

        # Header labels
        for i in range(9):
            layout0.addWidget(header_labels[i], 0, i+1)
        # Value labels
        for i in range(9):
            for j in range(4):
                layout0.addWidget(self.biv_labels[i][j], j+1, i+1)

        self.setLayout(layout0)

    def do_submit_Bc(self):
        Bc = [0.]*3

        print("[DEBUG] do_submit_Bc(): combo_input index:", self.combo_input.currentIndex())


        if self.combo_input.currentIndex() == 0:  # Case: unit is uT
            print("[DEBUG] do_submit_Bc(): detected unit: \u03bcT")
            for i in range(3):
                Bc[i] = 1000*float(self.le_inputs[i].text())
        elif self.combo_input.currentIndex() == 1:  # Case: unit is nT
            print("[DEBUG] do_submit_Bc(): detected unit: nT")
            for i in range(3):
                Bc[i] = float(self.le_inputs[i].text())

        print("[DEBUG] do_submit_Bc(): Bc =", Bc)

        self.datapool.do_set_Bc(Bc)



    def do_update_biv_labels(self):
        # print("[DEBUG] GroupManualInput.do_update_biv_labels()")
        # Mapping biv_labels: Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id
        # Bo = Bc-Br
        # Bd = Bo-Bm
        # Id = Ic-Im

        # # DUMMIES
        # self.Bc = [50., 50., 50.]
        # self.Br = [-5., 2.5, -45.]
        # self.Bm = [70., 70., 70.]
        # self.Vc = [60.0, 60.0, 60.0]
        # self.Ic = [1200., 1200., 1200.]
        # self.Im = [1400., 1400., 1400.]

        # t0 = time()  # [TIMING]

        # Calculating values (~5 us)
        vc, ic, im = self.datapool.Vc, self.datapool.Ic, self.datapool.Im
        bc, br, bm = self.datapool.Bc, self.datapool.Br, self.datapool.Bm

        # # Convert from nT to uT:  SLOWER
        # for b in (bc, br, bm):
        #     b = [b[0]/1000, b[1]/1000, b[2]/1000]
        #
        # Bc = [bc[0], bc[1], bc[2],
        #       (bc[0]**2 + bc[1]**2 + bc[2]**2)**(1/2)]
        # Br = [br[0], br[1], br[2],
        #       (br[0]**2 + br[1]**2 + br[2]**2)**(1/2)]
        # Bm = [bm[0], bm[1], bm[2],
        #       (bm[0]**2 + bm[1]**2 + bm[2]**2)**(1/2)]

        # Convert from nT to uT and calculate vector magnitudes
        Bc = [bc[0]/1000, bc[1]/1000, bc[2]/1000,
              (bc[0]**2 + bc[1]**2 + bc[2]**2)**(1/2)/1000]
        Br = [br[0]/1000, br[1]/1000, br[2]/1000,
              (br[0]**2 + br[1]**2 + br[2]**2)**(1/2)/1000]
        Bm = [bm[0]/1000, bm[1]/1000, bm[2]/1000,
              (bm[0]**2 + bm[1]**2 + bm[2]**2)**(1/2)/1000]

        Bo = [Bc[0]-Br[0], Bc[1]-Br[1], Bc[2]-Br[2],
              ((Bc[0]-Br[0])**2 + (Bc[1]-Br[1])**2 + (Bc[2]-Br[2])**2)**(1/2)]
        Bd = [Bo[0]-Bm[0], Bo[1]-Bm[1], Bo[2]-Bm[2],
              ((Bo[0]-Bm[0])**2 + (Bo[1]-Bm[1])**2 + (Bo[2]-Bm[2])**2)**(1/2)]

        Vc = [vc[0], vc[1], vc[2], 0]
        Ic = [ic[0], ic[1], ic[2], 0]
        Im = [im[0], im[1], im[2], 0]
        Id = [Ic[0]-Im[0], Ic[1]-Im[1], Ic[2]-Im[2], 0]

        # t1 = time()  # [TIMING]

        # Mapping values to labels:
        for i, p in enumerate((Bc, Br, Bo, Bm, Bd, Vc, Ic, Im, Id)):
            for j in range(4):
                if i >= 5 and j == 3:
                    # skip summed entries for voltage and current
                    pass
                else:
                    self.biv_labels[i][j].setText("{:.3f}".format(p[j]))

        # t2 = time() # [TIMING]
        # print("update_biv_labels calc:", round((t1-t0)*1E6), "us")  # [TIMING]
        # print("update_biv_labels updt:", round((t2-t1)*1E6), "us")  # [TIMING]


