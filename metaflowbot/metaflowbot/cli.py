import os
import time
from datetime import datetime

import click

from .action_loader import SUPPORTED_ACTIONS
from .exceptions import MFBException
from .rules import MFBRules
from .server import MFBServer, StateNotFound
from .slack_client import MFBSlackClientV2

LOGGER_TIMESTAMP = "magenta"
LOGGER_COLOR = "green"
LOGGER_BAD_COLOR = "red"


def logger(body="", system_msg=False, head="", bad=False, timestamp=True):
    if timestamp:
        tstamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        click.secho(tstamp + " ", fg=LOGGER_TIMESTAMP, nl=False)
    if head:
        click.secho(head, fg=LOGGER_COLOR, nl=False)
    click.secho(body, bold=system_msg, fg=LOGGER_BAD_COLOR if bad else None)


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Debug mode: Print to stdout instead of sending to Slack",
)
@click.option(
    "--slack-bot-token",
    envvar="SLACK_BOT_TOKEN",
    help="Bot token to make web API calls to Slack.",
)
@click.option(
    "--slack-app-token",
    envvar="SLACK_APP_TOKEN",
    help="App token to make a socket connection to Slack.",
)
@click.option("--admin-thread", help="Admin thread for actions (do not set manually)")
@click.option("--reply-thread", help="Reply thread for actions (do not set manually)")
@click.pass_obj
def cli(
    obj,
    debug=False,
    slack_bot_token=None,
    slack_app_token=None,
    admin_thread=None,
    reply_thread=None,
):
    obj.sc = MFBSlackClientV2(slack_bot_token, slack_app_token=slack_app_token)
    if debug:
        obj.publish_state = lambda msg: logger(msg, head="[debug state] ")
        obj.reply = lambda msg: logger(msg, head="[debug reply] ")
    else:
        if admin_thread:
            obj.publish_state = lambda msg: obj.sc.post_message(
                msg, *admin_thread.split(":")
            )

        if reply_thread:
            obj.thread = reply_thread
            channel, thread_ts = reply_thread.split(":")
            obj.reply = lambda msg, attachments=None, blocks=None: obj.sc.post_message(
                msg, channel, thread_ts, attachments=attachments, blocks=blocks
            )


@cli.command(help="Start the Metaflow bot server.")
@click.option(
    "--admin",
    required=True,
    help="Email of the admin user (used to idenify the admin " "Slack account).",
)
@click.option(
    "--new-admin-thread",
    is_flag=True,
    default=False,
    help="Initialize a new admin thread in a DM between "
    "@metaflow and the admin user.",
)
@click.option(
    "--load-state/--no-load-state",
    default=True,
    show_default=True,
    help="Reconstruct state based on the admin channel.",
)
@click.option(
    "--action-user",
    default="nobody",
    show_default=True,
    help="If the server is run as root, sudo to this user "
    "for all actions, to prevent system-wide side-effects.",
)
@click.pass_obj
def server(obj, admin=None, new_admin_thread=False, load_state=None, action_user=None):
    def log(msg="", **kwargs):
        logger(msg, system_msg=True, **kwargs)

    if os.getuid() != 0:
        action_user = None
    spaces = "\n\t\t\t"
    modules = spaces.join(SUPPORTED_ACTIONS.keys())
    modules_message = f"Discovered the following actions :{spaces}{modules}"
    log(modules_message)
    rules_obj = MFBRules()
    log("Loaded %d rules" % (len(rules_obj)))

    server = MFBServer(obj.sc, admin, rules_obj, logger, action_user)
    if new_admin_thread:
        server.new_admin_thread()
        log("Started a new admin thread.")

    if load_state:
        log("Starting to load previous state..")
        try:
            server.reconstruct_state()
        except StateNotFound as e:
            log("Previous state was not found. "
                "Making new admin thread")
            server.new_admin_thread()
            time.sleep(2)
            server.reconstruct_state()
        except:
            raise
        log("State reconstructed.")
    log(head="Activating the bot..")
    server.loop_forever()


@cli.group(help="Bot actions")
@click.pass_obj
def action(ctx):
    pass
