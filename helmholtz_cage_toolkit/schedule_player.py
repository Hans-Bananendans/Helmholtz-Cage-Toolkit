# from PyQt5.QtCore import (
#     QTimer,
# )

from helmholtz_cage_toolkit import *

class SchedulePlayer:
    def __init__(self, datapool, march_interval=10, maxskips=10):

        # External variables: self.datapool.get_schedule_steps()
        self.datapool = datapool
        self.maxskips = maxskips
        self.march_interval = march_interval    # [ms] event loop frequency
        self.init_values()


    def init_values(self):
        self.step = 0
        self.t = 0.0
        self.t_next = 0.0
        self.march_mult = 1
        self.timer = QTimer()
        self.timer.timeout.connect(self.march)

    # @Slot()
    def start(self):
        self.timer.start(self.march_interval)

    # @Slot()
    def stop(self):
        self.timer.stop()

    # @Slot()
    def reset(self):
        self.step = 0
        self.t = 0.0
        self.t_next = 0.0
        self.update()

    def set_march_mult(self, march_mult):
        self.march_mult = march_mult

    # @Slot()
    def march(self):
        """ Marches using self.timer

        General idea:
         - Keep it low overhead for cases where number of timer loops is large
            between each call of self.update()
         - Make timer able to recognise when timestep of timer was so large
            that multiple steps have to be skipped.
         - Make timer able to recognise when current step exceeds total number
            of steps, and handle this case correctly.

        Setup:
        1. Find out whether t is larger than t_next. If not, increment by dt,
            where dt is current time [s] plus ( time interval per march [ms]
            times march multiplier [ms] ) divided by 1000 [ms->s]
        2. Define d=1 as the number of steps it is going to skip
        3. Loop over the next maxskips step and check whether t is also larger
            than any of them.
        4. Keep incrementing d each time you check.
        5. Once loop ends, check whether schedule end was reached
          - If it has, set self.step to 0 and self.t to 0.0
          - If not, increment self.step by d, calculate t_text, and call
            self.update()

        Un-optimized overhead:
        ~42 us of overhead for if
        ~11 us of overhead for else
        This includes 4 time() calls, and excludes the update() call
        """
        # t0 = time()  # [TIMING]

        # print(f"[DEBUG] t.= {round(self.t, 1)}/{round(self.datapool.get_schedule_duration(), 1)}", end=" ")
        # print(f"tnext.= {round(self.t_next, 1)}", end=" ")
        # print(f"step.= {self.step}/{self.datapool.get_schedule_steps()}", end=" ")
        if self.t >= self.t_next:
            for d in range(1, self.maxskips+1):
                if self.t >= self.datapool.schedule[2][
                    (self.step + d + 1) % self.datapool.get_schedule_steps()]:
                    pass
                else:
                    break

            # print(f"d. = {d}")

            # Check for end-of-schedule
            # TODO Using -2 instead of -1 to fix a bug that prevents the if
            # TODO from triggering for high playback speeds.
            # TODO This is a stupid fix and introduces other bugs (schedules
            # TODO of length 1!), but for now it works
            # if self.step + d >= self.datapool.get_schedule_steps()-1:
            if self.step + d >= self.datapool.get_schedule_steps()-2:
                # print("[DEBUG] END OF SCHEDULE")
                self.t = 0.0
                self.step = 0
            else:
                self.t = (self.t + self.march_mult * self.march_interval / 1000) \
                         % self.datapool.get_schedule_duration()
                self.step += d

            # t1 = time()  # [TIMING]
            self.update()
            # t2 = time()  # [TIMING]

            self.t_next = self.datapool.schedule[2][
                (self.step + 1) % self.datapool.get_schedule_steps()]

        else:
            # t1 = time()  # [TIMING]
            # t2 = time()  # [TIMING]
            self.t = (self.t + self.march_mult*self.march_interval/1000)
            # print(f"")

        # print("Time: ", round((time()-t0 - (t2-t1))*1E6), "us")  # [TIMING]

    def update(self):
        """Method to overload."""
        pass


