import re
import time
import json
from typing import List, Optional, Union
import urllib
from itertools import islice

import requests
import os 
from slackclient import SlackClient
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from threading import Thread
from queue import Queue

from .exceptions import MFBException
from threading import Event


NUM_RETRIES = 3
MIN_RTM_EVENTS_INTERVAL = 1

# Slack file permalinks look like
# https://netflix.slack.com/files/U6U5ZJGE4/FBGAXGH71/foobar
# We are interested in the file ID, starting with F. Slack
# wraps links to <https://foobar>, we ignore the wrapping.
PERMALINK_FILE_ID = re.compile('<?https://.*?/(F.*?)/.*')

class MFBInvalidPermalink(MFBException):
    headlink = 'Invalid Slack permalink'
    def __init__(self, url):
        super(MFBInvalidPermalink, self).__init__("Invalid permalink: %s" % url)

class MFBUserNotFound(MFBException):
    headline = 'User not found'
    def __init__(self, user):
        super(MFBUserNotFound, self).__init__("User not found: %s" % user)

class MFBChannelNotFound(MFBException):
    headline = 'Channel not found'
    def __init__(self, chan):
        super(MFBChannelNotFound, self).__init__("Channel not found: %s" % chan)

class MFBClientException(MFBException):
    headline = "Slack client failed"
    traceback = True
    def __init__(self, method, args, resp=None):
        lst = ', '.join('%s=%s' % x for x in args.items())
        msg = "Request '%s' with args %s failed" % (method, lst)
        if resp:
            msg += '. Unknown response: %s' % resp
        self.resp = resp
        super(MFBClientException, self).__init__(msg)

    def __str__(self):
        return self.msg

class MFBRequestFailed(MFBClientException):
    pass

class MFBRateLimitException(MFBClientException):
    pass

class MFBRateLimitException(MFBClientException):
    pass

class SlackMessageQueue(Queue):
    def __init__(self, maxsize: int) -> None:
        super().__init__(maxsize=maxsize)

    def injest(self,messages:List[dict]) -> None:
        """injest 
        TODO : Push Multiple messsage to Queue
        """
        pass

    def flush(self)-> Union[List[dict],None]:
        """flush 
        TODO :Take all messages from the Queue and return to the caller. 
        Essentially Empty Everything. 
        """
        pass



class SlackSocketSubscriber(Thread):
    """SlackSocketSubscriber 
    This will be a daemon thread that will connect to slack and subscribe to the message feed via the `SocketModeClient`
    This will use a message queue to keep sending messages to the main thread. 

    This is a daemon thread because it should die when the program shuts and we don't care much about it once it starts

    TODO : Ensure this thread runs without any kind of failure. 
    """
    def __init__(self,slack_token,message_queue:Queue) -> None:
        super().__init__(daemon=True)
        self.publisher_queue = message_queue
        # Todo : figure management for the `SLACK_APP_TOKEN` in the instantiation and code running. 
        self.sc = SocketModeClient(
            # This app-level token will be used only for establishing a connection
            app_token=os.environ.get("SLACK_APP_TOKEN"),  # xapp-A111-222-xyz
            # ? : Do we need a WebClient here ?
            web_client=WebClient(token=slack_token)  # xoxb-111-222-xyz
        )
    
    def run(self) -> None:
        """run 
        TODO : wire up the socket feed and the function to filter flush items to queue
        """
        pass

