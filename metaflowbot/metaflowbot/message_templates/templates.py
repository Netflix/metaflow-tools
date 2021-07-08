from datetime import datetime

import timeago

DATEPARSER = lambda date,format="%Y-%m-%dT%H:%M:%SZ": datetime.strptime(date,format)

# Block Messages on slack : https://api.slack.com/reference/block-kit/blocks
class IntroMessage:

    def get_slack_message(self,bot_name):
        INTO_MESSAGE_BLOCKS = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there :wave: I'm {bot_name}. I am the Metaflow Bot :robot_face:. "
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":one: You can wake up me by invoking `{bot_name}`. I will reply on a thread and will then respond to messages to you in that thread."
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
        return INTO_MESSAGE_BLOCKS



class ListFlowsTemplate:

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

    def make_context_block(self):
        return {
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": ":eyes: Inspect any of the runs messaging `inspect`\n:question: Get help at any time by messaging help on this thread or type *help* in a DM with me"
				}
			]
		}

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

        flowmessages.append(self.make_context_block())


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
