import traceback
from datetime import datetime
from urllib.parse import urlparse

import click
import timeago
from ..cli import action
from ..state import MFBState

MAX_ARTIFACT_SIZE = 1000
import requests
import json


def random_joke():
    ENDPOINT = r"https://official-joke-api.appspot.com/jokes/programming/random"    
    data = requests.get(ENDPOINT)
    tt = json.loads(data.text)
    return tt



@action.command(help="Tell Me A Joke")
@click.pass_context
def joke(ctx):
    obj = ctx.obj
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
        obj.reply(
            f'''
            Sorry, I couldn't find a joke at the moment :meow_dead:
            '''
        )
    