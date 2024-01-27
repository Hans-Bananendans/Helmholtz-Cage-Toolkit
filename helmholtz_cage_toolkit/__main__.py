""" HCT GUI Framework

This project covers a GUI framework for the Helmholtz Cage Toolkit, written
in PySide6.
"""

# __author__ = "Johan Monster"
# __credits__ = ["Johan Monster"]
# __license__ = "GPL"
# __version__ = "0.0.1"

# Imports
import sys

from helmholtz_cage_toolkit import *

from PyQt5.QtWidgets import QApplication
# from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from helmholtz_cage_toolkit.main_window import MainWindow
from helmholtz_cage_toolkit.config import config



if __name__ == "__main__":

    app = QApplication(sys.argv)
    if config["enable_skin"]:
        apply_stylesheet(app, theme="dark_teal.xml")
    window = MainWindow(config)
    window.show()
    app.exec()