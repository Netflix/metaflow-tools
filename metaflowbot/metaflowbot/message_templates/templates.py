import re
from collections import namedtuple
from datetime import datetime
from enum import Enum

import timeago
from metaflow.metaflow_version import get_version

from ..version import __version__

DATEPARSER = lambda date,format="%Y-%m-%dT%H:%M:%SZ": datetime.strptime(date,format)
DEFAULT_ERROR_MESSAGE = ':skull_and_crossbones: Oops something went wrong'
SLACK_MAX_BLOCKS = 50

class HEADINGS(Enum):
    NO_FLOWS = "No Flows Found :meow_dead:"
    NO_RUNS = "No Runs Matched :meow_dead:"

class RESPONSES(Enum):
    NO_FLOW_IN_NAMESPACE  = f"I couldn't find any flows on a Global namespace."\
                            "If you are new to Metaflow please have a look at the docs"\
                            ": https://docs.metaflow.org/"
    WAITING = f'Alright, Just a minute I am resolving your query.'

    USER_NOT_PRESENT = ":meow_thinkingcool: It seems the User you may have been "\
                        "looking for is not present in the Metadata service. Maybe try a different "\
                        "user ?"
class HEADINGS(Enum):
    NO_FLOWS = "No Flows Found :meow_dead:"
    NO_RUNS = "No Runs Matched :meow_dead:"

class RESPONSES(Enum):
    NO_FLOW_IN_NAMESPACE  = f"I couldn't find any flows on a Global namespace."\
                            "If you are new to Metaflow please have a look at the docs"\
                            ": https://docs.metaflow.org/"
    WAITING = f'Alright, Just a minute I am resolving your query.'

    USER_NOT_PRESENT = ":meow_thinkingcool: It seems the User you may have been "\
                        "looking for is not present in the Metadata service. Maybe try a different "\
                        "user ?"
class Template:

    def _make_null_response(self,
                            response_line=RESPONSES.NO_FLOW_IN_NAMESPACE.value,\
                            headline=HEADINGS.NO_FLOWS.value):

        message = [
             {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text":headline
                },
            },
            {
                "type":"section",
                "text":{
                    "type":"mrkdwn",
                    "text":f"{response_line}"
                }
            }
        ]
        message.extend(self.make_context_block())
        return message

    def make_context_block(self):
        return [
            {
                "type":"divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":question: Get help at any time by messaging help on "
                                "this thread or type *help* in a DM with me\n"
                    }
                ]
		    }
        ]

class BotVersion(Template):

    def _get_metadata_endpoint(self):
        from metaflow import get_metadata
        mds = get_metadata()
        _,service_url = mds.split('@')
        return service_url

    def get_slack_message(self):
        message = f"Running Metaflowbot version `{__version__}` with Metaflow version "\
                f"`{get_version(pep440=True)}` and "\
                "configured with metaflow service endpoint "\
                f"- `{self._get_metadata_endpoint()}`"

        return message

# Block Messages on slack : https://api.slack.com/reference/block-kit/blocks
class IntroMessage(Template):


    def get_slack_message(self,bot_name):
        intro_message = f"Hey, I am {bot_name}, the Metaflowbot :robot_face:! "\
                        "I can help you to inspect results of past runs. "\
                        f"If you want to inspect results, type the following commands for more information: "\
                        f"{bot_name} how to inspect run or {bot_name} how to inspect. "

        INTO_MESSAGE_BLOCKS = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": intro_message
                    }
                },
                {
                    "type":"divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Note that all discussions with me should happen in a thread. "\
                                    f"You can open a new thread with me e.g. by saying {bot_name} hey on any channel."\
                                    "You can open multiple threads with me if you want to. "\
                                    "Each thread is an independent discussion."
                        }
                    ]
		    }
        ]
        # INTO_MESSAGE_BLOCKS.extend(self.make_context_block())
        return intro_message,INTO_MESSAGE_BLOCKS
