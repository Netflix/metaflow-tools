import traceback

import click

from . import cli
from .exceptions import MFBException


class CliState(object):
    def __init__(self):
        self.token = None
        self.publish_state = None
        self.reply = None
        self.thread = None
        self.sc = None

try:
    cli.cli(auto_envvar_prefix='MFB',
            obj=CliState())
except cli.MFBException as ex:
    click.secho(ex.headline, fg='white', bold=True)
    if ex.traceback:
        traceback.print_exc()
    else:
        click.secho(ex.msg, fg='red', bold=True)
