import sys

from .actions import register_config_actions, register_default_actions

self = sys.modules[__name__]
self._is_installed = False


def install():
    """Register all actions"""

    print("Registering actions ..")
    register_default_actions()
    register_config_actions()

    print("Registered actions")
    self._is_installed = True


if self._is_installed is False:
    install()
