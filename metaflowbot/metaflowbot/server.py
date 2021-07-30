import json
import os
import subprocess
import sys
import time
import traceback
from collections import namedtuple

from .exceptions import MFBException
from .slack_client import MFBSlackClientV2
from .state import MFBState

# When a monitored process disappears, wait this many
# seconds before announcing it as a failed, lost process.
# In the normal case the monitored process sends a status
# update before LOST_PROCESS_LIMIT seconds have passed.
LOST_PROCESS_LIMIT = 30

Event = namedtuple(
    "Event",
    [
        "type",
        "msg",
        "user",
        "user_name",
        "chan",
        "chan_name",
        "ts",
        "thread_ts",
        "is_im",
        "is_mention",
        "is_direct",
    ],
)

class StateNotFound(MFBException):
    pass

class FormatFriendlyDict(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, k):
        v = self.data.get(k)
        if v is None:
            return ""
        elif isinstance(v, dict):
            return json.dumps(v)
        else:
            return v


class MFBServer(object):
    def __init__(
        self, slack_client: MFBSlackClientV2, admin_email, rules, logger, action_user
    ):
        self.sc = slack_client
        self.state = MFBState()
        self.dm_token = "<@%s>" % self.sc.bot_user_id()
        self.admin = self.sc.user_by_email(admin_email)
        self.admin_chan = self.sc.im_channel(self.admin)
        self.admin_thread = None
        self.rules = rules
        self.logger = logger
        self.action_user = action_user
        self._lost_processes = {}

    def new_admin_thread(self):
        ts = self.sc.post_message(
            self.state.message_new_admin_thread(), self.admin_chan
        )
        # sc.past_events considers only replies, so we need a reply in
        # the thread. Let's send a noop reply.
        self.sc.post_message(self.state.message_noop(), self.admin_chan, thread=ts)

    def reconstruct_state(self):
        """reconstruct_state
        On restart, State is reconstructed using a slack channel that has
        the dump of all messages.

        :raises StateNotFound: [description]
        """
        for event in self._state_event_log():
            self._update_state(event)
            self.admin_thread = event.thread_ts
        if self.admin_thread is None:
            raise StateNotFound(
                "Could not find a state thread. " "Restart with --new-admin-thread."
            )

    def _state_event_log(self):
        for top_event in self.sc.past_events(self.admin_chan):
            if self.state.is_admin_thread_parent(top_event["text"]):
                thread_ts = top_event["ts"]
                event_iter = self.sc.past_replies(self.admin_chan, thread_ts)
                yield from self._make_events(event_iter, admin_thread=thread_ts)

    def _log_event(self, event):
        head = "{0.type}"
        if event.type != "state_change":
            chan_field = "{0.chan}"
            if event.chan_name is not None:
                chan_field += " (#{0.chan_name})"
            elif event.chan[0] == "D":
                chan_field += " (direct)"
            user_field = "{0.user}"
            if event.user_name is not None:
                user_field += " (@{0.user_name})"
            head += " %s %s {0.thread_ts}" % (chan_field, user_field)
        head += " > "

        self.logger(
            event.msg, head=head.format(event), system_msg=(event.type == "state")
        )

    def loop_forever(self):
        while True:
            for event in  self._make_events(self.sc.rtm_events()):
                self._log_event(event)
                if event.type == "state_change":
                    self._update_state(event)
                self._apply_rule(event)
            time.sleep(1)


    def _make_events(self, event_iter, admin_thread=None):
        """_make_events [summary]
        Makes custom Event object from slack events.
        """
        if admin_thread is None:
            admin_thread = self.admin_thread
        for ev in event_iter:
            try:
                if ev["type"] == "message" or ev["type"] == "app_mention":
                    thread_ts = ev.get("thread_ts")
                    chan = ev.get("channel")
                    msg = ev.get("text", "")
                    user = ev.get("user")
                    ts = ev.get("ts")
                    is_im = chan and chan[0] == "D"
                    is_mention = msg and self.dm_token in msg
                    mfb_type = None

                    if is_mention:
                        # get rid of @metaflow
                        msg = msg.replace(self.dm_token, "")

                    # Type 1: State messages in the state thread.
                    # Unfortunately Slack doesn't give us the channel ID,
                    # so we must ensure that this is a state message
                    # otherwise.
                    if thread_ts == admin_thread and self.state.is_state_message(msg):
                        mfb_type = "state_change"

                    # To identify messsagae by bots we can now just check for bot_id
                    elif "bot_id" not in ev:
                        # Type 2: User messages in an existing thread. We
                        # ignore MFB's replies in existing threads.
                        if self.state.is_known_thread(chan, thread_ts):
                            mfb_type = "user_message"

                        # Type 3: Messages mentioning @metaflow that are not
                        # in existing threads. They activate new threads.
                        elif is_mention or is_im:
                            mfb_type = "new_thread"
                            if not thread_ts:
                                # this is not an existing thread, so the thread_ts
                                # is the parent event ts.
                                thread_ts = ts
                    if mfb_type:
                        yield Event(
                            type=mfb_type,
                            msg=msg.strip(),
                            is_mention=is_mention,
                            user=user,
                            user_name=self.state.user_name(user),
                            chan=chan,
                            is_im=is_im,
                            is_direct=is_im or is_mention,
                            chan_name=self.state.channel_name(chan),
                            ts=ts,
                            thread_ts=thread_ts,
                        )
            except GeneratorExit:
                pass
            except:
                traceback.print_exc()
                self.logger(
                    str(ev), head="Ignored a bad message: ", system_msg=True, bad=True
                )

    def _update_state(self, event):
        if not self.state.update(event):
            self.logger(
                str(event),
                head="Ignored a bad state message: ",
                system_msg=True,
                bad=True,
            )

    def _apply_rule(self, event):
        match = self.rules.match(event, self.state)
        if match:
            rule_name, action, msg_groups, context_update = match
            self.logger(rule_name, head="  -> Invoking rule: ")
            # if the rule matched a state change event, we want to
            # send replies to the originating thread, not to the
            # admin thread of the event
            reply_thread = self.state.get_thread(event)
            self._take_action(event, reply_thread, msg_groups, **action)
            if context_update:
                # ephemeral context update. Normally thread state (context)
                # gets updated via events in the admin thread but there are
                # a few cases where we need to update the state in the same
                # "transaction" with rule evaluation, e.g. to prevent the
                # same rule being invoked multiple times. This code path
                # serves this purpose.
                self.state.update_thread(reply_thread, context_update)

    def _take_action(
        self, event, reply_thread="", msg_groups="", op=None, **action_spec
    ):

        # click demands that local is set to UTF-8
        env = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}

        # use a custom cache location, to make sure our
        # action user has permissions to use it
        env["METAFLOW_CLIENT_CACHE_PATH"] = "metaflow_client_cache"

        if "PATH" in os.environ:
            # sys.executable does not work in subprocesses
            # if PATH is not set
            env["PATH"] = os.environ["PATH"]

        if "PYTHONPATH" in os.environ:
            env["PYTHONPATH"] = os.environ["PYTHONPATH"]

        # Use the Parent server thread's environment variables.
        env.update({k: os.environ[k] for k in os.environ if k not in env})
        cmd = []
        # We don't need app-token because only calling
        # server needs an app token.
        cmd += [
            sys.executable,
            "-m",
            "metaflowbot",
            "--slack-bot-token",
            self.sc.token,
            "--admin-thread",
            "%s:%s" % (self.admin_chan, self.admin_thread),
            "--reply-thread",
            reply_thread,
        ]

        cmd.extend(("action", op))
        context = FormatFriendlyDict(self.state.get_thread_state(reply_thread))
        try:
            for k, v in action_spec.items():
                if isinstance(v, bool):
                    cmd.append("--%s%s" % ("" if v else "no-", k))
                else:
                    tmpl = str(v).format(
                        event=event, context=context, message_group=msg_groups
                    )
                    # note: empty strings are currently not supported as valid
                    # values, since we need them to denote missing values
                    if tmpl:
                        cmd.extend(("--%s" % k, tmpl))
            subprocess.Popen(
                cmd,
                env=env,
                # don't inherit signals (esp SIGINT) in children
                preexec_fn=os.setpgrp,
            )
        except:
            traceback.print_exc()
            self.logger(
                str(cmd),
                head="Taking action (%s) failed: " % op,
                system_msg=True,
                bad=True,
            )
