import traceback
from urllib.parse import urlparse

import click
import timeago

from metaflowbot.cli import action
from metaflowbot.state import MFBState

MAX_ARTIFACT_SIZE = 1000
import json

import requests


def random_joke():
    ENDPOINT = r"https://official-joke-api.appspot.com/jokes/programming/random"
    data = requests.get(ENDPOINT)
    tt = json.loads(data.text)
    return tt



@action.command(help="Tell Me A Joke")
@click.option('--create-thread/--no-create-thread',
              help="Will create a new thread")
@click.pass_context
def joke(ctx,create_thread=False):
    obj = ctx.obj
    if create_thread:
        obj.publish_state(MFBState.message_new_thread(obj.thread))
    try:
        joke = random_joke()[0]
        setup = joke["setup"]
        punchline= joke["punchline"]
        obj.reply(
            f'''
            {setup} \n{punchline}
            '''
        )
    except:
        traceback.print_exc()
        obj.reply(
            f'''
            Sorry, I couldn't find a joke at the moment :meow_dead:
            '''
        )
