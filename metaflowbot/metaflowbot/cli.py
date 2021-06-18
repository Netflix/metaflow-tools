import sys
import os
from datetime import datetime

import click

from .slack_client import MFBSlackClient
from .exceptions import MFBException
from .server import MFBServer
from .rules import MFBRules

DEFAULT_RULES = os.path.join(os.path.dirname(__file__),
                             'metaflowbot_rules.yaml')

LOGGER_TIMESTAMP = 'magenta'
LOGGER_COLOR = 'green'
LOGGER_BAD_COLOR = 'red'

def logger(body='', system_msg=False, head='', bad=False, timestamp=True):
    if timestamp:
        tstamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        click.secho(tstamp + ' ', fg=LOGGER_TIMESTAMP, nl=False)
    if head:
        click.secho(head, fg=LOGGER_COLOR, nl=False)
    click.secho(body,
                bold=system_msg,
                fg=LOGGER_BAD_COLOR if bad else None)

# TODO : Change the layer'd CLI here with the modified Slack client.
@click.group()
@click.option('--debug',
              is_flag=True,
              default=False,
              help="Debug mode: Print to stdout instead of sending to Slack")
# TODO : Remove --slack-token from CLI Options 
@click.option('--slack-token',
              help="Token for the Slack API.")
@click.option('--admin-thread',
              help="Admin thread for actions (do not set manually)")
@click.option('--reply-thread',
              help="Reply thread for actions (do not set manually)")
@click.pass_obj
def cli(obj,
        debug=False,
        slack_token=None,
        admin_thread=None,
        reply_thread=None):
    # TODO : Remove slack_token
    obj.sc = MFBSlackClient(slack_token)
    if debug:
        obj.publish_state = lambda msg: logger(msg, head='[debug state] ')
        obj.reply = lambda msg: logger(msg, head='[debug reply] ')
        obj.upload = lambda path:\
            logger('upload %s' % path, head='[debug upload] ')
    else:
        if admin_thread:
            obj.publish_state =\
                lambda msg: obj.sc.post_message(msg, *admin_thread.split(':'))
        if reply_thread:
            obj.thread = reply_thread
            channel, thread_ts = reply_thread.split(':')
            obj.upload =\
                lambda path: obj.sc.upload_file(path, channel, thread_ts)
            obj.reply =\
                lambda msg, attachments=None: obj.sc.post_message(msg,
                                                                  channel,
                                                                  thread_ts,
                                                                  attachments)

@cli.command(help="Start the Metaflow bot server.")
@click.option('--admin',
              required=True,
              help="Email of the admin user (used to idenify the admin "
                   "Slack account).")
@click.option('--rules',
              default=DEFAULT_RULES,
              show_default=True,
              help="Rules file.")
@click.option('--new-admin-thread',
              is_flag=True,
              default=False,
              help="Initialize a new admin thread in a DM between "
                   "@metaflow and the admin user.")
@click.option('--load-state/--no-load-state',
              default=True,
              show_default=True,
              help="Reconstruct state based on the admin channel.")
@click.option('--action-user',
              default='nobody',
              show_default=True,
              help="If the server is run as root, sudo to this user "
                   "for all actions, to prevent system-wide side-effects.")
@click.pass_obj
def server(obj,
           admin=None,
           rules=None,
           new_admin_thread=False,
           load_state=None,
           action_user=None):

    def log(msg='', **kwargs):
        logger(msg, system_msg=True, **kwargs)

    if os.getuid() != 0:
        action_user = None

    rules_obj = MFBRules(rules)
    log("Loaded %d rules from %s" % (len(rules_obj), rules))

    server = MFBServer(obj.sc, admin, rules_obj, logger, action_user)
    if new_admin_thread:
        server.new_admin_thread()
        log("Started a new admin thread.")
    if load_state:
        log("Starting to load previous state..")
        server.reconstruct_state()
        log("State reconstructed.")
    log(head="Activating the bot..")
    server.loop_forever()

@cli.group(help='Bot actions')
@click.pass_obj
def action(ctx):
    pass
