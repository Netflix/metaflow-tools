import math
import re
from collections import namedtuple
from datetime import datetime

import timeago
from metaflow import Flow, namespace
from metaflow.exception import MetaflowNotFound

from metaflowbot.message_templates.templates import DATEPARSER

ResolvedRun = namedtuple("ResolvedRun", ["id", "flow", "who", "when"])

ResolvedStep = namedtuple(
    "ResolvedStep",
    [
        "num_tasks",
        "name",
        "started_on",
        "finished_at",
        "step_runtime",
    ],
)


class RunResolverException(Exception):
    def __init__(self, flow):
        self.flow = flow

    def __str__(self):
        return "Couldn't find the run. :meow_dead: "


class RunNotFound(RunResolverException):
    def __init__(self, flow):
        super().__init__(flow)


class RunSyntaxError(RunResolverException):
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return (
            "Hmm, I am not sure what you mean. Type "
            "`how to %s` for help." % self.command
        )


class FlowNotFound(RunResolverException):
    def __str__(self):
        return (
            "Flow `%s` not found. Note that flow names are "
            "case-sensitive." % self.flow
        )


class NoRuns(RunResolverException):
    def __init__(self, flow, command):
        self.flow = flow
        self.command = command

    def __str__(self):
        return (
            "I couldn't find any runs with the given spec. "
            "You can see a list of runs if you specify just the "
            "flow name, `%s %s`." % (self.command, self.flow)
        )


STYLES = [  # [Run/ID]
    "(?P<flow>[a-z0-9_]+)/(?P<runid>[a-z0-9_\-]+)",
    # (someone's / the) (latest run of) [flow], (tagged tag)
    "((?P<user>[a-z]+)'s?|the)? ?(?P<latest>latest run of )?"
    "(?P<flow>[a-z0-9_]+),?( tagged (?P<tag>.+))?",
]

PARSER = [re.compile(x, re.IGNORECASE) for x in STYLES]



def running_time(run):
    try:
        if run.finished:
            if run.successful:
                mins = (
                    DATEPARSER(run.finished_at) - DATEPARSER(run.created_at)
                ).total_seconds() / 60
                return mins
    except:
        pass
    return None


def datetime_response_parsing(secs):
    if secs < 60:
        return "%d %s" % (secs,'second' if secs == 1 else 'seconds')
    elif secs < (60 * 60):  # If less than one hour
        return "%d %s" % (secs / 60, 'minute' if int(secs / 60) == 1 else 'minutes')
    elif secs < (24 * 60 * 60):  # If less than one day
        num_hours = math.floor(secs / (60 * 60))
        num_mins = (secs % (60 * 60)) / 60
        hr_str = 'hours' if num_hours > 1 else 'hour'
        min_str = 'minutes' if num_mins > 1 else 'minute'
        return "%d %s and %d %s" % (num_hours, hr_str, num_mins, min_str)
    else:  # More than a day
        num_days = math.floor(secs / (24 * 60 * 60))
        num_hours = (secs % (24 * 60 * 60)) / (60 * 60)
        hr_str = 'hours' if num_hours > 1 else 'hour'
        day_str = 'days' if num_days > 1 else 'day'
        return "%d %s and %d %s" % (num_days, day_str, num_hours, hr_str)


def step_runtime(tasks):
    # Code dies here at times because
    # t.finished_at is somehow linked to S3
    # More info at : https://github.com/Netflix/metaflow/blob/48e37bea3ea4e83ddab8227869bbe56b52d9957d/metaflow/client/core.py#L956
    if tasks:
        try:
            end = [
                DATEPARSER(t.finished_at) for t in tasks if t.finished_at is not None
            ]
            if all(end) and len(end) > 0:
                secs = (max(end) - DATEPARSER(tasks[-1].created_at)).total_seconds()
                return datetime_response_parsing(secs)
        except:
            pass
    return "?"


class RunResolver(object):
    def __init__(self, command):
        self.command = command

    def resolve(self, msg, max_runs=5):
        match = None
        if msg.startswith(self.command):
            msg = msg[len(self.command) :].strip()
            match = list(filter(None, [p.match(msg) for p in PARSER]))
        if match:
            query = match[0].groupdict()
            runs = list(self._query(query, max_runs))
            if runs:
                return runs
            else:
                raise NoRuns(query["flow"], self.command)
        else:
            raise RunSyntaxError(self.command)

    def format_runs(self, runs, run_filter):
        msg = ["I found these runs:"]
        example = None
        for run in runs:
            exclude = run_filter(run)
            if not exclude and not example:
                example = run.id
            msg.append(
                " - {x}`{run.id}`{x} _by {run.who}, {when}_ {reason}".format(
                    run=run,
                    when=timeago.format(DATEPARSER(run.when), now=datetime.utcnow()),
                    x="~" if exclude else "",
                    reason="(%s)" % exclude if exclude else "",
                )
            )
        if example:
            msg.append(
                "Choose one of the run IDs above by writing e.g. "
                "`%s %s`" % (self.command, example)
            )
        else:
            msg.append(
                "It seems none of these runs were eligible. Try "
                "another query (try `how to %s` for ideas)" % self.command
            )
        return "\n".join(msg)

    def _query(self, query, max_runs):
        def _resolved_run(run):
            return ResolvedRun(
                id=run.pathspec,
                who=find_user(run),
                flow=run.pathspec.split("/")[0],
                when=run.created_at,
            )

        try:
            namespace(None)
            flow = Flow(query["flow"])
        except MetaflowNotFound:
            raise FlowNotFound(query["flow"])

        runid = query.get("runid")
        if runid:
            try:
                runs = [flow[runid]]
            except KeyError:
                raise RunNotFound(flow)
        else:
            tags = []
            if query.get("tag"):
                tags.append(query["tag"])
            if query.get("user"):
                tags.append("user:" + query["user"])
            runs = list(flow.runs(*tags))
            if query.get("latest"):
                runs = runs[:1]
        return map(_resolved_run, runs[:max_runs])

    def howto(self):
        return (
            "There are a number of ways to refer to an existing run:\n"
            " - Use an existing run ID: `{cmd} HelloFlow/12`.\n"
            " - Use a flow name: `{cmd} HelloFlow`.\n"
            " - Use a flow name with a user: `{cmd} dberg's HelloFlow`.\n"
            " - Use the latest run of a user: `{cmd} dberg's latest run of HelloFlow`.\n"
            " - Use the latest run by anyone: `{cmd} the latest run of HelloFlow`.\n"
            "You can filter by a tag by appending `tagged some_tag` in any of the "
            "expressions above except the first one. If there are multiple "
            "eligible runs, I will show you a list of run IDs to choose from.".format(
                cmd=self.command
            )
        )


def find_user(run):
    usrlst = [tag for tag in run.tags if tag.startswith("user:")]
    if usrlst:
        return usrlst[0][5:]
    else:
        return "unknown"


if __name__ == "__main__":
    import sys

    print("\n".join(map(str, RunResolver("use code from").resolve(sys.argv[1]))))
