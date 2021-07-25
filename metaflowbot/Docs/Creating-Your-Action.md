# Creating Custom Metaflow Bot Actions

The `metaflowbot.actions` follows [`pkgutil` style Namespace packaging.]((https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages).)

An example of how to implement pkgutil style [subpackage](https://github.com/pypa/sample-namespace-packages/tree/master/pkgutil) can be found here.

### How To Create Your Own Bot Action
Create your custom action with the following folder structure

```
your_bot_action/ # the name of this dir doesn't matter
├ setup.py
├ metaflowbot/ # namespace package name
│  └ __init__.py       # special pkgutil namespace __init__.py
│  └ action/      # namespace sub package name
│      ├__init__.py    # special pkgutil namespace __init__.py
│      └ your-special-acton/            # dir name must match the package name in `setup.py`
│        └ __init__.py  # Contains a prespecified code block given below
│        └ rules.yml.   # This mandatory to create rules
│        └ commands.py. # This create main commands from click
.
```

Every module must contain a `rules.yml`, a `__init__.py`, and a module that contains click commands imported from `metaflowbot.cli.actions`.

The `__init__.py` inside an installable action must contain the following code to integrate with metaflowbot's actions
```python
import pkgutil

from metaflowbot.rules import MFBRules

data = pkgutil.get_data(__name__, "rules.yml")
RULES = MFBRules.make_subpackage_rules(data)
from . import commands
```

## Examples : Jokes Command

- The Jokes command can be installed from [this](../extensions/jokes-command) directory.
- Any custom action needs to follow same folder structure as given in the Jokes Command
- After doing a `pip install` of the `metaflowbot`, you can install the `jokes-command` by doing a `pip install .` in [this](../extensions/jokes-command) directory.
- The [MANIFEST.in](../extensions/jokes-command/MANIFEST.in) helps ensure the `rules.yml` file also present when the action is installed.
