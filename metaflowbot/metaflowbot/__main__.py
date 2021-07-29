import traceback

import click

# `action_loader` needs to be loaded before `cli` because
# it will load all the actions that may have been custom installed.
# Once `action_loader` is loaded, `cli` can safely be loaded;
# We do this because `cli` loads of SUPPORTED_ACTIONS object which needs
# `action_loader` to be loaded first
from . import action_loader, cli
from .exceptions import MFBException


class CliState(object):
    def __init__(self):
        self.token = None
        self.publish_state = None
        self.reply = None
        self.thread = None
        self.sc = None


def main():
    try:
        cli.cli(auto_envvar_prefix="MFB", obj=CliState())
    except cli.MFBException as ex:
        click.secho(ex.headline, fg="white", bold=True)
        if ex.traceback:
            traceback.print_exc()
        else:
            click.secho(ex.msg, fg="red", bold=True)


if __name__ == "__main__":
    main()
