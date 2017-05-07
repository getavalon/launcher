import os
import json
import copy
import errno
import shutil
import getpass
import traceback

from PyQt5 import QtCore

from mindbender import schema
from mindbender.vendor import toml
from . import lib, io, model

Signal = QtCore.pyqtSignal
Slot = QtCore.pyqtSlot
Property = QtCore.pyqtProperty

DEFAULTS = {
    "icon": {
        "project": "map",
        "silo": "database",
        "asset": "plus-square",
        "task": "male",
        "app": "file",
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
                "_id",
                "name",
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

    def launch(self, name):
        """Launch `app`

        Arguments:
            name (str): Name of app

        """

        application_definition = lib.which_app(name)

        if application_definition is None:
            return io.log("%s not found." % name, io.ERROR)

        try:
            with open(application_definition) as f:
                app = toml.load(f)
                io.log(json.dumps(app, indent=4), io.DEBUG)
                schema.validate(app, "application")
        except (schema.ValidationError,
                schema.SchemaError,
                toml.TomlDecodeError) as e:
            io.log("Application definition was invalid.", io.ERROR)
            io.log("%s" % e, io.ERROR)
            return io.log(" - %s" % application_definition, io.ERROR)

        executable = lib.which(app["executable"])

        if executable is None:
            return io.log("%s could not be found." % executable, io.ERROR)

        frame = self.current_frame()
        frame["environment"]["root"] = self._root

        template_private = frame["config"]["template"]["work"]

        try:
            workdir = template_private.format(**dict(
                user=getpass.getuser(),
                app=app["application_dir"],
                **frame["environment"]
            ))

        except KeyError as e:
            return io.log("Missing environment variable: %s" % e, io.ERROR)

        # TODO(marcus): These shouldn't be necessary
        # once the templates are used.
        # ----------------------------------------------------------------------
        template_rootpath = template_private.split("{silo}")[0]
        template_assetpath = template_private.split("{asset}")[0] + "{asset}"
        template_taskpath = template_private.split("{task}")[0] + "{task}"

        silospath = template_rootpath.format(**frame["environment"])
        assetpath = template_assetpath.format(**frame["environment"])
        taskpath = template_taskpath.format(**frame["environment"])

        frame["environment"]["silospath"] = silospath
        frame["environment"]["assetpath"] = assetpath
        frame["environment"]["taskpath"] = taskpath
        frame["environment"]["workdir"] = workdir
        # ----------------------------------------------------------------------

        # TODO(marcus): These will eventually replace the name-based
        # references currently stored in the environment.
        frame["environment"]["_project"] = frame["project"]
        frame["environment"]["_asset"] = frame["asset"]

        environment = os.environ.copy()

        environment = dict(environment, **{
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
            if app["name"] == name
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
            dict({
                "icon": DEFAULTS["icon"]["project"]
            }, **project)

            for project in io.find({"type": "project"})
        ])

        frame = {
            "environment": {
                # Indicate that the launched application was
                # launched using the launcher.
                "projectversion": "2.0",
            },
        }
        self._frames[:] = [frame]

        self.pushed.emit(header)
        self.navigated.emit()

    @Slot(QtCore.QModelIndex)
    def push(self, index):
        name = model.data(index, "name")
        self.breadcrumbs.append(name)

        level = len(self.breadcrumbs)
        handler = {
            1: self.on_project_changed,
            2: self.on_silo_changed,
            3: self.on_asset_changed,
            4: self.on_task_changed,
            5: self.on_app_changed,
        }[level]

        handler(index)
        self.navigated.emit()

    @Slot()
    def pop(self):
        self._frames.pop()
        self._model.pop()

        if not self.breadcrumbs:
            self.popped.emit()
            self.navigated.emit()
            return self.init()

        try:
            self.breadcrumbs.pop()
        except IndexError:
            pass
        else:
            self.popped.emit()
            self.navigated.emit()

    def on_project_changed(self, index):
        name = model.data(index, "name")
        path = os.path.join(self._root, name)

        frame = self.current_frame()
        document = io.find_one({"_id": model.data(index, "_id")})

        assert document is not None

        frame["config"] = {
            "apps": document.get("apps", []),
            "tasks": document.get("tasks", []),
            "template": document.get("template", {})
        }

        self._model.push([
            dict({
                "name": silo,
                "icon": DEFAULTS["icon"]["silo"],
            })
            for silo in ["assets", "film"]
        ])

        frame["project"] = document["_id"]
        frame["environment"]["project"] = name
        frame["environment"]["projectpath"] = path

        self._frames.append(frame)
        self.pushed.emit(name)

    def on_silo_changed(self, index):
        name = model.data(index, "name")
        frame = self.current_frame()

        self._model.push([
            dict({
                "id": str(doc["_id"]),
                "icon": DEFAULTS["icon"]["asset"],
            }, **(doc or {}))
            for doc in sorted(
                io.find({
                    "type": "asset",
                    "parent": frame["project"],
                    "silo": name
                }),

                # Hard-sort by group
                # TODO(marcus): Sorting should really happen in
                # the model, via e.g. a Proxy.
                key=lambda item: (
                    # Sort by group
                    item.get(
                        "group",

                        # Put items without a
                        # group at the top
                        "0"),

                    # Sort inner items by name
                    item["name"]
                )
            )
        ])

        frame["environment"]["silo"] = name

        self._frames.append(frame)
        self.pushed.emit(name)

    def on_asset_changed(self, index):
        name = model.data(index, "name")
        frame = self.current_frame()

        frame["asset"] = model.data(index, "_id")
        frame["environment"]["asset"] = name

        # TODO(marcus): These are going to be accessible
        # from database, not from the environment.
        asset = io.find_one({"_id": frame["asset"]})
        frame["environment"].update({
            key: value
            for key, value in asset.items()
            if key not in (
                "_id",
                "parent",
                "schema",
                "silo",
                "group",
                "asset",
            )
        })

        self._model.push([
            dict({
                "icon": DEFAULTS["icon"]["task"]
            }, **task)
            for task in sorted(
                frame["config"].get("tasks", []),
                key=lambda t: t["name"])
        ])

        self._frames.append(frame)
        self.pushed.emit(name)

    def on_task_changed(self, index):
        name = model.data(index, "name")

        frame = self.current_frame()
        self._model.push([
            dict({
                "name": app["name"],
                "icon": DEFAULTS["icon"]["app"]
            }, **app)
            for app in sorted(
                frame["config"].get("apps", []),
                key=lambda a: a["name"])
        ])

        frame["environment"]["task"] = name

        self._frames.append(frame)
        self.pushed.emit(name)

    def on_app_changed(self, index):
        """Launch application on clicking it"""
        name = model.data(index, "name")
        self.launch(name)
        self.breadcrumbs.pop()


def dirs(root):
    try:
        base, dirs, files = next(os.walk(root))
    except (IOError, StopIteration):
        # Ignore non-existing dirs
        return list()

    return dirs
