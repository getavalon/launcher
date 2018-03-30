import sys


self = sys.modules[__name__]
self._is_installed = False


def install():
    """Register actions"""

    if self._is_installed:
        return

    from .actions import register_config_actions, register_default_actions

    print("Registering default actions..")
    register_default_actions()
    print("Registering config actions..")
    register_config_actions()

    self._is_installed = True
