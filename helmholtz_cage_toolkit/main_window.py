from time import time

# from PyQt5 import Qt
# from PySide6 import Qt

import pyqtgraph as pg
import numpy as np

from helmholtz_cage_toolkit import *
from helmholtz_cage_toolkit.datapool import DataPool
from helmholtz_cage_toolkit.control_window import ControlWindow
from helmholtz_cage_toolkit.cyclics_window import CyclicsWindow
from helmholtz_cage_toolkit.orbital_window import OrbitalWindow
from helmholtz_cage_toolkit.connection_window import ConnectionWindow
from helmholtz_cage_toolkit.webcam_window import WebcamWindow
from helmholtz_cage_toolkit.command_window import CommandWindow
from helmholtz_cage_toolkit.orbit_design_window import OrbitDesignWindow
from helmholtz_cage_toolkit.file_handling import load_file, save_file, NewFileDialog


class TestTab(QWidget):
    # Todo: Eventually remove
    def __init__(self, tabname: str):
        super().__init__()
        layout_0 = QVBoxLayout()
        layout_0.addWidget(QLabel(tabname))
        layout_0.addWidget(QLabel(f"Instance: {self}"))
        self.setLayout(layout_0)

class MainWindow(QMainWindow):
    def __init__(self, config) -> None:
        super().__init__()

        # Load config
        self.config = config

        # Create the global instance of DataPool
        self.datapool = DataPool(self, config)

        # Main window options
        self.resize(config["default_windowsize"][0],
                    config["default_windowsize"][1])  # Default w x h dimensions

        self.datapool.main_window = self                # Reference to datapool

        # Make a menu bar
        menubar = self.create_menubar()
        self.setMenuBar(menubar)
        self.datapool.menu_bar = menubar                # Reference to datapool

        # Statusbar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.datapool.status_bar = status_bar           # Reference to datapool

        # CentralWidget
        self.tabcontainer = QStackedWidget()  # Important: this must be defined before calling create_tabbar()
        self.setCentralWidget(self.tabcontainer)
        self.datapool.tabcontainer = self.tabcontainer  # Reference to datapool

        # Tabbar
        tabbar = self.create_tabbar()
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tabbar)
        self.datapool.tab_bar = tabbar                  # Reference to datapool

    # @Slot()
    def load(self):
        gen = load_file(self.datapool)
        self.datapool.refresh(source=gen)

    # @Slot()
    def save(self):
        save_file(self.datapool)

    # @Slot()
    def newfile(self):
        out = NewFileDialog().run()
        if out == 1:
            print("[DEBUG] Started new file")
            self.datapool.init_schedule()
            self.datapool.refresh(source="orbital")
            self.datapool.set_window_title()


    def create_menubar(self):
        # TODO: Add menus
        # TODO: Autogenerate from config dict
        menubar = QMenuBar()

        menu_file = menubar.addMenu("&File")
        menu_view = menubar.addMenu("&View")
        menu_tools = menubar.addMenu("&Tools")
        menu_help = menubar.addMenu("&Help")


        # Menu bar - File menu
        # TODO: Add menu items, connect actions
        act_new = QAction(
            QIcon("./assets/icons/feather/file.svg"),
            "&New", self)
        act_new.setStatusTip("Start with an empty file")
        act_new.triggered.connect(self.newfile)
        act_new.setCheckable(False)
        act_new.setShortcut(QKeySequence("Ctrl+n"))
        menu_file.addAction(act_new)

        act_load = QAction(
            QIcon("./assets/icons/feather/folder.svg"),
            "&Load B-schedule...", self)
        act_load.setStatusTip("Load a previously saved B-schedule file")
        act_load.triggered.connect(self.load)
        act_load.setCheckable(False)
        act_load.setShortcut(QKeySequence("Ctrl+o"))
        menu_file.addAction(act_load)

        act_saveas = QAction(
            icon=QIcon("./assets/icons/feather/save.svg"),
            text="&Save as...", parent=self)
        act_saveas.setStatusTip("Save a B-schedule to a .bsch file...")
        act_saveas.triggered.connect(self.save)
        act_saveas.setCheckable(False)
        menu_file.addAction(act_saveas)


        #
        # act_save_config = QAction(
        #     QIcon(QPixmap(":save")),
        #     "&Save configuration", self)
        # act_save_config.setStatusTip("Save this configuration to a file")
        # # act_save_config.triggered.connect()
        # act_save_config.setCheckable(False)
        # act_save_config.setShortcut(QKeySequence("Ctrl+s"))
        #
        # act_settings = QAction(
        #     QIcon(QPixmap(":settings")),
        #     "Settings", self)
        # act_settings.setStatusTip("View and edit program settings")
        # # act_settings.triggered.connect()
        # act_settings.setCheckable(False)
        #
        # act_quit = QAction(text="&Quit", parent=self)
        # act_quit.setStatusTip("Save this configuration to a file")
        # # act_quit.triggered.connect()
        # act_quit.setCheckable(False)
        #
        # menu_file.addAction(act_new)
        # menu_file.addAction(act_load)
        # menu_file.addAction(act_saveas)
        # menu_file.addAction(act_save_config)
        # menu_file.addSeparator()
        # menu_file.addAction(act_settings)
        # menu_file.addSeparator()
        # menu_file.addAction(act_quit)
        #
        # # Menu bar - View menu
        # # TODO: Add menu items
        act_toggle_plot_visibility_tabs = QAction(
            QIcon("./assets/icons/sidebar_right.svg"),
            "Show plot &sidebars", self)
        act_toggle_plot_visibility_tabs.setStatusTip(
            "Dump the internal datapool to the terminal.")
        act_toggle_plot_visibility_tabs.triggered.connect(
            self.datapool.toggle_plot_visibility_tabs)
        act_toggle_plot_visibility_tabs.setCheckable(True)
        act_toggle_plot_visibility_tabs.setChecked(
            self.datapool.config["show_plot_visibility_tabs"])
        menu_view.addAction(act_toggle_plot_visibility_tabs)



        # # Menu bar - Tools menu
        # # TODO: Add menu items, connect actions
        act_dump_datapool = QAction(
            QIcon("./assets/icons/feather/terminal.svg"),
            "Dump &datapool", self)
        act_dump_datapool.setStatusTip("Dump the internal datapool to the terminal.")
        act_dump_datapool.triggered.connect(self.datapool.dump_datapool)
        act_dump_datapool.setCheckable(False)
        menu_tools.addAction(act_dump_datapool)

        act_dump_config = QAction(
            QIcon("./assets/icons/feather/terminal.svg"),
            "Dump &config", self)
        act_dump_config.setStatusTip("Dump the loaded config file to the terminal.")
        act_dump_config.triggered.connect(self.datapool.dump_config)
        act_dump_config.setCheckable(False)
        menu_tools.addAction(act_dump_config)

        act_dump_generation_parameters_cyclics = QAction(
            QIcon("./assets/icons/feather/terminal.svg"),
            "Dump C&yclics genparameters", self)
        act_dump_generation_parameters_cyclics.setStatusTip("Dump the current Cyclics generation parameters to the terminal.")
        act_dump_generation_parameters_cyclics.triggered.connect(self.datapool.dump_generation_parameters_cyclics)
        act_dump_generation_parameters_cyclics.setCheckable(False)
        menu_tools.addAction(act_dump_generation_parameters_cyclics)

        act_dump_generation_parameters_orbital = QAction(
            QIcon("./assets/icons/feather/terminal.svg"),
            "Dump &Orbital genparameters", self)
        act_dump_generation_parameters_orbital.setStatusTip("Dump the current Orbital generation parameters to the terminal.")
        act_dump_generation_parameters_orbital.triggered.connect(self.datapool.dump_generation_parameters_orbital)
        act_dump_generation_parameters_orbital.setCheckable(False)
        menu_tools.addAction(act_dump_generation_parameters_orbital)

        # ==== Bm_sim action group
        # TODO: DISABLE UNTIL CONNECT
        menu_tools.addSection("Bm_sim") # Doesn't display text in qt_material
        actgroup_Bm_sim = QActionGroup(menu_tools)

        act_bm_sim_disabled = QAction("Bm_sim - disabled", self)
        act_bm_sim_disabled.setActionGroup(actgroup_Bm_sim)
        act_bm_sim_disabled.setStatusTip("Set serveropt 'Bm_sim' to 'disabled'.")
        act_bm_sim_disabled.triggered.connect(
            lambda: self.datapool.set_serveropts_Bm_sim("disabled")
        )
        act_bm_sim_disabled.setCheckable(True)
        menu_tools.addAction(act_bm_sim_disabled)

        act_bm_sim_constant = QAction("Bm_sim - constant", self)
        act_bm_sim_constant.setActionGroup(actgroup_Bm_sim)
        act_bm_sim_constant.setStatusTip("Set serveropt 'Bm_sim' to 'constant'.")
        act_bm_sim_constant.triggered.connect(
            lambda: self.datapool.set_serveropts_Bm_sim("constant")
        )
        act_bm_sim_constant.setCheckable(True)
        menu_tools.addAction(act_bm_sim_constant)

        act_bm_sim_mutate = QAction("Bm_sim - mutate", self)
        act_bm_sim_mutate.setActionGroup(actgroup_Bm_sim)
        act_bm_sim_mutate.setStatusTip("Set serveropt 'Bm_sim' to 'mutate'.")
        act_bm_sim_mutate.triggered.connect(
            lambda: self.datapool.set_serveropts_Bm_sim("mutate")
        )
        act_bm_sim_mutate.setCheckable(True)
        menu_tools.addAction(act_bm_sim_mutate)

        act_bm_sim_feedback = QAction("Bm_sim - feedback", self)
        act_bm_sim_feedback.setActionGroup(actgroup_Bm_sim)
        act_bm_sim_feedback.setStatusTip("Set serveropt 'Bm_sim' to 'feedback'.")
        act_bm_sim_feedback.triggered.connect(
            lambda: self.datapool.set_serveropts_Bm_sim("feedback")
        )
        act_bm_sim_feedback.setCheckable(True)
        menu_tools.addAction(act_bm_sim_feedback)

        act_bm_sim_disabled.setChecked(True)

        menu_tools.addSeparator()

        # # TODO DELETE
        # act_toggle_loopback = QAction(
        #     QIcon("./assets/icons/feather/repeat.svg"),
        #     "Toggle loopback", self)
        # act_toggle_loopback.setStatusTip("Toggle server option 'loopback'.")
        # act_toggle_loopback.triggered.connect(self.datapool.serveropts_toggle_loopback)
        # act_toggle_loopback.setCheckable(True)
        # menu_tools.addAction(act_toggle_loopback)


        # act_screenshot = QAction(
        #     QIcon(QPixmap(":camera")),
        #     "Take a &Screenshot", self)
        # act_screenshot.setStatusTip("Take a screenshot")
        # # act_screenshot.triggered.connect()
        # act_screenshot.setCheckable(False)
        # # act_screenshot.setShortcut(QKeySequence("Ctrl+s"))
        #
        # menu_tools.addAction(act_screenshot)

        return menubar

    def create_tabbar(self):
        """
        Creates the tabbar, a QToolBar that allows the user to navigate
         between the different tabs of the CentralWidget.

        Returns a QToolBar object
        """
        tabbar = QToolBar()
        tabbar.setMovable(False)
        tabbar.setIconSize(QSize(36, 36))

        # First create a new list:
        self.tabactions = []

        for i, attrs in self.config["tab_dict"].items():
            # Create a new action for each entry in tab dict
            self.tabactions.append(
                QAction(  # noqa
                    QIcon(QPixmap(attrs["icon"])),
                    attrs["name"],
                    self,
                    checkable=attrs["checkable"]
                )
            )
            # Connect each created item to the change_tab() function
            self.tabactions[i].triggered.connect(self.change_tab)
            # Connect the action to the tabbar, so they are visible on the UI
            tabbar.addAction(self.tabactions[i])

            # Artificially create a TestTab for each entry and add to the
            #  QStackedWidget object. # TODO: Replace with more useful generation
            if i == 0:
                self.tabcontainer.addWidget(ConnectionWindow(self.config, self.datapool))
            elif i == 1:
                self.tabcontainer.addWidget(CommandWindow(self.config, self.datapool))
            elif i == 2:
                self.tabcontainer.addWidget(OrbitalWindow(self.config, self.datapool))
            # elif i == 3:
            #     self.tabcontainer.addWidget(OrbitDesignWindow(self.config, self.datapool))
            elif i == 3:
                self.tabcontainer.addWidget(CyclicsWindow(self.config, self.datapool))
            elif i == 4:
                self.tabcontainer.addWidget(WebcamWindow(self.config, self.datapool))
            elif i == 5:
                self.tabcontainer.addWidget(ControlWindow(self.config, self.datapool))
            else:
                self.tabcontainer.addWidget(TestTab(attrs["name"]))

        # Cement the indexing by casting list into tuple
        self.tabactions = tuple(self.tabactions)

        # Set the default tab checked and visible upon startup
        self.tabactions[self.config["default_tab"]].setChecked(True)
        self.tabcontainer.setCurrentIndex(self.config["default_tab"])

        return tabbar

    # @Slot()
    def change_tab(self) -> None:
        """
        Allows navigation of the various "tabs" of the CentralWidget, which
        are really just layered widgets in a QStackedWidget. Whenever a signal
        calls this function, change_tab() figures which tab action the signal
        originated from, set that tab action checked in the tabbar, set all
        others unchecked, and swap to the corresponding tab in the central
        widget.
        """
        # TODO: Currently the checked tabbar item can be clicked again, and be
        # TODO:  de-checked in this way. Fix it so that checked tabbar items
        # TODO:  cannot be unchecked manually.

        # Find the index of the tab action that sent the signal. This index
        # is identical to the index of the desired tab in the QStackedWidget.
        tab_index = self.tabactions.index(self.sender())

        # Set all tab actions unchecked, except for the one just clicked
        for action in self.tabactions:
            if action != self.tabactions[tab_index]:
                action.setChecked(False)

        # Tell the StackedWidget to display the tab with the desired index
        self.tabcontainer.setCurrentIndex(tab_index)
