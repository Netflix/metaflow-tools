import json
from functools import partial
from itertools import islice
from queue import Empty, Queue
from threading import Event, Thread
from typing import List

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from .exceptions import MFBException

NUM_RETRIES = 3
MIN_RTM_EVENTS_INTERVAL = 1


class MFBInvalidPermalink(MFBException):
    headlink = "Invalid Slack permalink"

    def __init__(self, url):
        super(MFBInvalidPermalink, self).__init__("Invalid permalink: %s" % url)


class MFBUserNotFound(MFBException):
    headline = "User not found"

    def __init__(self, user):
        super(MFBUserNotFound, self).__init__("User not found: %s" % user)


class MFBChannelNotFound(MFBException):
    headline = "Channel not found"

    def __init__(self, chan):
        super(MFBChannelNotFound, self).__init__("Channel not found: %s" % chan)


class MFBClientException(MFBException):
    headline = "Slack client failed"
    traceback = True

    def __init__(self, method, args, resp=None):
        lst = ", ".join("%s=%s" % x for x in args.items())
        msg = "Request '%s' with args %s failed" % (method, lst)
        if resp:
            msg += ". Unknown response: %s" % resp
        self.resp = resp
        super(MFBClientException, self).__init__(msg)

    def __str__(self):
        return self.msg


class MFBRequestFailed(MFBClientException):
    pass


class MFBRateLimitException(MFBClientException):
    pass


class SlackMessageQueue(Queue):
    """SlackMessageQueue
    Message Queue to hold all Slack messages from `SlackSocketSubscriber`.
    TODO: Stress Test the queue.
    """

    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize=maxsize)

    def injest(self, messages: List[dict]) -> None:
        """injest
        Push Multiple messsage to Queue. \
        Queue.put is by default Blocking to avoid Loosing messages and has Mutex's internally.
        """
        for m in messages:
            self.put(m)

    def flush(self) -> List[dict]:
        """flush
        Take all messages from the Queue and return to the caller.
        Essentially Empty Everything.
        https://stackoverflow.com/questions/8196254/how-to-iterate-queue-queue-items-in-python
        """
        try:
            queue_items = []
            while True:
                queue_items.append(self.get_nowait())
        except Empty:
            pass
        return queue_items


def process(
    message_event_queue: SlackMessageQueue,
    client: SocketModeClient,
    req: SocketModeRequest,
):
    if req.type == "events_api":
        # Slash commands will have a different req.type
        """
        # Permisssions for :
            - https://api.slack.com/events/message.im
            - https://api.slack.com/events/app_mention
        Payload from different events can be found : https://api.slack.com/events/
        Current `req.payload['event'].type == app_mention | message`
        """
        # ! acknowledgement is needed to ensure messages are not Double sent
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)
        message_event_queue.injest([req.payload["event"]])


class SlackSocketSubscriber(Thread):
    """SlackSocketSubscriber
    This will be a daemon thread that will connect to slack and subscribe to the message feed via the `SocketModeClient`
    This will use a message queue to keep sending messages to the main thread.

    This is a daemon thread because it should die when the program shuts and we don't care much about it once it starts
    """

    def __init__(
        self,
        app_token,
        message_event_queue: Queue,
    ) -> None:
        assert app_token is not None
        super().__init__(daemon=True)
        self.message_event_queue = message_event_queue
        self._app_token = app_token

    def run(self) -> None:
        """run
        wire up the socket feed and the function to filter flush items to queue
        """
        self.sc = SocketModeClient(
            # This app-level token will be used only for establishing a connection
            app_token=self._app_token,  # xapp-A111-222-xyz
        )
        # Bind the queue to ensure Message Paassig.
        subscriber_func = partial(process, self.message_event_queue)
        self.sc.socket_mode_request_listeners.append(subscriber_func)
        # Establish a WebSocket connection to the Socket Mode servers
        self.sc.connect()
        Event().wait()


def create_slack_subscriber(app_token):
    message_event_queue = SlackMessageQueue()
    socket_thread = SlackSocketSubscriber(app_token, message_event_queue)
    socket_thread.start()
    return message_event_queue, socket_thread


