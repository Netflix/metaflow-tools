import re
import time
import json
import urllib
from itertools import islice

import requests
from slackclient import SlackClient

from .exceptions import MFBException

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
