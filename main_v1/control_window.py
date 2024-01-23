from PyQt5.QtCore import QDir, QSize, Qt, QRunnable, QThreadPool, QTimer, QRectF, QLineF
from PyQt5.QtGui import (
    # QAction,
    # QActionGroup,
    QFont,
    QIcon,
    QImage,
    QKeySequence,
    QPixmap,
    QPalette,
    QColor,
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFileDialog,
    QGraphicsView,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
# from dummy_functions import (
#     # TF_B_Ic,
#     # TF_Ic_Vc,
#     # b_read,
# )

from control_functions import (
    setup_interface_board,
    setup_supplies,
    setup_magnetometer,
    # adc_read,
)

from datapool import DataPool

import os
import time
import pyqtgraph as pg
import numpy as np


class ControlWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.data = datapool  # TODO: self.data -> self.datapool

        layout0 = QGridLayout()
        
        # Connect hardware
        self.data.interface_board = setup_interface_board(config)
        self.data.supplies = setup_supplies(config, self.data.interface_board)
        self.data.magnetometer = setup_magnetometer(config, self.data.interface_board)
        
        self.data.log(4, "ControlWindow - Setting up hardware...")
        self.data.log(4, f"interface_board: {self.data.interface_board}")
        self.data.log(4, f"supply1: {self.data.supplies[0]}")
        self.data.log(4, f"supply2: {self.data.supplies[1]}")
        self.data.log(4, f"supply3: {self.data.supplies[2]}")
        self.data.log(4, f"magnetometer: {self.data.magnetometer}")
        self.data.log(4, "")
    
        # Generate groups
        # Note: these subwindows access config indirectly through the datapool
        group_control_input = GroupControlInput(self.data)
        group_control_scheduler = GroupControlScheduler(self.data)
        group_field_readout = GroupFieldReadout(self.data)
        group_2d_plot = Group2dPlot(self.data)

        # Consolidate la(yout
        layout_left = QVBoxLayout()
        layout_left.addWidget(group_control_input)
        layout_left.addWidget(group_control_scheduler)

        layout_right = QVBoxLayout()
        layout_right.addWidget(group_field_readout)
        layout_right.addWidget(group_2d_plot)

        layout0.addLayout(layout_left, 0, 0)
        layout0.addLayout(layout_right, 0, 1)
        self.setLayout(layout0)
    

    # def log(self, verbosity_level, string):
    #     """Prints string to console when verbosity is above a certain level"""
    #     if verbosity_level <= self.data.config["verbosity"]:
    #         print(string)
    



class GroupControlInput(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Control Input")

        # self.setMinimumSize(QSize(480, 360))
        
        self.data = datapool

        layout0 = QGridLayout()

        # Populate control grid
        text = [
            ["Bx: ", "By: ", "Bz: "],
            ["Bxc: ", "Byc: ", "Bzc: "],
            ["Ix: ", "Iy: ", "Iz: "],
            ["Vccx: ", "Vccy: ", "Vccz: "]]

        input_bx = QLineEdit("0.0")
        input_by = QLineEdit("0.0")
        input_bz = QLineEdit("0.0")
        for input_b in (input_bx, input_by, input_bz):
            input_b.setMaxLength(8)
        self.input_b = [input_bx, input_by, input_bz]

        # [bxc, byc, bzc] = [0.0, 0.0, 0.0]; self.bc = [bxc, byc, bzc]
        # [ix, iy, iz] = [0.0, 0.0, 0.0]; self.ixyz = [ix, iy, iz]
        # [vccx, vccy, vccz] = [0.0, 0.0, 0.0]; self.vcc = [vccx, vccy, vccz]

        self.blabel = [QLabel(), QLabel(), QLabel()]
        self.ilabel = [QLabel(), QLabel(), QLabel()]
        self.vlabel = [QLabel(), QLabel(), QLabel()]

        for i in range(3):
            layout0.addWidget(QLabel(text[0][i]), i + 1, 1)
            layout0.addWidget(self.input_b[i], i + 1, 2)
            layout0.addWidget(QLabel(" uT"), i + 1, 3)

            layout0.addWidget(QLabel(text[1][i]), i + 1, 5)
            layout0.addWidget(self.blabel[i], i + 1, 6)
            layout0.addWidget(QLabel(" uT"), i + 1, 7)

            layout0.addWidget(QLabel(text[2][i]), i + 1, 9)
            layout0.addWidget(self.ilabel[i], i + 1, 10)
            layout0.addWidget(QLabel(" A"), i + 1, 11)

            layout0.addWidget(QLabel(text[3][i]), i + 1, 13)
            layout0.addWidget(self.vlabel[i], i + 1, 14)
            layout0.addWidget(QLabel(" V"), i + 1, 15)

        self.redraw_values()

        self.button_submit = QPushButton("Submit",)
        self.button_submit.clicked.connect(self.submit)
        layout0.addWidget(self.button_submit, 5, 2)

        self.button_panic_reset = QPushButton("PANIC RESET!",)
        self.button_panic_reset.clicked.connect(self.panic_reset)
        layout0.addWidget(self.button_panic_reset, 6, 2)


        for i, j in enumerate([0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]):
            layout0.setColumnStretch(i, j)  # Ensure correct horizontal alignment
        for i, j in enumerate([0, 0, 0, 0, 1, 0, 2]):
            layout0.setRowStretch(i, j)  # Ensure correct vertical alignment

        self.setLayout(layout0)

    def redraw_values(self):
        self.data.log(4, "Redrawing values...")
        for i in range(3):
            self.blabel[i].setText(str(round(self.data.B_c[i], 3)))
            self.ilabel[i].setText(str(round(self.data.I_c[i], 3)))
            self.vlabel[i].setText(str(round(self.data.V_cc[i], 3)))

    # @Slot()
    def submit(self):
        axis = ("X", "Y", "Z")
        for i in range(3):
            self.data.B_c[i] = float(self.input_b[i].text())
            self.data.I_c[i] = TF_B_Ic(self.data.B_c[i], axis=axis[i])
            self.data.V_cc[i] = TF_Ic_Vc(self.data.I_c[i])

        self.data.log(4, "B_c:  {self.data.B_c}")
        self.data.log(4, "I_c:  {self.data.I_c}")
        self.data.log(4, "V_cc: {self.data.V_cc}")

        self.data.supplies[0].set_current_out(self.data.I_c[0])

        self.redraw_values()
    
    def panic_reset(self):
        axis = ("X", "Y", "Z")
        for i in range(3):
            self.data.B_c[i] = 0.0
            self.data.I_c[i] = TF_B_Ic(self.data.B_c[i], axis=axis[i])
            self.data.V_cc[i] = TF_Ic_Vc(self.data.I_c[i])

        self.data.log(1, "PANIC RESET")
        self.data.log(4, "B_c:  {self.data.B_c}")
        self.data.log(4, "I_c:  {self.data.I_c}")
        self.data.log(4, "V_cc: {self.data.V_cc}")

        self.data.supplies[0].set_zero_output()
        self.data.supplies[1].set_zero_output()
        self.data.supplies[2].set_zero_output()

        self.redraw_values()


# class ADC_worker(QRunnable):
#     def __init__(self, f):


class Worker(QRunnable):
    # @Slot()  # TODO: REMOVE
    def run(self, n_seconds=15):
        print("Counting down from", n_seconds)
        time.sleep(n_seconds)
        print("Countdown complete")


class GroupControlScheduler(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Scheduler")

        self.data = datapool

        self.setCheckable(True)
        self.setChecked(False)
        self.setMinimumSize(QSize(540, 360))

        self.schedule_filepath = ""
        self.schedule_filename = ""
        self.schedule_content = None

        layout0 = QGridLayout()

        # ==== File loading
        self.button_load = QPushButton("...")
        self.button_load.clicked.connect(self.load_schedule)

        self.load_textbox = QLineEdit()
        self.load_textbox.setReadOnly(True)
        self.load_textbox.setPlaceholderText("<empty>")

        layout_load = QHBoxLayout()
        layout_load.addWidget(QLabel("Schedule: "))
        layout_load.addWidget(self.load_textbox)
        layout_load.addWidget(self.button_load)


        # ==== Schedule play controls
        layout_play = QHBoxLayout()

        layout_playbuttons = QHBoxLayout()
        self.button_play = QPushButton("Play")
        self.button_pause = QPushButton("Pause")
        self.button_reset = QPushButton("Reset")
        layout_playbuttons.addWidget(self.button_play)
        layout_playbuttons.addWidget(self.button_pause)
        layout_playbuttons.addWidget(self.button_reset)

        # Create playdisplay values
        self.current_time = 0
        self.current_step = 0
        self.total_steps = 0
        self.entry_current = None

        self.time_display = QLabel()
        self.step_display = QLabel()

        self.update_playdisplay()

        layout_display = QVBoxLayout()
        layout_display.addWidget(self.time_display)
        layout_display.addWidget(self.step_display)

        layout_play.addLayout(layout_playbuttons)
        layout_play.addLayout(layout_display)


        # ==== Schedule view
        self.scheduleview = QTextEdit()
        self.scheduleview.setReadOnly(True)
        self.scheduleview.setFontFamily("Monospace")
        self.scheduleview.setFontPointSize(8)
        self.scheduleview.setPlainText("Test")
        # self.scheduleview.setMinimumHeight(200)

        # ==== Consolidation
        layout0.addLayout(layout_load, 1, 1)
        layout0.addLayout(layout_play, 2, 1)
        layout0.addWidget(self.scheduleview, 3, 1)

        # ==== TEST BUTTONS
        self.testbutton1 = QPushButton("T1")
        self.testbutton1.clicked.connect(self.testfunc2)
        self.testbutton2 = QPushButton("T2")
        # self.testbutton2.clicked.connect(self.do_threaded)
        self.testbutton3 = QPushButton("T3")
        self.testbutton3.clicked.connect(self.update_scheduleview)
        layout0.addWidget(self.testbutton1, 5, 1)
        layout0.addWidget(self.testbutton2, 6, 1)
        layout0.addWidget(self.testbutton3, 7, 1)
        # =================

        # layout0.setRowStretch(3, 10)

        self.setLayout(layout0)


        # self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    # def do_threaded(self):
    #     worker = Worker()
    #     self.threadpool.start(worker)

    # @Slot()
    def update_current_time(self):
        self.current_time += 1
        self.update_playdisplay()

    # @Slot()
    def update_current_step(self):
        self.current_step += 1
        self.update_playdisplay()


    def scheduleview_parseheader(self):
        header = " "
        header += "i".center(len(str(len(self.schedule_content))))
        header += " | "
        header += "t [s]".center(8)
        header += " | "
        header += "Bx [uT]".center(8)
        header += " | "
        header += "By [uT]".center(8)
        header += " | "
        header += "Bz [uT]".center(8)
        header += " |"
        return header


    def scheduleview_parseseparator(self):
        separator = "-"
        separator += "-"*(len(str(len(self.schedule_content))))
        separator += ("-|-" + "-"*8)*4 + "-|"
        return separator


    def scheduleview_parseline(self, i_line=0, sel=False):
        line = self.schedule_content[i_line]

        if sel:
            parsedline = ">"
            parsedline += str(i_line).rjust(len(str(len(self.schedule_content))))
            parsedline += "< >"
            parsedline += str(line[0]).rjust(8)
            parsedline += "<|>"
            parsedline += str(line[1]).rjust(8)
            parsedline += "<|>"
            parsedline += str(line[2]).rjust(8)
            parsedline += "<|>"
            parsedline += str(line[3]).rjust(8)
            parsedline += "<|"
        else:
            parsedline = " "
            parsedline += str(i_line).rjust(len(str(len(self.schedule_content))))
            parsedline += "   "
            parsedline += str(line[0]).rjust(8)
            parsedline += " | "
            parsedline += str(line[1]).rjust(8)
            parsedline += " | "
            parsedline += str(line[2]).rjust(8)
            parsedline += " | "
            parsedline += str(line[3]).rjust(8)
            parsedline += " |"

        return parsedline

    # @Slot()  # TODO: REMOVE
    def testfunc1(self):
        scheduleinfo = ""
        scheduleinfo += "<span style=font-family:'Courier'; font-size:11pt; font-weight:600;>"
        scheduleinfo += "<span style='white-space: pre'>"
        scheduleinfo += "0 1  2   3    4     5"
        scheduleinfo += "<br> T  E    S  T"
        # for i in range(len(self.schedule_content)):
            # if i == 2:
            #     scheduleinfo += self.b(self.div(self.scheduleview_parseline(i))) + br
            # else:
            #     scheduleinfo += self.div(self.scheduleview_parseline(i)) + br
        # scheduleinfo += "</div>"
        scheduleinfo += "</span>"
        scheduleinfo += "</span>"
        # print(scheduleinfo)
        self.scheduleview.setPlainText(scheduleinfo)

    # @Slot()  # TODO: REMOVE
    def testfunc2(self):
        scheduleinfo = ""
        scheduleinfo += self.scheduleview_parseheader() + "\n"
        scheduleinfo += self.scheduleview_parseseparator() + "\n"
        for i in range(len(self.schedule_content)):
            if i == self.current_step-1:
                scheduleinfo += self.scheduleview_parseline(i, sel=True) + "\n"
            else:
                scheduleinfo += self.scheduleview_parseline(i, sel=False) + "\n"
        # print(scheduleinfo)
        self.scheduleview.setPlainText(scheduleinfo)

    # @Slot()  # TODO: REMOVE
    def update_scheduleview_html(self):

        # DEBUG
        # print(self.scheduleview_parseheader())
        # print(self.scheduleview_parseseparator())
        # for i in range(len(self.schedule_content)):
            # print(self.scheduleview_parseline(i))

        br = "<br>"

        scheduleinfo = ""
        scheduleinfo += "<span style='white-space: pre'>"
        scheduleinfo += "<span style=font-family:'Courier'; font-size:10pt;>"
        scheduleinfo += self.b(self.scheduleview_parseheader()) + br
        scheduleinfo += self.scheduleview_parseseparator() + br
        for i in range(len(self.schedule_content)):
            if i == 2:
                scheduleinfo += self.b(self.scheduleview_parseline(i)) + br
            else:
                scheduleinfo += self.scheduleview_parseline(i) + br
        scheduleinfo += "</span></span>"
        # print(scheduleinfo)
        self.scheduleview.setHtml(scheduleinfo)

    # @Slot()
    def update_scheduleview(self):
        scheduleinfo = ""
        scheduleinfo += self.scheduleview_parseheader() + "\n"
        scheduleinfo += self.scheduleview_parseseparator() + "\n"
        for i in range(len(self.schedule_content)):
            if i == 2:
                scheduleinfo += self.scheduleview_parseline(i, sel=True) + "\n"
            else:
                scheduleinfo += self.scheduleview_parseline(i, sel=False) + "\n"
        # print(scheduleinfo)
        self.scheduleview.setPlainText(scheduleinfo)

    # @Slot()
    def update_playdisplay(self):

        if self.entry_current:
            pass  # TODO: Add entry handling
        self.time_display.setText(
            "Time: " + str(self.current_time).rjust(5) + " s"
        )
        self.step_display.setText(
            "Step: "
            + (str(self.current_step) + "/" + str(self.total_steps)).rjust(10)
        )

    # @Slot()
    def load_schedule(self):
        filepath_dialog = QFileDialog.getOpenFileName(
            self,
            "Open Schedule",
            "",
            "B-schedule Files (*.bsch);; All Files (*.*)"
        )
        filepath = filepath_dialog[0]
        filename = os.path.basename(filepath)

        # print(filepath)
        # print(filename)

        self.schedule_filepath = filepath
        self.schedule_filename = filename

        with open(filepath) as f:
            content = f.readlines()

        # print("")
        # print(content)
        #
        # print(self.parse_schedule(content))
        # print(len(self.parse_schedule(content)))

        self.schedule_content = self.parse_schedule(content)

        self.load_textbox.setPlaceholderText(filename)

        # Reset play control values
        self.current_time = 0
        self.current_step = 1
        self.total_steps = len(self.schedule_content)

        # Update playdisplay with schedule properties
        self.update_playdisplay()

    @staticmethod
    def parse_schedule(unparsed_schedule):
        # Pre-allocate ndarray
        parsed_schedule = np.zeros((len(unparsed_schedule), 4))

        for i, line in enumerate(unparsed_schedule):

            # Remove newline characters independent of OS
            lensep = len(os.linesep)
            if line[-(lensep-1):] == os.linesep:
                line = line[:-(lensep-1)]

            # Split the line
            split_line = line.split(" ")

            # Push into ndarray
            for j in range(4):
                parsed_schedule[i, j] = split_line[j]

        return parsed_schedule

    # def load_schedule(self):
    #     file_filter = "B-Schedule File (*.bsched)"
    #
    #     response = QFileDialog.getOpenFileName(
    #         parent=self,
    #         caption="Select a schedule file",
    #         # directory=os.getcwd(),
    #         filter=file_filter,
    #         # initialFilter="B-Schedule File (*.bsched)"
    #     )
    #     self.load_textbox.setText(str(response))

class GroupFieldReadout(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("GroupFieldReadout")
        self.data = datapool

        # self.setMinimumSize(QSize(480, 360))

        layout0 = QGridLayout()
        layout0.setColumnStretch(4, 1)  # Ensure left horizontal alignment

        lcd0x = QLCDNumber()
        lcd0x.setStyleSheet(self.data.config["stylesheet_lcd_red"])
        layout0.addWidget(QLabel("B_x: "), 1, 1)
        layout0.addWidget(lcd0x, 1, 2)
        layout0.addWidget(QLabel(" uT"), 1, 3)

        lcd0y = QLCDNumber()
        lcd0y.setStyleSheet(self.data.config["stylesheet_lcd_green"])
        layout0.addWidget(QLabel("B_y: "), 2, 1)
        layout0.addWidget(lcd0y, 2, 2)
        layout0.addWidget(QLabel(" uT"), 2, 3)

        lcd0z = QLCDNumber()
        lcd0z.setStyleSheet(self.data.config["stylesheet_lcd_blue"])
        layout0.addWidget(QLabel("B_z: "), 3, 1)
        layout0.addWidget(lcd0z, 3, 2)
        layout0.addWidget(QLabel(" uT"), 3, 3)

        lcd0abs = QLCDNumber()
        lcd0abs.setStyleSheet(self.data.config["stylesheet_lcd_white"])
        layout0.addWidget(QLabel("B_abs: "), 4, 1)
        layout0.addWidget(lcd0abs, 4, 2)
        layout0.addWidget(QLabel(" uT"), 4, 3)

        self.lcd0 = (lcd0x, lcd0y, lcd0z, lcd0abs)

        # Common lcd settings
        maxdigits = self.data.config["lcd_maxdigits"]
        for lcd in self.lcd0:
            lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
            lcd.setDigitCount(maxdigits)

        layout1 = QGridLayout()

        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.advance_clock)
        self.timer2 = QTimer()
        self.timer2.timeout.connect(self.b_read)

        # self.pollrate = 20

        self.clock = 0
        self.widget_clock = QLabel(str(self.clock))
        self.count = 0
        self.widget_counter = QLabel(str(self.count))
        layout1.addWidget(QLabel("Clock: "), 0, 0)
        layout1.addWidget(self.widget_clock, 0, 1)
        layout1.addWidget(QLabel("Count: "), 1, 0)
        layout1.addWidget(self.widget_counter, 1, 1)
        layout1.addWidget(QLabel("Polling rate: "), 2, 0)
        layout1.addWidget(QLabel(str(self.data.adc_pollrate)), 2, 1)
        layout1.addWidget(QLabel(" Hz"), 2, 2)

        layout0.addLayout(layout1, 0, 1)

        self.redraw_lcd()

        self.setLayout(layout0)

        self.timer1.start(1000)
        self.timer2.start(int(1000/self.data.adc_pollrate))

    def redraw_lcd(self):
        for i, lcd in enumerate(self.lcd0):
            if i < 3:
                lcd.display(round(self.data.B_m[i], 3))
            elif i == 3:
                lcd.display(round(np.linalg.norm(self.data.B_m), 3))

    def advance_clock(self):
        self.clock += 1
        self.widget_clock.setText(str(self.clock))

    def advance_count(self):
        self.count += 1
        self.widget_counter.setText(str(self.count))

    # @Slot()
    def b_read(self):
        if self.data.config["use_dummies"]:
            self.data.B_m = self.data.B_m
        else:
            (self.data.B_m, self.data.tBm) = \
            self.data.magnetometer.read(convert_to_b=True)
        self.redraw_lcd()
        self.advance_count()


class HHCPlot(pg.GraphicsLayoutWidget):
    def __init__(self, direction="YZ", bscale=1.0):
        super().__init__()

        self.direction = direction
        self.bscale = bscale
        self.plot = self.addPlot(row=0, col=0)
        self.resize(360, 360)
        self.plot.setRange(xRange=(-1, 1), yRange=(-1, 1))
        self.plot.showGrid(x=True, y=True)
        self.plot.showAxis('bottom', True)
        self.plot.showAxis('left', True)

        if direction == "YZ":
            self.plot_hhc_elements_yz()
        elif direction == "XY":
            self.plot_hhc_elements_xy()
        else:
            raise ValueError("Parameter 'direction' must be 'XY' or 'YZ'!")

        # self.arrow_length = 100 * 1.28  # Correcting for plot abnormalities

        self.arrow = pg.ArrowItem(angle=0, headLen=20, tailLen=self.arrow_length(), pen=None, brush='y')
        self.plot.addItem(self.arrow)
        self.arrow.setPos(-1, 0)

    def arrow_length(self, l=1.0):
        return 100*1.28*l/self.bscale - 20

    def plot_hhc_elements_xy(self):

        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#F00F", "#0F0F", "#22FF")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot.addItem(coils[i])

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.25, 2 * 0.25, 2 * 0.25)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot.addItem(item)

    def plot_hhc_elements_yz(self):
        ts = 0.15
        tripod = (
            QGraphicsLineItem(QLineF(-1, -1, -1+ts, -1)),
            QGraphicsLineItem(QLineF(-1, -1, -1, -1+ts)),
            QGraphicsLineItem(QLineF(-1, -1, -1-ts/3, -1-ts/5))
        )
        for i, c in enumerate(("#0F0F", "#22FF", "#F00F")):
            tripod[i].setPen(pg.mkPen(c))
            self.plot.addItem(tripod[i])

        coils = (
            QGraphicsRectItem(QRectF(-0.90, -0.90, 2 * 0.90, 2 * 0.90)),
            QGraphicsRectItem(QRectF(-0.95, -0.95, 2 * 0.95, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.80, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF( 0.75, -0.95, 0.05, 2 * 0.95)),
            QGraphicsRectItem(QRectF(-0.95, -0.80, 2 * 0.95, 0.05)),
            QGraphicsRectItem(QRectF(-0.95,  0.75, 2 * 0.95, 0.05)),
        )
        for i, c in enumerate(("#F008", "#F008", "#0F08", "#0F08", "#22F8", "#22F8")):
            coils[i].setPen(pg.mkPen(c))
            self.plot.addItem(coils[i])

        table = (
            QGraphicsRectItem(QRectF(-0.25, -0.05, 2 * 0.25, 1 * 0.05)),
            QGraphicsRectItem(QRectF(-0.15, -1, 0.05, 0.95)),
            QGraphicsRectItem(QRectF(0.1, -1, 0.05, 0.95)),
        )

        for item in table:
            item.setPen(pg.mkPen("#FFF6"))
            self.plot.addItem(item)


class Group2dPlot(QGroupBox):
    def __init__(self, datapool) -> None:
        super().__init__("Visualizations")
        self.data = datapool

        windowsize = (self.data.config["plotwindow_windowsize"][0],
                      self.data.config["plotwindow_windowsize"][1])
        self.setMinimumSize(QSize(windowsize[0], windowsize[1]))
        self.setMaximumSize(QSize(windowsize[0], windowsize[1]))

        layout0 = QGridLayout()

        self.bscale = self.data.config["plotwindow_bscale"]
        self.hhcplot_yz = HHCPlot(direction="YZ", bscale=self.bscale)
        self.hhcplot_xy = HHCPlot(direction="XY", bscale=self.bscale)

        layout0.addWidget(QLabel("Front view (YZ)"), 0, 0)
        layout0.addWidget(self.hhcplot_yz, 1, 0)

        layout0.addWidget(QLabel("Top view (XY)"), 0, 1)
        layout0.addWidget(self.hhcplot_xy, 1, 1)
        # layout0.addWidget(QLabel("Layout2dPlots"))

        self.setLayout(layout0)


        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.update_bvector)
        self.timer1.start(int(1000/self.data.config["plotwindow_updaterate"]))

    # @Slot()
    def random_move_arrow(self):
        self.hhcplot_yz.arrow.setStyle(angle=np.random.uniform(0, 360))
        self.hhcplot_yz.arrow.setPos(np.random.uniform(), np.random.uniform())

    # @Slot()
    def point_vector_random(self):
        # x = -1; y = -1; z = 0
        x = np.random.uniform(-1, 1)
        y = np.random.uniform(-1, 1)
        z = np.random.uniform(-1, 1)

        xy = np.array([x, y])
        yz = np.array([y, z])
        b = np.array([1, 0])

        if y != 0:
            sign_y = y/np.abs(y)
        else:
            sign_y = 1
        angle_xy = sign_y * (180/np.pi*(np.arccos(np.dot(xy, b) / (np.linalg.norm(xy) * np.linalg.norm(b)))))
        abslen_xy = np.linalg.norm(xy)


        if z != 0:
            sign_z = z/np.abs(z)
        else:
            sign_z = 1
        angle_yz = sign_z * (180/np.pi*(np.arccos(np.dot(yz, b) / (np.linalg.norm(yz) * np.linalg.norm(b)))))
        abslen_yz = np.linalg.norm(yz)

        self.hhcplot_xy.arrow.setStyle(angle=-angle_xy+180, tailLen=self.hhcplot_xy.arrow_length(abslen_xy))
        self.hhcplot_xy.arrow.setPos(x, y)

        self.hhcplot_yz.arrow.setStyle(angle=-angle_yz+180, tailLen=self.hhcplot_yz.arrow_length(abslen_yz))
        self.hhcplot_yz.arrow.setPos(y, z)

        # print(f"Displaying (x,y,z) = ({round(x, 2)}, {round(y, 2)}, {round(z, 2)})")
        # print(f"angle_xy = {round(angle_xy, 1)} deg  -  angle_yz = {round(angle_yz, 1)} deg")
        # print(f"abslen_xy = {round(abslen_xy, 3)}  -  abslen_xy = {round(abslen_xy, 3)}")


        # xt = x * self.hhcplot.plot.getViewBox().mapSceneToView(QPoint(x, self.hhcplot.plot.width())).x()
        # yt = y * self.hhcplot.plot.getViewBox().mapSceneToView(QPoint(y, self.hhcplot.plot.height())).y()
        # print(xt, yt)

    def update_bvector(self):
        bx, by, bz = self.data.B_m
        xy = np.array([bx, by])
        yz = np.array([by, bz])
        b = np.array([1, 0])

        if by != 0:
            sign_y = by/np.abs(by)
        else:
            sign_y = 1
        angle_xy = sign_y * (180/np.pi*(np.arccos(np.dot(xy, b) / (np.linalg.norm(xy) * np.linalg.norm(b)))))
        abslen_xy = np.linalg.norm(xy) 


        if bz != 0:
            sign_z = bz/np.abs(bz)
        else:
            sign_z = 1
        angle_yz = sign_z * (180/np.pi*(np.arccos(np.dot(yz, b) / (np.linalg.norm(yz) * np.linalg.norm(b)))))
        abslen_yz = np.linalg.norm(yz)

        # plot_correction = 100*1.28

        self.hhcplot_xy.arrow.setStyle(angle=-angle_xy+180, tailLen=self.hhcplot_xy.arrow_length(abslen_xy))
        self.hhcplot_xy.arrow.setPos(bx/self.bscale, by/self.bscale)

        self.hhcplot_yz.arrow.setStyle(angle=-angle_yz+180, tailLen=self.hhcplot_yz.arrow_length(abslen_yz))
        self.hhcplot_yz.arrow.setPos(by/self.bscale, bz/self.bscale)


