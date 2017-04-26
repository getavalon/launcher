import sys

from . import model

self = sys.modules[__name__]
self.db = None
self.url = "https://mindbender-assets.firebaseio.com"
self.terminal = None

DEBUG = 1 << 0
INFO = 1 << 1
WARNING = 1 << 2


def init():
    self.terminal = model.Model()


def log(line, level=INFO):
    self.terminal.append(line)
