import os
import json
import copy
import errno
import shutil
import getpass
import traceback

from PyQt5 import QtCore

from . import lib, io, schema, model
from .vendor import yaml

Signal = QtCore.pyqtSignal
Slot = QtCore.pyqtSlot
Property = QtCore.pyqtProperty

DEFAULTS = {
    "icon": {
        "project": lib.resource("icon", "project.png"),
        "silo": lib.resource("icon", "silo.png"),
        "asset": lib.resource("icon", "asset.png"),
        "task": lib.resource("icon", "task.png"),
        "app": lib.resource("icon", "app.png"),
    },
    "config": {
        "schema": "mindbender-core:config-1.0",
        "apps": [
            {
                "name": "python",
                "args": [
                    "-u", "-c",
                    "print('Default Python does nothing')"
                ]
            }
        ],
        "tasks": [{"name": "default"}],
        "template": {
            "publish": "{projectpath}/publish",
            "work": "{projectpath}/work"
        }
    },
    "inventory": {
        "schema": "mindbender-core:inventory-1.0",

        "assets": {
            "Default asset 1": None,
            "Default asset 2": None,
        },
        "film": {
            "Default shot 1": {
                "edit_in": 1000,
                "edit_out": 1143
            },
            "Default shot 2": {
                "edit_in": 1000,
                "edit_out": 1081
            },
        }
    }
}