class MFBSlackClientV2(object):
    """MFBSlackClientV2
    Replaces the `slack_client` with `slack_sdk`
        - Leverages the `WebClient` and the `SocketModeClient` (With RTM Message subscriber)

    `slack_sdk` Socket Management:
    https://slack.dev/python-slack-sdk/socket-mode/index.html#socketmodeclient

    `slack_sdk` WebClient :
    https://slack.dev/python-slack-sdk/web/index.html

    `SocketModeClient` leverages a Message queue which gets the RTM events.

    """

    def __init__(self, slack_token, slack_app_token=None) -> None:
        assert slack_token is not None
        self.sc = WebClient(token=slack_token)  # xoxb-111-222-xyz
        self._app_token = slack_app_token
        self.rtm_connected = False
        self._slack_token = slack_token
        self._last_rtm_events = 0
        self._rmt_feed_queue = None
        self._socket_tread = None

    @property
    def token(self):
        return self._slack_token

    def bot_name(self):
        return self.sc.auth_test()["user"]

    def bot_user_id(self):
        # permission : auth.test
        return self.sc.auth_test()["user_id"]

    def post_message(self, msg, channel, thread=None, attachments=None, blocks=None):
        # This function is important because the CLI wrapper with click and the
        # MFBServer will use this to put messages in admin thread and actual user threads.
        args = {"channel": channel}
        if msg is not None:
            args["text"] = msg
        if attachments:
            args["attachments"] = json.dumps(attachments)
        if thread:
            args["thread_ts"] = thread
        if blocks is not None:
            args["blocks"] = blocks
        return self.sc.chat_postMessage(**args)["ts"]

    def _connect(self):
        # Instantiate event reader over here.
        if not self.rtm_connected:
            self._rmt_feed_queue, self._socket_tread = create_slack_subscriber(
                self._app_token
            )
            self.rtm_connected = True
        return self.rtm_connected

    def rtm_events(self):
        """rtm_events
        this method is only called by the server to get the get the realtime
        events from slack.

        Version 1 used SlackClient.rtm_read() to retrieve the messages from slack with a
        timeout.

        Verison 2 is using SocketMode and in that light is it better to create a thread
        along with a message queue to keep flushing information socket consumer and the
        main server thread.

        This version also tries to connect to many
        """
        self._connect()
        return self._rmt_feed_queue.flush()

    def im_channel(self, user):
        # Older API : im.open --> Deprecated
        # New API : conversations.open
        # SCOPE:  mpim:write
        # SCOPE:  im:write
        # SCOPE:  groups:write
        # SCOPE:  channels:manage
        try:
            return self.sc.conversations_open(users=user)["channel"]["id"]
        except MFBRequestFailed as ex:
            if ex.resp["error"] == "user_not_found":
                raise MFBUserNotFound(user)
            else:
                raise

    def user_by_email(self, email):
        # permission : users.lookupByEmail
        try:
            return self.sc.users_lookupByEmail(email=email)["user"]["id"]
        except MFBRequestFailed as ex:
            if ex.resp["error"] == "users_not_found":
                raise MFBUserNotFound(email)
            else:
                raise

    def past_events(self, channel, **opts):
        # API : conversations.history
        # SCOPE : channels:history
        # SCOPE : groups:history
        # SCOPE : im:history
        # SCOPE : mpim:history
        events = self._page_iter(
            self.sc.conversations_history, "messages", channel=channel
        )
        return self._format_history(events, **opts)

    def past_replies(self, channel, thread, **opts):
        # API: conversations.replies
        # SCOPE : channels:history
        # SCOPE : groups:history
        # SCOPE : im:history
        # SCOPE : mpim:history
        events = self._page_iter(
            self.sc.conversations_replies, "messages", channel=channel, ts=thread
        )
        return (
            event
            for event in self._format_history(events, **opts)
            if "reply_count" not in event
        )

    def _format_history(self, events, max_number=None, sort_key="ts"):
        if max_number is not None:
            events = islice(events, max_number)
        if sort_key:
            events = sorted(events, key=lambda x: x[sort_key])
        return events

    def _page_iter(self, method, it_field, **args):
        # Iteartor for getting paginated data
        args["limit"] = 200
        while True:
            resp = method(**args)
            for item in resp[it_field]:
                yield item
            cursor = None
            if "response_metadata" in resp:
                cursor = resp["response_metadata"].get("next_cursor")
            if cursor:
                args["cursor"] = cursor
            else:
                break
