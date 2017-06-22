import os
import sys
import shutil
import tempfile

from launcher import schema
from launcher.vendor import yaml

self = sys.modules[__name__]


def setup():
    self.root = tempfile.mkdtemp()

    self.config = {
        "schema": "avalon-core:config-1.0",
        "apps": [
            {
                "name": "maya2016"
            },
            {
                "name": "python",
                "args": [
                    "-u",
                    "-c",
                    "print('Something nice')"
                ]
            }
        ],
        "tasks": [
            {
                "label": "animation",
                "name": "animation"
            }
        ],
        "template": {
            "publish": "{projectpath}/publish",
            "work": "{projectpath}/work"
        }
    }

    self.inventory = {
        "schema": "avalon-core:inventory-1.0",

        "assets": {
            "Batman": None,
            "Tarantula": None
        },
        "film": {
            "1000": {
                "edit_in": 1000,
                "edit_out": 1143
            },
            "1200": {
                "edit_in": 1000,
                "edit_out": 1081
            },
            "2000": None,
            "2100": None,
            "2400": None
        }
    }

    self.application = {
        "schema": "avalon-core:application-1.0",
        "label": "Autodesk Maya 2016x64",
        "description": "",
        "application_dir": "maya",
        "executable": "maya2016",
        "default_dirs": [
            "scenes",
            "data",
        ],
        "environment": {
            "MAYA_DISABLE_CLIC_IPM": "Yes",
            "PYTHONPATH": [
                "{PYBLISH_MAYA}/pyblish_maya/pythonpath",
                "{AVALON_CORE}/avalon/maya/pythonpath",
                "{PYTHONPATH}"
            ]
        },
        "arguments": [
            "-proj",
            "{AVALON_WORKDIR}"
        ],
        "copy": {
            "{AVALON_CORE}/res/workspace.mel":
                "{AVALON_WORKDIR}/workspace.mel"
        }
    }

    os.environ["PATH"] += os.pathsep.join([
        os.environ["PATH"],
        self.root
    ])

    with open(os.path.join(self.root, "python.yml"), "w") as f:
        yaml.dump({
            "executable": "python",
            "application_dir": "python",
            "label": "Python 2.7"
        }, f)


def teardown():
    shutil.rmtree(self.root)


def test_config():
    schema.validate(self.config, "config")


def test_inventory():
    schema.validate(self.inventory, "inventory")


def test_application():
    schema.validate(self.application, "application")
