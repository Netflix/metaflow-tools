import random
from datetime import datetime
from typing import List

import timeago
from metaflowbot.message_templates.templates import (DATEPARSER, HEADINGS,
                                                     Template)

from .run_resolver import ResolvedRun, ResolvedStep


def make_help(cmd_base):
    return [
        (
            "Inspect `Run`s of a particular `Flow`",
            [
                f"{cmd_base} HelloFlow",
                f"{cmd_base} savin's HelloFlow",
                f"{cmd_base} savin's HelloFlow tagged some_tag"
            ]
        ),
        (
            "Inspect an individual `Run` instance",
            [
                f"{cmd_base} HelloFlow/12",
                f"{cmd_base} the latest run of HelloFlow",
                f"{cmd_base} dberg's latest run of HelloFlow",
            ]
        )
    ]

class InspectHelp(Template):

    EMOJI_NUMBERS = [":one:",":two:",":three:",":four:",":five:",":six:",":seven:",":eight:",":nine:",":ten:"]

    def __init__(self,help_blocks=[]) -> None:
        super().__init__()
        if len(help_blocks) > 0:
            for h in help_blocks:
                assert len(h) == 2
        self._help_blocks = help_blocks

    def _format_help_sentence(self,command):
        sent = f":hash: `{command}`"
        return sent

    def _submenu_heading(self,help_message):
        return [
            {
                "type":"header",
                "text": {
                    "type": "plain_text",
                    "text": help_message
                }
            }
        ]

    def _format_command_help(self,help_message,sentences,max_routes=10):
        help_blocks = []
        help_blocks.extend(self._submenu_heading(help_message))
        route_sentences = []
        sample_sentences = random.sample(sentences,max_routes) if max_routes < len(sentences) else sentences
        for command in sample_sentences:
            assert command is not None
            route_sentences.append(
                self._format_help_sentence(command)
            )
        help_commands = '\n\n'.join(route_sentences)
        help_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f'\n{help_commands}'
                }
        })
        return help_blocks

    def _help_menu(self):
        main_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":mag_right: How to `inspect` ?"
                }
            },
            {
                "type":"divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`inspect` :mag_right: uses the Metaflow Client API to inspect (meta)data "\
                            "about past or ongoing runs. Calling inspect in different ways will result "
                            "in different types of responses. There are three major types of responses."
                }
            }
        ]
        route_numbers = []
        if len(self._help_blocks) > len(self.EMOJI_NUMBERS):
            route_numbers = self.EMOJI_NUMBERS+ [":keycap_star:" for _ in range(len(self._help_blocks) - len(self.EMOJI_NUMBERS))]
        else:
            route_numbers = self.EMOJI_NUMBERS[:len(self._help_blocks)]

        if len(self._help_blocks) > 0:
            for help_tup,head_emoji in zip(self._help_blocks,route_numbers):
                main_blocks.append({"type":"divider"})
                help,routes = help_tup
                if help is not None:
                    help = f"{head_emoji} {help}"
                main_blocks.extend(self._format_command_help(help,routes))
        main_blocks.extend(self.make_context_block())
        return main_blocks


    def make_help(self):
        return "How to inspect",self._help_menu()


class RunResponse(Template):

    def _make_run_block(self,run:ResolvedRun):
        run_user = [t for t in run.tags if 'user:' in t]
        user = 'Not Found'
        if len(run_user) > 0:
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
                        "text": f"*Run Spec:* {run.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tags:* {tags}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Successful:* {':white_check_mark:' if run.successful else ':question:' }"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed On:* {ago}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed By:* {user}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Currently Running:* {':white_check_mark:' if run.running else ':x: ' }"
                    }
                    ]
                },
        ]
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
                    "text": f":star: Found {num_runs} Runs of {flow_name}"
                }
            },

        ]

        runmessages.extend(run_blocks)
        runmessages.extend(self.make_context_block())

        return runmessages

    def _make_run_attachment(self,flow):
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

    def make_attachments(self,resolved_runs):
        attachments = []
        for run in resolved_runs:
            attachments.append(self._make_run_attachment(run))
        return attachments



class InspectRunResponse(Template):

    SLACK_MAX_BLOCKS = 50

    def _step_overflow_context(self,num_excess):
        return  [
            {
                "type":"divider"
            },
            {
                "type":"context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":ocean: There were more steps than we could display on Slack :slack:. "
                                f"Showing last {abs(num_excess)} steps"
                    }
                ]
            }
        ]

    @property
    def _main_tags(self):
        if self._tags is not None:
            return ', '.join([f'`{t}`'for t in self._tags.split(',')])
        return None

    @property
    def _date(self):
        if self._start_date is None:
            return None
        return self._start_date.strftime('%Y-%m-%d')

    @property
    def _path_spec(self):
        return f'{self._flow}/{self._runid}'

    def _make_headline(self,resolved_run:ResolvedRun):
        header_message = f":mag_right: Inspecting Run : {resolved_run.id}"
        header = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_message
                }
            },
            {
                "type":"divider"
            },
        ]
        return header


    def _make_run_block(self,run:ResolvedRun):
        run_user = [t for t in run.tags if 'user:' in t]
        user = 'Not Found'
        if len(run_user) > 0:
            user = run_user[0].replace('user:','')
        ago = timeago.format(DATEPARSER(run.when), now=datetime.utcnow())
        tags = ', '.join([f'`{t}`' for t in run.tags])
        steps = list(run)
        block =  [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Spec:* {run.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tags:* {tags}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Successful:* {':white_check_mark:' if run.successful else ':question:' }"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed On:* {ago}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run Executed By:* {user}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Currently Running:* {':white_check_mark:' if run.running else ':x: ' }"
                    }
                    ]
            }
        ]
        return block

    def _make_resolved_steps(self,steps:List[ResolvedStep],max_steps=30):
        def step_parser(step:ResolvedStep):
            return {
                "type": "section",
                "text":{
                    "type":"mrkdwn",
                    "text":f"*Step Name:`{step.name}`*"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Number Of Tasks*: `{step.num_tasks}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Step Runtime*: {step.step_runtime }"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Step Execution Started On*: {step.started_on}"
                    }
                ]
            }
        steps_to_parse = steps
        if len(steps) > max_steps:
            # find last x steps if the steps are greater than max_steps
            # We do this because slack at max allows certain number of `blocks`
            steps_to_parse = steps[-max_steps:]

        overflow_context = [] if len(steps) < max_steps else self._step_overflow_context(max_steps)
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":star2: Step Metadata"
                }
            }
        ] + list(map(step_parser,steps_to_parse)) + overflow_context


    def get_slack_message(self,resolved_tuple):
        # ! NOT USING THIS METHOD ANYMORE .
        # REVERED TO OLD CODE>
        if resolved_tuple is None:
            response_message = f"I Couldn't find anything with your query on."
            return self._make_null_response(
                headline=HEADINGS.NO_RUNS.value,
                response_line=response_message
            )

        resolved_run,_ = resolved_tuple
        headlineblock = self._make_headline(resolved_run)
        headlineblock.extend(self._make_run_block(resolved_run))

        # We do -3 for  header,STEP_OVERFLOW(2),context(2)
        # max_allowed_steps = self.SLACK_MAX_BLOCKS - len(headlineblock) - 5
        # headlineblock.extend(self._make_resolved_steps(resolved_steps,max_steps=max_allowed_steps))
        # headlineblock.extend(self.make_context_block())
        return headlineblock
