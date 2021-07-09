# we import actions just to execute the action modules,
# so they will get a chance to add themselves to cli.actions
from . import actions
from .version import __version__
