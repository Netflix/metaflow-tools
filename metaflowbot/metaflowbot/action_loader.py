# we import actions just to execute the action modules,
# so they will get a chance to add themselves to cli.actions
import importlib
import pkgutil

from . import actions


# Code from https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
def iter_namespace(ns_pkg):
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


SUPPORTED_ACTIONS = {}
SUPPORTED_RULES = []
# This module is loaded at Last because the rules
# in basic have Greeting actions wired to opening new-thread
# For this reason we need to ensure that metaflowbot.actions.basic loads last
LAST_LOAD_MODULE = "metaflowbot.actions.basic"

for finder, name, ispkg in iter_namespace(actions):
    if name == LAST_LOAD_MODULE:
        continue
    action_package = importlib.import_module(name)
    action = name
    try:
        # Register the rules here
        assert action_package.RULES is not None
        SUPPORTED_RULES.extend(action_package.RULES)
        SUPPORTED_ACTIONS[action] = action_package
    except AttributeError as e:
        print(
            f"Ignoring import of action {action} since it lacks any associated rules."
        )


SUPPORTED_ACTIONS[LAST_LOAD_MODULE] = importlib.import_module(LAST_LOAD_MODULE)
SUPPORTED_RULES.extend(SUPPORTED_ACTIONS[LAST_LOAD_MODULE].RULES)
