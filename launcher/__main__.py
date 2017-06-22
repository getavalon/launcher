"""Pyblish QML command-line interface"""

import os
import sys
import argparse

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--root", default=os.getcwd())

    kwargs = parser.parse_args()

    # External Dependencies
    missing = list()
    dependencies = (
        "PYBLISH_BASE",
        "PYBLISH_QML",
        "AVALON_CONFIG",
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

    # Set PYTHONPATH
    os.environ["PYTHONPATH"] = os.pathsep.join(
        os.environ.get("PYTHONPATH", "").split(os.pathsep) +
        [os.getenv(dependency) for dependency in dependencies]
    )

    # Expose dependencies to Launcher
    sys.path[:] = [
        os.getenv(dep) for dep in dependencies
    ] + sys.path

    from . import app
    return app.main(**kwargs.__dict__)


sys.exit(cli())
