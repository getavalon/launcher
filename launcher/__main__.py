"""Pyblish QML command-line interface"""

import os
import sys
import argparse
import PyQt5

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def cli():
    # External Dependencies
    missing = list()
    dependencies = (
        "PYBLISH_BASE",
        "PYBLISH_QML",
        "AVALON_CONFIG",
        "AVALON_PROJECTS",
        "AVALON_CORE",
    )

    for dependency in dependencies:
        if dependency not in os.environ:
            missing.append(dependency)

    if missing:
        sys.stderr.write(
            "Incomplete environment, missing variables:\n%s"
            % "\n".join("- %s" % var for var in missing)
        )

        return EXIT_FAILURE

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--root", default=os.environ["AVALON_PROJECTS"])

    kwargs = parser.parse_args()

    # Take advantage of the fact that the Launcher requires a Python
    # distribution with PyQt5 readily available.
    for key, value in (("PYBLISH_QML_PYQT5", os.path.dirname(PyQt5.__file__)),
                       ("PYBLISH_QML_PYTHON_EXECUTABLE", sys.executable)):

        # But only if it hasn't already been set by the user, in which
        # case we assume that is the desired one.
        if key in os.environ:
            continue

        os.environ[key] = value

    # Set PYTHONPATH
    os.environ["PYTHONPATH"] = os.pathsep.join(
        os.environ.get("PYTHONPATH", "").split(os.pathsep) +
        [os.getenv(dependency) for dependency in dependencies]
    )

    # Fulfill schema, and expect the application
    # to fill it in in due course.
    for placeholder in ("AVALON_PROJECT",
                        "AVALON_ASSET",
                        "AVALON_SILO",
                        "AVALON_TASK",
                        "AVALON_APP",):
        os.environ[placeholder] = "placeholder"

    # Expose dependencies to Launcher
    sys.path[:] = [
        os.getenv(dep) for dep in dependencies
    ] + sys.path

    print("Using Python @ '%s'" % sys.executable)
    print("Using PyQt5 @ '%s'" % os.environ["PYBLISH_QML_PYQT5"])
    print("Using core @ '%s'" % os.getenv("AVALON_CORE"))
    print("Using launcher @ '%s'" % os.getenv("AVALON_LAUNCHER"))
    print("Using root @ '%s'" % kwargs.root)
    print("Using config: '%s'" % os.environ.get("AVALON_CONFIG",
                                                "Set by project"))

    from . import app
    return app.main(**kwargs.__dict__)


sys.exit(cli())