def create_slack_subscriber(slack_token:str):
    message_queue = SlackMessageQueue()
    socket_thread = SlackSocketSubscriber(slack_token,message_queue) 
    socket_thread.start()
    return message_queue


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
    def __init__(self,slack_token) -> None:
        # plug in appropriate slack_sdk. Ensure `slack_token` is there. 
        # Todo : figure management for the `SLACK_APP_TOKEN` in the instantiation and code running. 
        self.sc = WebClient(token=slack_token)  # xoxb-111-222-xyz
        self.rtm_connected = False
        self._slack_token = slack_token
        self._last_rtm_events = 0
        self._rmt_feed_queue = None

    @property
    def token(self):
        return self._slack_token


    def bot_user_id(self):
        # permission : auth.test
        return self.sc.auth_test()['user_id']

    def post_message(self, msg, channel, thread=None, attachments=None):
        # TODO : This function is wrapper to throw a message into a channel. 
        # This function is important because the CLI wrapper with click and the 
        # MFBServer will use this to put messages in admin thread and actual user threads. 
        pass

    # def event_processor

    def upload_file(self, path, channel, thread=None):
        # permission : files.upload
        args = {'channels': channel}
        if thread:
            args['thread_ts'] = thread

        args['file'] = open(path, 'rb')
        self.sc.files_upload(**args)

    def rtm_events(self):
        """rtm_events 
        this method is only called by the server to get the get the realtime 
        events from slack. 

        Version 1 used SlackClient.rtm_read() to retrieve the messages from slack with a 
        timeout. 

        Verison 2 is using SocketMode and in that light is it better to create a thread 
        along with a message queue to keep flushing information socket consumer and the 
        main server thread. 
        """
        # todo : Instantiate event reader over here. 
        if not self.rtm_connected:
            self._rmt_feed_queue = create_slack_subscriber(self.token)
            self.rtm_connected = True
        
        return self._rmt_feed_queue.flush()
        

    def im_channel(self, user):
        # permission : im.open
        try:
            return self.sc.im_open(user)['channel']['id']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'user_not_found':
                raise MFBUserNotFound(user)
            else:
                raise

    def user_by_email(self, email):
        # permission : users.lookupByEmail
        try:
            return self.user_by_email(email)['user']['id']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'users_not_found':
                raise MFBUserNotFound(email)
            else:
                raise

    def user_info(self, user):
        # permission : users.info
        try:
            return self.user_info(user)['user']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'user_not_found':
                raise MFBUserNotFound(user)
            else:
                raise

    def channel_info(self, channel):
        # permission : channels.info
        try:
            return self.channel_info(channel)['channel']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'user_not_found':
                raise MFBChannelNotFound(channel)
            else:
                raise

    def direct_channels(self):
        # TODO : permission : im.list, ims
        pass

    def past_events(self, channel, **opts):
        # TODO : permission : conversations.history, messages
        pass

    def past_replies(self, channel, thread, **opts):
        # TODO : permission : conversations.replies, messages
        pass

    def download_file(self, file_permalink):
        # TODO : permission : files.info
        pass

    def _format_history(self, events, max_number=None, sort_key='ts'):
        if max_number is not None:
            events = islice(events, max_number)
        if sort_key:
            events = sorted(events, key=lambda x: x[sort_key])
        return events

    def _page_iter(self, method, it_field, **args):
        # TODO : validate if this method is needed. 
        pass

    def _request_file(self, url):
        # TODO : validate if this method is needed. 
        pass

    def _request(self, method, raise_on_error=False, **args):
        # TODO : validate if this method is needed. 
        pass

