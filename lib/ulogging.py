import sys

import uasyncio
from micropython import const

TRACE = const(1)
DEBUG = const(2)
INFO = const(3)
WARNING = const(4)
ERROR = const(5)
CRITICAL = const(6)

_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    TRACE: "TRACE",
}

_stream = sys.stderr


class Logger:

    def __init__(self, name, live=False):
        from settings import DEBUG

        self.name = name
        self.live = live
        self.state_machine = None
        self.loop = uasyncio.get_event_loop()
        self.level = TRACE if DEBUG else INFO

    def level_str(self, level=None):
        if not level:
            level = self.level

        name = _level_dict.get(level)
        if name is not None:
            return name

        return "LVL%s" % level

    def setLevel(self, level):
        if isinstance(level, str):
            level = globals()[level]

        self.level = level

    def getLevel(self):
        return self.level

    def isEnabledFor(self, level):
        return level >= self.level

    def log(self, level, msg, *args):
        if level >= self.level:
            _stream.write("%s:%s: " % (self.name, self.level_str(level)))

            if args:
                msg = msg % args

            print(msg, file=_stream)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def trace(self, msg, *args):
        self.log(TRACE, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg="Unhandled exception", *args):
        self.error(msg, *args)

        sys.print_exception(e, _stream)

    def exception(self, msg, *args):
        self.exc(sys.exc_info()[1], msg, *args)


logger = Logger("AP")