class PlayerControls(QGroupBox):
    """Defines a set of UI elements for playback control. It is linked to an
    instance to the SchedulePlayer class, which handles the actual playback."""
    def __init__(self, datapool, scheduleplayer, label_update_interval=30) -> None:
        super().__init__()

        self.datapool = datapool
        self.setStyleSheet(
            self.datapool.config["stylesheet_groupbox_smallmargins_notitle"]
        )

        self.scheduleplayer = scheduleplayer

        # Speed at which labels will update themselves. Slave the act of
        # performing the update to a QTimer.
        self.label_update_interval = label_update_interval
        self.label_update_timer = QTimer()
        self.label_update_timer.timeout.connect(self.update_labels)

        # To keep overhead on the update_label() function minimal, already
        # generate the strings of the total schedule duration and steps
        self.str_step_prev = 0
        self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
        self.str_steps = "/{}".format(self.datapool.get_schedule_steps())

        # Main layout
        layout0 = QHBoxLayout()

        # Generate and configure playback buttons
        self.button_play = QPushButton()
        self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))
        self.button_play.toggled.connect(self.toggle_play)
        self.button_play.setCheckable(True)

        self.button_reset = QPushButton()
        self.button_reset.setIcon(QIcon("./assets/icons/feather/rotate-ccw.svg"))
        self.button_reset.clicked.connect(self.toggle_reset)

        self.button_mult10 = QPushButton()
        self.button_mult10.setIcon(QIcon("./assets/icons/x10.svg"))
        self.button_mult10.toggled.connect(self.toggle_mult10)
        self.button_mult10.setCheckable(True)

        self.button_mult100 = QPushButton()
        self.button_mult100.setIcon(QIcon("./assets/icons/x100.svg"))
        self.button_mult100.toggled.connect(self.toggle_mult100)
        self.button_mult100.setCheckable(True)

        self.button_mult1000 = QPushButton()
        self.button_mult1000.setIcon(QIcon("./assets/icons/x1000.svg"))
        self.button_mult1000.toggled.connect(self.toggle_mult1000)
        self.button_mult1000.setCheckable(True)

        self.buttons_playback = (
            self.button_play,
            self.button_reset,
        )
        self.buttons_mult = (
            self.button_mult10,
            self.button_mult100,
            self.button_mult1000,
        )

        button_size = QSize(32, 32)
        button_size_icon = QSize(24, 24)

        for button in self.buttons_playback+self.buttons_mult:
            button.setFixedSize(button_size)
            button.setIconSize(button_size_icon)
            layout0.addWidget(button)



        # Generate and configure playback labels
        self.label_t = QLabel("0.000/0.000")
        self.label_t.setMinimumWidth(256)
        self.label_step = QLabel("0/0")

        self.update_labels()

        for label in (self.label_t, self.label_step):
            label.setStyleSheet(self.datapool.config["stylesheet_label_timestep"])
            label.setAlignment(Qt.AlignRight)
            layout0.addWidget(label)

        self.setLayout(layout0)


    def refresh(self):
        # Stops playback when called
        self.toggle_reset()
        self.button_play.setChecked(False)

        self.str_step_prev = 0
        self.str_duration = "/{:.3f}".format(round(self.datapool.get_schedule_duration(), 3))
        self.str_steps = "/{}".format(self.datapool.get_schedule_steps())
        self.update_labels(force_refresh=True)

    # def uncheck_buttons(self, buttons_group): # TODO DELETE UNUSED
    #     for button in buttons_group:
    #         button.setChecked(False)

    # @Slot()
    def toggle_play(self):
        # If user clicked button and playback has to "turn on", start playback
        # immediately, start the label update timer, and change the icon to
        # indicate it now functions as pause button.
        if self.button_play.isChecked():
            self.scheduleplayer.start()
            self.label_update_timer.start(self.label_update_interval)
            self.button_play.setIcon(QIcon("./assets/icons/feather/pause.svg"))

        # If user clicked button and playback has to "pause", stop playback
        # immediately, stop the label update timer, and change the icon to
        # indicate it now functions as play button.
        else:
            self.scheduleplayer.stop()
            self.label_update_timer.stop()
            self.button_play.setIcon(QIcon("./assets/icons/feather/play.svg"))

    # @Slot()
    def toggle_reset(self):
        self.scheduleplayer.reset()

    def set_mult(self, mult):
        # Sets the march multiplier on the SchedulePlayer
        self.scheduleplayer.set_march_mult(mult)

    def toggle_mult10(self):
        # If toggled, uncheck other mult buttons, and set playback to x10
        if self.button_mult10.isChecked():
            self.button_mult100.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(10)
        else:
            self.set_mult(1)

    # @Slot()
    def toggle_mult100(self):
        # If toggled, uncheck other mult buttons, and set playback to x100
        if self.button_mult100.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult1000.setChecked(False)
            self.set_mult(100)
        else:
            self.set_mult(1)

    # @Slot()
    def toggle_mult1000(self):
        # If toggled, uncheck other mult buttons, and set playback to x1000
        if self.button_mult1000.isChecked():
            self.button_mult10.setChecked(False)
            self.button_mult100.setChecked(False)
            self.set_mult(1000)
        else:
            self.set_mult(1)

    # @Slot()
    def update_labels(self, force_refresh=False):
        """ Updates the time and step label.

        Optimizations:
         - Pre-generate the string with total steps and duration, so they do
            not have to be calculated in the loop.
         - Replace the only instance of round with a custom 3-digit round that
            has ~30 us less overhead.
         - Save ~10 us of overhead per cycle by not updating steps label when
            step was not updated internally.
        Total improvement from ~150 us to ~50 us
        """
        # t0 = time()  # [TIMING]
        self.label_t.setText("{:.3f}".format(
                (self.scheduleplayer.t * 2001) // 2 / 1000) + self.str_duration)
        # t1 = time()  # [TIMING]

        if self.scheduleplayer.step != self.str_step_prev or force_refresh:
            self.label_step.setText(
                str(self.scheduleplayer.step) + self.str_steps
            )
            self.str_step_prev = self.scheduleplayer.step

        # t2 = time()  # [TIMING]
        # print(f"[TIMING] update_labels(): {round((t1-t0)*1E6)} us  {round((t2-t1)*1E6)} us")  # [TIMING]
