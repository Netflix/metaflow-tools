import pkgutil

# This is the Template to write and expose Comands and rules
# This can now be transformed into a framework.
from metaflowbot.rules import MFBRules

from . import commands

data = pkgutil.get_data(__name__, "rules.yml")
RULES = MFBRules.make_subpackage_rules(data)
# In order for click to register commands we need
# the package to have a relative import in thee __init__.py file