class Controller(QtCore.QObject):
    # An item was clicked, causing an environment change
    #
    # Arguments:
    #   label (str): The visual name of the item
    #
    pushed = Signal(str, arguments=["label"])

    # The back button was pressed
    popped = Signal()

    # The hierarchy was navigated, either forwards or backwards
    navigated = Signal()

    def __init__(self, root, parent=None):
        super(Controller, self).__init__(parent)

        self._root = root
        self._breadcrumbs = list()
        self._processes = list()
        self._model = model.Model(
            items=[],
            roles=[
                "label",
                "icon",
                "group"
            ])

        # A "frame" contains the environment at a given point
        # in the asset hierarchy. For example, browsing all the
        # way to an application yields a fully qualified frame
        # usable when launching an application.
        # The current frame is visualised by the Terminal in the GUI.
        self._frames = list()

    def launch(self, label):
        """Launch `app`

        Arguments:
            label (str): Name of app

        """

        application_definition = lib.which_app(label)

        if application_definition is None:
            return io.log("%s not found." % label, io.ERROR)

        with open(application_definition) as f:
            app = yaml.load(f)
            io.log(json.dumps(app, indent=4), io.DEBUG)
            schema.validate(app, "application")

        executable = lib.which(app["executable"])

        if executable is None:
            return io.log("%s could not be found." % executable, io.ERROR)

        frame = self.current_frame()

        template_private = frame["config"]["template"]["work"]

        try:
            workdir = template_private.format(**dict(
                user=getpass.getuser(),
                app=app["application_dir"],
                **frame["environment"]
            ))

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
            "MINDBENDER_" + key.upper(): str(value)
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
                # Treat list values as application_definition variables
                environment[key] = os.pathsep.join(value)

            elif isinstance(value, str):
                environment[key] = value

            else:
                io.log("Unsupported environment variable in %s"
                       % application_definition, io.ERROR)

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
            dst = os.path.join(workdir, dst)

            try:
                io.log("Copying %s -> %s" % (src, dst))
                shutil.copy(src, dst)
            except OSError as e:
                io.log("Could not copy application file: %s" % e, io.ERROR)
                io.log(" - %s -> %s" % (src, dst), io.ERROR)

        item = next(
            app for app in frame["config"]["apps"]
            if app["name"] == label
        )
        args = item.get("args", []) + app.get("arguments", [])

        try:
            popen = lib.launch(
                executable=executable,
                args=args,
                environment=environment,
            )
        except ValueError:
            return io.log(traceback.format_exc())

        except OSError:
            return io.log(traceback.format_exc())

        except Exception as e:
            io.log("Something unexpected happened..")
            return io.log(traceback.format_exc())

        else:
            io.log(json.dumps(environment, indent=4, sort_keys=True), io.DEBUG)
            io.log("Launching {executable} {args}".format(
                executable=executable,
                args=" ".join(args))
            )

        process = {}

        class Thread(QtCore.QThread):
            messaged = Signal(str)

            def run(self):
                for line in lib.stream(process["popen"].stdout):
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

    def current_frame(self):
        """Shorthand for the current frame"""
        try:
            # Nested dictionaries require deep copying.
            return copy.deepcopy(self._frames[-1])

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

    @Property(model.Model, notify=navigated)
    def model(self):
        return self._model

    def init(self):
        header = "Root"

        self._model.push([
            {
                "label": project,
                "icon": DEFAULTS["icon"]["project"]
            } for project in dirs(self._root)
        ])

        frame = {
            "environment": {
                # Indicate that the launched application was
                # launched using the launcher.
                "with_launcher": "True"
            },
        }
        self._frames[:] = [frame]

        self.pushed.emit(header)
        self.navigated.emit()

    @Slot(str)
    def push(self, breadcrumb):
        self.breadcrumbs.append(breadcrumb)

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
        self._model.pop()

        try:
            self.breadcrumbs.pop()
        except IndexError:
            pass
        else:
            self.popped.emit()
            self.navigated.emit()

    def on_project_changed(self, label):
        path = os.path.join(self._root, label)
        configpath = os.path.join(path, ".config.yml")
        inventorypath = os.path.join(path, ".inventory.yml")

        try:
            with open(configpath) as f:
                config = yaml.load(f)
                schema.validate(config, "config")
        except IOError:
            config = DEFAULTS["config"]
        except (schema.ValidationError, schema.SchemaError):
            return io.log("%s has been misconfigured, "
                          "speak to your supervisor."
                          % configpath, io.ERROR)

        try:
            with open(inventorypath) as f:
                inventory = yaml.load(f)
                schema.validate(config, "inventory")
        except IOError:
            inventory = DEFAULTS["inventory"]
        except (schema.ValidationError, schema.SchemaError):
            return io.log("%s has been misconfigured, "
                          "speak to your supervisor."
                          % inventorypath, io.ERROR)

        frame = self.current_frame()
        frame["config"] = config
        frame["inventory"] = inventory

        self._model.push([
            {
                "label": key,
                "icon": DEFAULTS["icon"]["silo"]
            }
            for key in sorted(inventory)
            if key != "schema"
        ])

        frame["environment"]["project"] = label
        frame["environment"]["projectpath"] = path

        # Install optional metadata
        # TODO(marcus): Once ls() has been adapted to use the inventory,
        # data will be fetched not from the environment, but from there.
        frame["environment"].update(config.get("metadata", {}))

        self._frames.append(frame)
        self.pushed.emit(label)

    def on_silo_changed(self, label):
        frame = self.current_frame()

        self._model.push([
            dict({
                "label": key,
                "icon": DEFAULTS["icon"]["asset"],
            }, **(value or {}))
            for key, value in sorted(frame["inventory"][label].items())
        ])

        frame["environment"]["silo"] = label

        self._frames.append(frame)
        self.pushed.emit(label)

    def on_asset_changed(self, label):
        frame = self.current_frame()

        self._model.push([
            dict({
                "label": task.get("label", task["name"]),
                "icon": DEFAULTS["icon"]["task"]
            }, **task)
            for task in sorted(
                frame["config"].get("tasks", []),
                key=lambda t: t["name"])
        ])

        silo = frame["environment"]["silo"]
        metadata = frame["inventory"][silo][label]
        frame["environment"]["asset"] = label
        frame["environment"].update((metadata or {}).items())

        self._frames.append(frame)
        self.pushed.emit(label)

    def on_task_changed(self, label):

        frame = self.current_frame()
        self._model.push([
            dict({
                "label": app["name"],
                "icon": DEFAULTS["icon"]["app"]
            }, **app)
            for app in sorted(
                frame["config"].get("apps", []),
                key=lambda a: a["name"])
        ])

        frame["environment"]["task"] = label

        self._frames.append(frame)
        self.pushed.emit(label)

    def on_app_changed(self, label):
        """Launch application on clicking it"""
        self.launch(label)
        self.breadcrumbs.pop()


def dirs(root):
    try:
        base, dirs, files = next(os.walk(root))
    except (IOError, StopIteration):
        # Ignore non-existing dirs
        return list()

    return dirs
