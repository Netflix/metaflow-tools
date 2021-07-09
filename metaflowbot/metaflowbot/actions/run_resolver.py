import re
from datetime import datetime

import timeago
from metaflow import Flow, namespace
from metaflow.exception import MetaflowNotFound

from ..message_templates.templates import DATEPARSER, ResolvedRun, RunResponse


class RunResolverException(Exception):
    def __init__(self, flow):
        self.flow = flow

class RunSyntaxError(RunResolverException):
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return "Hmm, I am not sure what you mean. Type "\
               "`how to %s` for help." % self.command

class FlowNotFound(RunResolverException):
    def __str__(self):
        return "Flow `%s` not found. Note that flow names are "\
               "case-sensitive." % self.flow

class NoRuns(RunResolverException):
    def __init__(self, flow, command):
        self.flow = flow
        self.command = command

    def __str__(self):
        return "I couldn't find any runs with the given spec. "\
               "You can see a list of runs if you specify just the "\
               "flow name, `%s %s`." % (self.command, self.flow)

STYLES = [# [Run/ID]
          "(?P<flow>[a-z0-9_]+)/(?P<runid>[a-z0-9\-]+)",
          # (someone's / the) (latest run of) [flow], (tagged tag)
          "((?P<user>[a-z]+)'s?|the)? ?(?P<latest>latest run of )?"\
          "(?P<flow>[a-z0-9_]+),?( tagged (?P<tag>.+))?"
         ]

PARSER = [re.compile(x, re.IGNORECASE) for x in STYLES]


def find_origin_id(run):
    origin_run_id = None
    # TODO : Check if this can be done more efficiently.
    # Listinng all stepss in one go can be troublesome.
    for step in list(run.steps()):
        origin_run_id = step.task.metadata_dict.get('origin-run-id')
        if origin_run_id != 'None' and origin_run_id is not None:
            origin_run_id = f"{run.pathspec.split('/')[0]}/{origin_run_id}"
            break
        else:
            origin_run_id = None

    return origin_run_id


class RunResolver(object):

    def __init__(self, command):
        self.command = command

    def resolve(self, msg, max_runs=10):
        match = None
        if msg.startswith(self.command):
            msg = msg[len(self.command):].strip()
            match = list(filter(None, [p.match(msg) for p in PARSER]))
        if match:
            query = match[0].groupdict()
            runs = list(self._query(query, max_runs))
            if runs:
                return runs
            else:
                raise NoRuns(query['flow'], self.command)
        else:
            raise RunSyntaxError(self.command)

    def format_runs(self, runs, run_filter):
        blocks = RunResponse().get_slack_message(runs)
        return "Run message comes here",blocks

    def _query(self, query, max_runs):
        def _resolved_run(run):
            origin_run_id = find_origin_id(run)
            flow_running = run.finished_at is None
            return ResolvedRun(id=run.pathspec,
                                tags=run.tags,
                                origin_run_id=origin_run_id,
                               who=find_user(run),
                               flow= run.pathspec.split('/')[0],
                               when=run.created_at,
                                finished = run.finished,
                                successful = run.successful,
                                errored= not flow_running and not run.successful,
                                running = flow_running,
                               code_package=None)

        try:
            namespace(None)
            flow = Flow(query['flow'])
        except MetaflowNotFound:
            raise FlowNotFound(query['flow'])

        runid = query.get('runid')
        if runid:
            runs = [flow[runid]]
        else:
            tags = []
            if query.get('tag'):
                tags.append(query['tag'])
            if query.get('user'):
                tags.append('user:' + query['user'])
            runs = list(flow.runs(*tags))
            if query.get('latest'):
                runs = runs[:1]
        return map(_resolved_run, runs[:max_runs])

    def howto(self):
        return\
"There are a number of ways to refer to an existing run:\n"\
" - Use an existing run ID: `{cmd} HelloFlow/12`.\n"\
" - Use a flow name: `{cmd} HelloFlow`.\n"\
" - Use a flow name with a user: `{cmd} dberg's HelloFlow`.\n"\
" - Use the latest run of a user: `{cmd} dberg's latest run of HelloFlow`.\n"\
" - Use the latest run by anyone: `{cmd} the latest run of HelloFlow`.\n"\
"You can filter by a tag by appending `tagged some_tag` in any of the "\
"expressions above except the first one. If there are multiple "\
"eligible runs, I will show you a list of run IDs to choose from."\
.format(cmd=self.command)

def find_user(run):
    usrlst = [tag for tag in run.tags if tag.startswith('user:')]
    if usrlst:
        return usrlst[0][5:]
    else:
        return 'unknown'

if __name__ == '__main__':
    import sys
    print('\n'.join(map(str, RunResolver('use code from').resolve(sys.argv[1]))))
