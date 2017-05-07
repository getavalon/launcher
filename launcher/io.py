import os
import sys

from . import model

# Third-party dependencies
import pymongo

self = sys.modules[__name__]
self._collection = None
self.uri = os.getenv("MINDBENDER_MONGO", "mongodb://localhost:27017")
self.terminal = None

DEBUG = 1 << 0
INFO = 1 << 1
WARNING = 1 << 2
ERROR = 1 << 3


def init():
    self.terminal = model.Model([], roles=["line", "level"])

    client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=500)

    try:
        client.server_info()
    except Exception:
        raise IOError("ERROR: Couldn't connect to %s" % self.uri)

    database = client["mindbender"]
    self._collection = database["assets"]

    # Shorthand
    self.find = self._collection.find
    self.find_one = self._collection.find_one
    self.insert_one = self._collection.insert_one
    self.insert_many = self._collection.insert_many
    self.save = self._collection.save


def log(line, level=INFO):
    sys.stdout.write(line + "\n")
    self.terminal.append({
        "line": line,
        "level": level
    })
