import traceback

import click

from metaflowbot.cli import action
from metaflowbot.message_templates.templates import (DEFAULT_ERROR_MESSAGE,
                                                     BotVersion, IntroMessage,
                                                     error_message)
from metaflowbot.state import MFBState


@action.command(help="new_thread")
@click.option("--create-thread/--no-create-thread", help="Will create a new thread")
@click.pass_obj
def new_thread(obj, create_thread=False):
    try:
        if create_thread:
            obj.publish_state(MFBState.message_new_thread(obj.thread))
        greeting = IntroMessage()
        dm_token = "<@%s>" % obj.sc.bot_user_id()
        intromsg, blocks = greeting.get_slack_message(dm_token)
        obj.reply(intromsg, blocks=blocks)
    except:
        traceback.print_exc()
        my_traceback = traceback.format_exc()
        obj.reply(DEFAULT_ERROR_MESSAGE, **error_message(my_traceback))


@action.command(help="reply")
@click.option("--message", required=True, help="Reply this message")
@click.pass_obj
def reply(obj, message=None):
    obj.reply(message)


@action.command(help="version")
@click.option("--create-thread/--no-create-thread", help="Will create a new thread")
@click.pass_obj
def version(obj, create_thread=False):
    try:
        if create_thread:
            obj.publish_state(MFBState.message_new_thread(obj.thread))
        message = BotVersion().get_slack_message()
        obj.reply(message)
    except:
        traceback.print_exc()
        my_traceback = traceback.format_exc()
        obj.reply(DEFAULT_ERROR_MESSAGE, **error_message(my_traceback))
