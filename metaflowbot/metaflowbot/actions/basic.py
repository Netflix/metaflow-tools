import click

from ..cli import action
from ..state import MFBState

@action.command(help='channel_info')
@click.option('--channel',
              required=True,
              help="Channel to request info for")
@click.pass_obj
def channel_info(obj, channel=None):
    info = obj.sc.channel_info(channel)
    obj.publish_state(MFBState.message_channel_info(channel, info['name']))

@action.command(help='user_info')
@click.option('--user',
              required=True,
              help="User to request info for")
@click.pass_obj
def user_info(obj, user=None):
    info = obj.sc.user_info(user)
    obj.publish_state(MFBState.message_user_info(user, info['name']))

@action.command(help='new_thread')
@click.option('--greeting',
              required=True,
              help="Greeting message")
@click.pass_obj
def new_thread(obj, greeting=None):
    obj.reply(greeting)
    obj.publish_state(MFBState.message_new_thread(obj.thread))

@action.command(help='reply')
@click.option('--message',
              required=True,
              help="Reply this message")
@click.pass_obj
def reply(obj, message=None):
    obj.reply(message)
