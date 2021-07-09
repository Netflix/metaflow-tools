from datetime import datetime

import timeago
from metaflow import Run

from ..version import __version__

"""
Actions Supported by the Bot :

[+] Action 1. : `@flowey help`
[+] Action 2.1: `@flowey list flows`
[ ] Action 2.2: `@flowey list flows run by valaydave`
[ ] Action 2.2: `@flowey list flows by valaydave`
[ ] Action 2.3: `@flowey list flows`
[ ] Action 2.3: `@flowey list flows with tag from `

[ ] Action 3: `@flowey what's your version?`
[ ] Action 3: `@flowey --version`
[ ] Action 3: `@flowey version`

[+] Action 4.1: `@flowey inspect run`
[+] Action 4.2: `@flowey inspect run HelloFlow/12.`
[+] Action 4.3: `@flowey inspect run HelloAWSFlow tagged date:2021-07-08`
[ ] Action 4.4: `@flowey inspect run HelloAWSFlow.`
[ ] Action 4.5: `@flowey inspect dberg's HelloFlow.`
[ ] Action 4.6: `@flowey inspect dberg's latest run of HelloFlow.`
[ ] Action 4.7: `@flowey inspect the latest run of HelloFlow.`
[+] Action 4.8: `@flowey inspect logs [step] # Incontext`
[+] Action 4.9: `@flowey inspect data [step] # Incontext`
"""

from collections import namedtuple

ResolvedRun = namedtuple('ResolvedRun',
                         ['id',
                          'flow',
                          'who',
                          'when',
                          'finished',
                          'successful',
                          'errored',
                          'running',
                          'tags',
                          'origin_run_id',
                          'code_package'])

DATEPARSER = lambda date,format="%Y-%m-%dT%H:%M:%SZ": datetime.strptime(date,format)

HowToInspect = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "`inspect` :mag_right: uses the Metaflow Client API to inspect (meta)data "\
                    "about past or ongoing runs. First, you need to specify a run "
                    "After you have specified a run, you can use the following "\
                    "commands:"\
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "There are a number of ways to refer to an existing run:\n"\
        }
    },
    {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":":one: * Use an existing run ID: `inspect HelloFlow/12`.*\n",
        }
    },
    {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":":two: * Use a flow name: `inspect HelloFlow`.*\n",
        }
    },
    {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":":three: * Use a flow name with a user: `inspect dberg's HelloFlow`.*\n",
        }
    },
    {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":":four: * Use the latest run of a user: `inspect dberg's latest run of HelloFlow`.*\n",
        }
    },
    {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":":five: * Use the latest run by anyone: `inspect the latest run of HelloFlow`.*\n",
        }
    },
     {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":"You can filter by a tag by appending `tagged some_tag` in any of the "\
                    "expressions above except the first one. If there are multiple "\
                    "eligible runs, I will show you a list of run IDs to choose from."\

        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": " *`inspect` * to see an overview of the run status.\n"\
                    " *`inspect data at [step]` * to inspect data of the given step.\n"\
                    " *`inspect logs at [step]` * to inspect logs of the given step.\n"
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
                "text": ":eyes: Inspect any of the runs messaging `inspect`\n:question: Get help at any time by messaging help on this thread or type *help* in a DM with me"
            }
        ]
    }
]

class Template:
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
					"text": ":eyes: Inspect any of the runs messaging `inspect`\n"
                            ":scroll: List flows by messaging `list flows`\n"
                            ":question: Get help at any time by messaging help on "
                            "this thread or type *help* in a DM with me\n"
				}
			]
		}
]

