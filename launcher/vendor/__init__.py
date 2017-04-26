import sys

PYTHON = sys.version_info[0]  # e.g. 2 or 3

if PYTHON == 2:
    from ._py2 import *

if PYTHON == 3:
    from ._py3 import *


__all__ = [
    "yaml"
]
