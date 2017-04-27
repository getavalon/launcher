import os
import sys
import json
import errno
import shutil
import getpass
import traceback
import subprocess

from PyQt5 import QtCore, QtQml

from . import lib, io
from .vendor import six, yaml

Signal = QtCore.pyqtSignal
Slot = QtCore.pyqtSlot
Property = QtCore.pyqtProperty

module = sys.modules[__name__]
module._current_task = None
module._icons = {
    "defaultProject": lib.resource("icon", "project.png"),
    "defaultSilo": lib.resource("icon", "silo.png"),
    "defaultAsset": lib.resource("icon", "asset.png"),
    "defaultTask": lib.resource("icon", "task.png"),
    "defaultApp": lib.resource("icon", "app.png"),
}


class Controller(QtCore.QObject):
    pushed = Signal("QVariant",
                    "QVariant",
                    arguments=["label",
                               "items"])

    popped = Signal()
    navigated = Signal()
    threaded_message = Signal()

    def __init__(self, root, parent=None):
        super(Controller, self).__init__(parent)

        self._root = root
        self._breadcrumbs = list()
        self._processes = list()

        # A "frame" contains the environment at a given point
        # in the asset hierarchy. For example, browsing all the
        # way to an application yields a fully qualified frame
        # usable when launching an application.
        # The current frame is visualised by the Terminal in the GUI.
        self._frames = list()

    def launch(self, item):
        """Launch `app`

        Arguments:
            app (dict): Application from configuration

        """

        application_json = lib.which_app(item["label"])

        if application_json is None:
            return io.log("%s not found." % item["label"], io.ERROR)

        with open(application_json) as f:
            app = json.load(f)

        args = item.get("args", []) + app.get("arguments", [])
        executable = lib.which(app["executable"])

        if executable is None:
            return io.log("%s could not be found." % executable, io.ERROR)

        frame = self.frame.copy()

        template_private = frame["config"]["template"]["private"]

        try:
            workdir = template_private.format(
                projectpath=frame["environment"]["projectpath"],
                silo=frame["environment"]["silo"],
                asset=frame["environment"]["asset"],
                task=frame["environment"]["task"],
                user=getpass.getuser(),
                app=app["application_dir"],
            )

        except KeyError as e:
            return io.log("Missing environment variable: %s" % e, io.ERROR)

        template_rootpath = template_private.split("{silo}")[0]
        template_assetpath = template_private.split("{asset}")[0] + "{asset}"
        template_taskpath = template_private.split("{task}")[0] + "{task}"

        rootpath = template_rootpath.format(**frame["environment"])
        assetpath = template_assetpath.format(**frame["environment"])
        taskpath = template_taskpath.format(**frame["environment"])

        frame["environment"]["root"] = rootpath.replace("/", os.sep)
        frame["environment"]["assetpath"] = assetpath.replace("/", os.sep)
        frame["environment"]["taskpath"] = taskpath.replace("/", os.sep)
        frame["environment"]["workdir"] = workdir.replace("/", os.sep)

        environment = dict(os.environ, **{
            "MINDBENDER_" + key.upper(): value
            for key, value in frame["environment"].items()
        })

        try:
            app = lib.dict_format(app, **environment)
        except KeyError as e:
            io.log("Application error: variable %s "
                   "not found in application .json" % e, io.ERROR)
            io.log(json.dumps(environment, indent=4, sort_keys=True), io.ERROR)
            return io.log("This is typically a bug in the pipeline, "
                          "ask your developer.", io.ERROR)

        for key, value in app.get("environment", {}).items():
            if isinstance(value, list):
                # Treat list values as application_json variables
                environment[key] = os.pathsep.join(value)

            elif isinstance(value, str):
                environment[key] = value

            else:
                io.log("Unsupported environment variable in %s"
                       % application_json, io.ERROR)

        try:
            os.makedirs(workdir)
            io.log("Creating working directory '%s'" % workdir, io.INFO)

        except OSError as e:

            # An already existing working directory is fine.
            if e.errno == errno.EEXIST:
                io.log("Existing working directory found.", io.INFO)

            else:
                io.log("Could not create working directory.", io.ERROR)
                return io.log(traceback.format_exc(), io.ERROR)

        else:
            io.log("Creating default directories..", io.DEBUG)
            for dirname in app.get("default_dirs", []):
                io.log(" - %s" % dirname, io.DEBUG)
                os.makedirs(os.path.join(workdir, dirname))

        # Perform application copy
        for src, dst in app.get("copy", {}).items():
            try:
                shutil.copy(src, dst)
            except OSError as e:
                io.log("Could not copy application file: %s" % e, io.ERROR)
                io.log(" - %s -> %s" % (src, dst), io.ERROR)

        # Asset environment variables
        silo = frame["environment"]["silo"]
        asset = frame["environment"]["asset"]
        for key, value in (frame["inventory"][silo][asset] or {}).items():
            environment["" + key.upper()] = str(value)

        try:
            popen = launch(
                executable=executable,
                args=args,
                environment=environment
            )
        except ValueError:
            return io.log(traceback.format_exc())

        except OSError:
            return io.log(traceback.format_exc())

        except Exception as e:
            io.log("Something unexpected happened..")
            return io.log(traceback.format_exc())

        else:
            io.log("Launching {executable} {args}".format(
                executable=executable,
                args=" ".join(args))
            )

        process = {}

        class Thread(QtCore.QThread):
            messaged = Signal(str)

            def run(self):
                for line in stream(process["popen"].stdout):
                    self.messaged.emit(line.rstrip())
                self.messaged.emit("%s killed." % process["app"]["executable"])

        thread = Thread()
        thread.messaged.connect(lambda line: io.log(line, io.INFO))

        process.update({
            "app": app,
            "thread": thread,
            "popen": popen
        })

        self._processes.append(process)

        thread.start()
        return process

    @property
    def frame(self):
        """Shorthand for the current frame"""
        try:
            return self._frames[-1]
        except IndexError:
            return dict()

    @Property("QVariant", notify=navigated)
    def breadcrumbs(self):
        return self._breadcrumbs

    @Property("QVariant", notify=navigated)
    def environment(self):
        try:
            frame = self._frames[-1]["environment"]
        except (IndexError, KeyError):
            return list()
        else:
            return [
                {"key": key, "value": value}
                for key, value in frame.items()
            ]

    def init(self):
        header = "Root"
        model = [
            {
                "label": project,
                "icon": module._icons["defaultProject"]
            } for project in walk(self._root)
        ]

        frame = dict()
        self._frames[:] = [frame]

        self.pushed.emit(header, model)
        self.navigated.emit()

    @Slot(QtQml.QJSValue)
    def push(self, breadcrumb):
        breadcrumb = dict(breadcrumb.toVariant())

        label = breadcrumb["label"]
        self.breadcrumbs.append(label)

        level = len(self.breadcrumbs)
        handler = {
            1: self.on_project_changed,
            2: self.on_silo_changed,
            3: self.on_asset_changed,
            4: self.on_task_changed,
            5: self.on_app_changed,
        }[level]

        handler(breadcrumb)
        self.navigated.emit()

    @Slot()
    def pop(self):
        self._frames.pop()

        try:
            self.breadcrumbs.pop()
        except IndexError:
            pass
        else:
            self.popped.emit()
            self.navigated.emit()

    def on_project_changed(self, item):
        path = os.path.join(self._root, item["label"])
        configpath = os.path.join(path, ".config.yml")
        inventorypath = os.path.join(path, ".inventory.yml")

        try:
            with open(configpath) as f:
                config = yaml.load(f)
                config.pop("schema")
        except IOError:
            config = dict()

        try:
            with open(inventorypath) as f:
                inventory = yaml.load(f)
                inventory.pop("schema")
        except IOError:
            inventory = dict()

        frame = self.frame.copy()
        frame["config"] = config
        frame["inventory"] = inventory

        model = [
            {
                "label": key,
                "icon": module._icons["defaultSilo"]
            }
            for key in sorted(inventory)
        ]

        frame["environment"] = dict()
        frame["environment"]["project"] = item["label"]
        frame["environment"]["projectpath"] = path

        self._frames.append(frame)
        self.pushed.emit(item, model)

    def on_silo_changed(self, item):
        frame = self.frame.copy()

        model = [
            {
                "label": key,
                "icon": module._icons["defaultAsset"]
            }
            for key in sorted(frame["inventory"][item["label"]])
        ]

        frame["environment"]["silo"] = item["label"]

        self._frames.append(frame)
        self.pushed.emit(item["label"], model)

    def on_asset_changed(self, item):
        frame = self.frame.copy()

        model = [
            dict({
                "label": task["name"],
                "icon": module._icons["defaultTask"]
            }, **task)
            for task in sorted(
                frame["config"].get("tasks", []),
                key=lambda t: t["name"])
        ]

        frame["environment"]["asset"] = item["label"]

        self._frames.append(frame)
        self.pushed.emit(item["label"], model)

    def on_task_changed(self, item):

        frame = self.frame.copy()
        model = [
            dict({
                "label": app["name"],
                "icon": module._icons["defaultApp"]
            }, **app)
            for app in sorted(
                frame["config"].get("apps", []),
                key=lambda a: a["name"])
        ]

        frame["environment"]["task"] = item["label"]

        self._frames.append(frame)
        self.pushed.emit(item["label"], model)

    def on_app_changed(self, item):
        """Launch application on clicking it"""
        self.launch(item)
        self.breadcrumbs.pop()


