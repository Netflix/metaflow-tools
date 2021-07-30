import pkgutil

# This is the template for creating Commands and Rules
from metaflowbot.rules import MFBRules

from . import commands

data = pkgutil.get_data(__name__, "rules.yml")
RULES = MFBRules.make_subpackage_rules(data)
# In order for click to register commands we need
# the package should have a relative import in the __init__.py file