class MFBSlackClient(object):

    def __init__(self, slack_token):
        self.sc = SlackClient(slack_token)
        self._slack_token = slack_token
        self.rtm_connected = False
        self._last_rtm_events = 0

    @property
    def token(self):
        return self._slack_token

    def bot_user_id(self):
        return self._request('auth.test', raise_on_error=True)['user_id']

    def post_message(self, msg, channel, thread=None, attachments=None):
        args = {'channel': channel}
        if msg is not None:
            args['text'] = msg
        if attachments:
            args['attachments'] = json.dumps(attachments)
        if thread:
            args['thread_ts'] = thread
        return self._request('chat.postMessage',
                             raise_on_error=True,
                             **args)['ts']

    def upload_file(self, path, channel, thread=None):

        args = {'channels': channel}
        if thread:
            args['thread_ts'] = thread

        args['file'] = open(path, 'rb')
        resp = self._request('files.upload', raise_on_error=True, **args)

    def rtm_events(self):
        if not self.rtm_connected:
            if self.sc.rtm_connect(with_team_state=False,
                                   auto_reconnect=True):
                self.rtm_connected = True
            else:
                raise MFBException("RTM connect failed")
        t = time.time()
        d = t - self._last_rtm_events
        if d < MIN_RTM_EVENTS_INTERVAL:
            time.sleep(MIN_RTM_EVENTS_INTERVAL - d)
        self._last_rtm_events = t
        return self.sc.rtm_read()

    def im_channel(self, user):
        try:
            return self._request('im.open',
                                 user=user,
                                 raise_on_error=True)['channel']['id']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'user_not_found':
                raise MFBUserNotFound(user)
            else:
                raise

    def user_by_email(self, email):
        try:
            return self._request('users.lookupByEmail',
                                 email=email,
                                 raise_on_error=True)['user']['id']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'users_not_found':
                raise MFBUserNotFound(email)
            else:
                raise

    def user_info(self, user):
        try:
            return self._request('users.info',
                                 user=user,
                                 raise_on_error=True)['user']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'user_not_found':
                raise MFBUserNotFound(user)
            else:
                raise

    def channel_info(self, channel):
        try:
            return self._request('channels.info',
                                 channel=channel,
                                 raise_on_error=True)['channel']
        except MFBRequestFailed as ex:
            if ex.resp['error'] == 'channel_not_found':
                raise MFBChannelNotFound(channel)
            else:
                raise

    def direct_channels(self):
        return self._page_iter('im.list', 'ims', sort_key=None)

    def past_events(self, channel, **opts):
        events = self._page_iter('conversations.history',
                                 'messages',
                                 channel=channel)
        return self._format_history(events, **opts)

    def past_replies(self, channel, thread, **opts):
        events = self._page_iter('conversations.replies',
                                 'messages',
                                 channel=channel,
                                 ts=thread)
        return (event for event in self._format_history(events, **opts)
                if 'reply_count' not in event)

    def download_file(self, file_permalink):
        m = PERMALINK_FILE_ID.match(file_permalink)
        if m:
            try:
                info = self._request('files.info',
                                     file=m.group(1),
                                     raise_on_error=True)['file']
            except MFBRequestFailed:
                raise MFBInvalidPermalink(file_permalink)
            else:
                return self._request_file(info['url_private'])
        else:
            raise MFBInvalidPermalink(file_permalink)

    def _format_history(self, events, max_number=None, sort_key='ts'):
        if max_number is not None:
            events = islice(events, max_number)
        if sort_key:
            events = sorted(events, key=lambda x: x[sort_key])
        return events

    def _page_iter(self, method, it_field, **args):
        args['limit'] = 200
        while True:
            resp = self._request(method, **args)
            for item in resp[it_field]:
                yield item
            cursor = None
            if 'response_metadata' in resp:
                cursor = resp['response_metadata'].get('next_cursor')
            if cursor:
                args['cursor'] = cursor
            else:
                break

    def _request_file(self, url):
        msg = None
        for i in range(NUM_RETRIES):
            try:
                headers = {'Authorization': 'Bearer ' + self.token}
                resp = requests.get(url, headers=headers)
            except:
                pass
            else:
                msg = resp.text
                status = str(resp.status_code)[0]
                if status == '2':
                    return resp.content
                elif status == '4':
                    break
            time.sleep(2**i)
        raise MFBClientException('download_file', {'url': url}, msg)

    def _request(self, method, raise_on_error=False, **args):
        for i in range(NUM_RETRIES + 1):
            delay = 2**i
            try:
                resp = self.sc.api_call(method, **args)
                if resp['ok']:
                    return resp
                elif 'Retry-After' in resp['headers']:
                    delay = int(response['headers']['Retry-After'])
                elif raise_on_error:
                    raise MFBRequestFailed(method, args, resp)
                else:
                    return resp
            except MFBRequestFailed:
                raise
            except:
                if i == NUM_RETRIES:
                    raise
            finally:
                time.sleep(delay)
        else:
            raise MFBRateLimitException(method, args)
