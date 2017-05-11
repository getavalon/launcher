import sys

from .model import Model

self = sys.modules[__name__]
self.model = None

DEBUG = 1 << 0
INFO = 1 << 1
WARNING = 1 << 2
ERROR = 1 << 3


def init():
    self.model = Model([], roles=["line", "level"])


def log(line, level=INFO):
    sys.stdout.write(line + "\n")
    self.model.append({
        "line": line,
        "level": level
    })
