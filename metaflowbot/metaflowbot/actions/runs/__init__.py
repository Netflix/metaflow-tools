import pkgutil

from metaflowbot.rules import MFBRules

data = pkgutil.get_data(__name__, "rules.yml")
RULES = MFBRules.make_subpackage_rules(data)
from . import commands
