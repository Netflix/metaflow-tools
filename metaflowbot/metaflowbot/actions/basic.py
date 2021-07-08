import click

from ..cli import action
from ..message_templates.templates import IntroMessage
from ..state import MFBState


@action.command(help='new_thread')
@click.option('--greeting',
              required=True,
              help="Greeting message")
@click.pass_obj
def new_thread(obj, greeting=None):
    greeting = IntroMessage()
    dm_token = '<@%s>' % obj.sc.bot_user_id()
    obj.reply('',blocks=greeting.get_slack_message(dm_token))
    obj.publish_state(MFBState.message_new_thread(obj.thread))

@action.command(help='reply')
@click.option('--message',
              required=True,
              help="Reply this message")
@click.pass_obj
def reply(obj, message=None):
    obj.reply(message)
