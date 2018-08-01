"""Pyblish QML command-line interface"""

import os
import sys
import argparse

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def cli():
    # Check environment dependencies
    missing = list()
    environment_dependencies = (
        "AVALON_CONFIG",
        "AVALON_PROJECTS"
    )

    for dependency in environment_dependencies:
        if dependency not in os.environ:
            missing.append(dependency)

    if missing:
        sys.stderr.write(
            "Incomplete environment, missing variables:\n%s"
            % "\n".join("- %s" % var for var in missing)
        )

        return EXIT_FAILURE

    # Check modules dependencies
    missing = []
    dependencies = {
        "PyQt5": None, "avalon": None
    }
    for dependency in dependencies:
        try:
            lib = __import__(dependency)
        except ImportError:
            missing.append(dependency)
        finally:
            dependencies[dependency] = lib

    if missing:
        sys.stderr.write(
            "Missing modules:\n{0}\nPlease check your PYTHONPATH:\n{1}".format(
                "\n".join("- %s" % var for var in missing),
                os.environ["PYTHONPATH"]
            )
        )

        return EXIT_FAILURE

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--root", default=os.environ["AVALON_PROJECTS"])

    kwargs = parser.parse_args()

    # Fulfill schema, and expect the application
    # to fill it in in due course.
    for placeholder in ("AVALON_PROJECT",
                        "AVALON_ASSET",
                        "AVALON_SILO",
                        "AVALON_TASK",
                        "AVALON_APP",):
        os.environ[placeholder] = "placeholder"

    print("Using Python @ '%s'" % sys.executable)
    print("Using root @ '%s'" % kwargs.root)
    print("Using config: '%s'" % os.environ["AVALON_CONFIG"])

    dependencies["launcher"] = sys.modules[__name__]
    for dependency, lib in dependencies.items():
        print("Using {0} @ '{1}'".format(
            dependency, os.path.dirname(lib.__file__))
        )

    from . import app
    return app.main(**kwargs.__dict__)


sys.exit(cli())
