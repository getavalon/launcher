"""Application entry-point"""

# Standard library
import os
import sys

# Dependencies
from avalon import io
# import avalon.vendor.qtawesome as qta
from PyQt5 import QtCore, QtGui, QtQml, QtWidgets, QtQuick

# Local libraries
from . import control, terminal, lib

QML_IMPORT_DIR = lib.resource("qml")
APP_PATH = lib.resource("qml", "main.qml")
ICON_PATH = lib.resource("icon", "main.png")


class Application(QtWidgets.QApplication):

    def __init__(self, root, source):
        super(Application, self).__init__(sys.argv)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        engine = QtQml.QQmlApplicationEngine()
        engine.objectCreated.connect(self.on_object_created)
        engine.warnings.connect(self.on_warnings)
        engine.addImportPath(QML_IMPORT_DIR)

        try:
            io.install()
        except IOError:
            raise  # Server refused to connect

        terminal.init()

        controller = control.Controller(root, self)
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("terminal", terminal.model)

        self._tray = None
        self.window = None
        self.engine = engine
        self.controller = controller

        engine.load(QtCore.QUrl.fromLocalFile(source))

        self.setQuitOnLastWindowClosed(False)

    def on_object_created(self, object, url):
        if object is None:
            print("Could not load QML file..")
            sys.exit(1)

        else:
            self.window = object
            self.init_tray()

            self.controller.init()
            print("Success")

    def on_warnings(self, warnings):
        for warning in warnings:
            print(warning.toString())

    def init_tray(self):

        tray = QtWidgets.QSystemTrayIcon(self.windowIcon(), parent=self)
        tray.setToolTip("Avalon Launcher")

        # Build the right-mouse context menu for the tray icon
        menu = QtWidgets.QMenu()
        # icon_color = "#509eff"   # launcher icon color

        def window_show():
            self.window.show()
            self.window.raise_()
            self.window.requestActivate()

        # Disabled icon due to mismatching font versions
        # icon = qta.icon("fa.eye", color=icon_color)
        show = QtWidgets.QAction("Show", self)
        show.triggered.connect(window_show)
        menu.addAction(show)

        def on_quit():
            # fix crash on quit with QML window open
            self.closeAllWindows()

            # fix tray icon remaining visible until hover over
            self._tray.hide()

            self.quit()

        # Disabled icon due to mismatching font versions
        # icon = qta.icon("fa.close", color=icon_color)
        quit = QtWidgets.QAction("Quit", self)
        quit.triggered.connect(on_quit)
        menu.addAction(quit)
        tray.setContextMenu(menu)

        # Add the double clicked behavior
        def on_tray_activated(reason):
            if reason == QtWidgets.QSystemTrayIcon.Context:
                return

            if self.window.isVisible():
                self.window.hide()

            elif reason == QtWidgets.QSystemTrayIcon.Trigger:
                window_show()

        tray.activated.connect(on_tray_activated)

        self._tray = tray

        tray.show()
        tray.showMessage("Avalon", "Launcher tray started.",
                         self.windowIcon(), 500)


def main(root, demo=False):
    """Start the Qt-runtime and show the window"""

    root = os.path.realpath(root)

    print("Starting avalon-launcher")
    app = Application(root, APP_PATH)
    return app.exec_()