class RunResponse(Template):

    def _make_run_block(self,run:ResolvedRun):
        run_user = [t for t in run.tags if 'user:' in t]
        user = run_user[0].replace('user:','')
        ago = timeago.format(DATEPARSER(run.when), now=datetime.utcnow())
        tags = ', '.join([f'`{t}`' for t in run.tags])

        block =  [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":zap: {run.id}"
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Spec:*\n{run.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tags:*\n{tags}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Successful : {':white_check_mark:' if run.successful else ':question:' } *"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed On:*\n{ago}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed By:*\n{user}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Currently Running:* {':white_check_mark:' if run.running else ':skull_and_crossbones: ' }"
                    }
                    ]
                },

        ]
        if run.origin_run_id is not None:
            block[1]['fields'].append(
                {
                        "type": "mrkdwn",
                        "text": f"*Originated From: {run.origin_run_id} * "
                }
            )
        return block

    def get_slack_message(self,runs):
        flow_name = None # todo : get flow anme
        run_blocks = []
        num_runs=0
        for run in runs:
            num_runs+=1
            flow_name = run.id.split('/')[0]
            run_blocks.extend(self._make_run_block(run))

        runmessages = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":star: I found {num_runs} Runs of {flow_name}"
                }
            },

        ]

        runmessages.extend(run_blocks)
        runmessages.extend(self.make_context_block())

        return runmessages

    def _make_flow_attachment(self,flow):
        ago = timeago.format(DATEPARSER(flow.latest_run.created_at), now=datetime.utcnow())
        run_latest_user = [t for t in flow.latest_run.tags if 'user:' in t]
        user = run_latest_user[0].replace('user:','')
        success_path_spec = None
        if flow.latest_successful_run is not None:
            success_path_spec = flow.latest_successful_run.pathspec
        fields = [
            {
                'title': 'Latest Successful Run',
                'value': success_path_spec,
                'short': True
            },
            {
                'title': 'Latest Run',
                'value': flow.latest_run.pathspec,
                'short': True
            },
            {
                'title': 'Latest Run Executed On',
                'value': ago,
                'short': True
            },
            {
                'title': 'Latest Run Executed By',
                'value': user,
                'short': True
            }
        ]
        return {
            'fallback': 'Flow %s' % flow.id,
            'title': ':zap: Flow: ' + flow.id,
            'fields': fields,
            'color': '#1F3FE0' # blue color
        }

    def make_attachments(self,flows):
        attachments = []
        for flow in flows:
            print(flow)
            attachments.append(self._make_flow_attachment(flow))
        return attachments



# Block Messages on slack : https://api.slack.com/reference/block-kit/blocks
class IntroMessage(Template):

    def get_slack_message(self,bot_name):
        INTO_MESSAGE_BLOCKS = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there :wave: I'm {bot_name}."
                                f"I am the Metaflow Bot v{__version__} :robot_face:. "
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":one: You can wake up me by invoking `{bot_name}`."
                                "I will reply on a thread and will then respond to"
                                "messages on that thread."
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":two: message `list flows` to inspect individual runs."
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":three: message `inspect` to inspect individual runs."
                    }
                },

        ]
        INTO_MESSAGE_BLOCKS.extend(self.make_context_block())
        return INTO_MESSAGE_BLOCKS


class ListFlows(Template):

    def _make_flow_block(self,flow):
        run_latest_user = [t for t in flow.latest_run.tags if 'user:' in t]
        user = run_latest_user[0].replace('user:','')
        ago = timeago.format(DATEPARSER(flow.latest_run.created_at), now=datetime.utcnow())
        success_path_spec = None
        if flow.latest_successful_run is not None:
            success_path_spec = flow.latest_successful_run.pathspec
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":zap: {flow.id}"
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Latest Run:*\n{flow.latest_run.pathspec}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Latest Successful Run:*\n{success_path_spec}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Latest Run Executed On:*\n{flow.latest_run.created_at}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Latest Run Executed On:*\n{ago}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Latest Run Executed By:*\n{run_latest_user[0].replace('user:','')}"
                    }
                    ]
                },

        ]

    def get_slack_message(self,flows):
        main_flow_meta = []
        flowmessages = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":star: I found {len(flows)} Flows"
                }
            },

        ]
        for f in flows:
            flowmessages.extend(self._make_flow_block(f))

        flowmessages.extend(self.make_context_block())


        return flowmessages

    def _make_flow_attachment(self,flow):
        ago = timeago.format(DATEPARSER(flow.latest_run.created_at), now=datetime.utcnow())
        run_latest_user = [t for t in flow.latest_run.tags if 'user:' in t]
        user = run_latest_user[0].replace('user:','')
        success_path_spec = None
        if flow.latest_successful_run is not None:
            success_path_spec = flow.latest_successful_run.pathspec
        fields = [
            {
                'title': 'Latest Successful Run',
                'value': success_path_spec,
                'short': True
            },
            {
                'title': 'Latest Run',
                'value': flow.latest_run.pathspec,
                'short': True
            },
            {
                'title': 'Latest Run Executed On',
                'value': ago,
                'short': True
            },
            {
                'title': 'Latest Run Executed By',
                'value': user,
                'short': True
            }
        ]
        return {
            'fallback': 'Flow %s' % flow.id,
            'title': ':zap: Flow: ' + flow.id,
            'fields': fields,
            'color': '#1F3FE0' # blue color
        }


    def make_attachments(self,flows):
        attachments = []
        for flow in flows:
            print(flow)
            attachments.append(self._make_flow_attachment(flow))
        return attachments
