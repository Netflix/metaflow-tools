import click
from metaflowbot.cli import action
from metaflowbot.message_templates.templates import BotVersion, IntroMessage
from metaflowbot.state import MFBState


@action.command(help='new_thread')
@click.pass_obj
def new_thread(obj):
    greeting = IntroMessage()
    dm_token = '<@%s>' % obj.sc.bot_user_id()
    intromsg,blocks = greeting.get_slack_message(dm_token)
    obj.reply(intromsg,blocks=blocks)
    obj.publish_state(MFBState.message_new_thread(obj.thread))

@action.command(help='reply')
@click.option('--message',
              required=True,
              help="Reply this message")
@click.pass_obj
def reply(obj, message=None):
    obj.reply(message)


@action.command(help='version')
@click.pass_obj
def version(obj):
    message,blocks = BotVersion().get_slack_message()
    obj.reply(message,blocks=blocks)