def _byteify(data):
    """Convert unicode to bytes"""

    # Unicode
    if isinstance(data, six.text_type):
        return data.encode("utf-8")

    # Members of lists
    if isinstance(data, list):
        return [_byteify(item) for item in data]

    # Members of dicts
    if isinstance(data, dict):
        return {
            _byteify(key): _byteify(value) for key, value in data.items()
        }

    # Anything else, return the original form
    return data


def schedule(task, delay=10):
    """Delay execution of `task` by `delay` milliseconds

    As opposed to a plain `QTimer.singleShot`, this will also
    ensure that only one task is ever queued at any one time.

    """

    try:
        module._current_task.stop()
    except AttributeError:
        # No task currently running
        pass

    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(task)
    timer.start(delay)

    module._current_task = timer


def walk(root):
    try:
        base, dirs, files = next(os.walk(root))
    except (IOError, StopIteration):
        # Ignore non-existing dirs
        return list()

    return dirs


def launch(executable, args=None, environment=None):
    """Launch a new subprocess of `args`

    Arguments:
        executable (str): Relative or absolute path to executable
        args (list): Command passed to `subprocess.Popen`
        environment (dict, optional): Custom environment passed
            to Popen instance.

    Returns:
        Popen instance of newly spawned process

    Exceptions:
        OSError on internal error
        ValueError on `executable` not found

    """

    CREATE_NO_WINDOW = 0x08000000
    IS_WIN32 = sys.platform == "win32"

    abspath = executable

    kwargs = dict(
        args=[abspath] + args or list(),
        env=environment or os.environ,

        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,

        # Output `str` through stdout on Python 2 and 3
        universal_newlines=True,

        shell=True
    )

    if IS_WIN32:
        kwargs["creationflags"] = CREATE_NO_WINDOW

    popen = subprocess.Popen(**kwargs)

    return popen


def stream(stream):
    for line in iter(stream.readline, ""):
        yield line
