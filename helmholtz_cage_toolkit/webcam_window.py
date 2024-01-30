import os
import time


from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.datapool import DataPool



class WebcamWindow(QWidget):
    def __init__(self, config, datapool):
        super().__init__()

        self.datapool = datapool


        layout0 = QGridLayout()

        # DUMMY LABEL # TODO REMOVE
        layout0.addWidget(QLabel("WEBCAM WINDOW"))

        self.setLayout(layout0)

    


