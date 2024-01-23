from PyQt5.QtCore import (
    QTimer,
)

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

    def start(self):
        self.timer.start(self.march_interval)

    def stop(self):
        self.timer.stop()

    def reset(self):
        self.step = 0
        self.t = 0.0
        self.t_next = 0.0
        self.update()

    def set_march_mult(self, march_mult):
        self.march_mult = march_mult

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