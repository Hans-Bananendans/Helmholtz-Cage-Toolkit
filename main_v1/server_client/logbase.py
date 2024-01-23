from time import time
from datetime import datetime

class LogBase:
    """A small base class that features a logging function.

    It assumes that any derived class imports a config file. To run correctly,
    this function reserves the following two config entries, and MUST have
    these specified as self._config in order to work correctly.

    config = {
        "verbosity": 0,
        "verbosity_printtimestamp": False,
    }

    """

    def log(self,
            verbosity_level: int,
            string: str,
            end: str = "\n",
            sep=" ",
            pts: bool = None):
        """Prints string to console when verbosity is above a certain level"""

        # Specifying 'pts' overrides the default behaviour specified by the config
        # For example, if you set config["verbosity_timestamp"] to True, every
        # call of log() will print the timestamp, unless you use log(..., pts=False)
        if pts is None:
            pts = self._config["verbosity_printtimestamp"]
        if pts:
            print(f"[{self._ts()}]", end=" ")

        if verbosity_level <= self._config["verbosity"]:
            print(string, end=end, sep=sep)


    def _ts(self):
        """Generates a TimeStamp string. This is the default implementation.

        The idea is that you can override self._ts() in your derived classes,
        should you need to.
        """
        return datetime.today()