import re
from collections import namedtuple
from datetime import datetime

import timeago
from metaflow import Flow, namespace
from metaflow.exception import MetaflowNotFound

from metaflowbot.message_templates.templates import DATEPARSER

ResolvedRun = namedtuple('ResolvedRun',
                         ['id',
                          'flow',
                          'who',
                          'when',
                          'finished',
                          'successful',
                          'errored',
                          'running',
                          'running_time',
                          'tags'])

ResolvedStep = namedtuple('ResolvedStep',[
    'num_tasks',
    'name',
    'started_on',
    'finished_at',
    'step_runtime',
])
class RunResolverException(Exception):
    def __init__(self, flow):
        self.flow = flow

    def __str__(self):
        return "Couldn't find the RunID. :meow_dead: "
class RunNotFound(RunResolverException):
    def __init__(self, flow,runid):
        super().__init__(flow)

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
          "(?P<flow>[a-z0-9_]+)/(?P<runid>[a-z0-9_\-]+)",
          # (someone's / the) (latest run of) [flow], (tagged tag)
          "((?P<user>[a-z]+)'s?|the)? ?(?P<latest>latest run of )?"\
          "(?P<flow>[a-z0-9_]+),?( tagged (?P<tag>.+))?"
         ]

PARSER = [re.compile(x, re.IGNORECASE) for x in STYLES]


def find_origin_id(run):
    """find_origin_id
    Needs to be better
    """
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


def running_time(run):
    try:
        if run.finished:
            if run.successful:
                mins = (DATEPARSER(run.finished_at) - DATEPARSER(run.created_at)).total_seconds() / 60
                return mins
    except:
        pass
    return None

def step_runtime(tasks):
    # Code dies here at times because
    # t.finished_at is somehow linked to S3
    # More info at : https://github.com/Netflix/metaflow/blob/48e37bea3ea4e83ddab8227869bbe56b52d9957d/metaflow/client/core.py#L956
    if tasks:
        try:
            end = [DATEPARSER(t.finished_at) for t in tasks if t.finished_at is not None]
            if all(end) and len(end) >0 :
                secs = (max(end) - DATEPARSER(tasks[-1].created_at)).total_seconds()
                if secs < 60:
                    return '%ds' % secs
                else:
                    return '%dmin' % (secs / 60)
        except:
            pass
    return '?'

class RunResolver(object):

    def __init__(self, command):
        self.command = command

    def resolve(self, msg, max_runs=3):
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

    def _query(self, query, max_runs):
        def _resolved_run(run):
            flow_running = run.finished_at is None
            return ResolvedRun(id=run.pathspec,
                                tags=run.tags,
                               who=find_user(run),
                               flow= run.pathspec.split('/')[0],
                               when=run.created_at,
                               running_time=running_time(run),
                                finished = run.finished,
                                successful = run.successful,
                                errored= not flow_running and not run.successful,
                                running = flow_running)

        try:
            namespace(None)
            flow = Flow(query['flow'])
        except MetaflowNotFound:
            raise FlowNotFound(query['flow'])

        runid = query.get('runid')
        if runid:
            try:
                runs = [flow[runid]]
            except KeyError:
                raise RunNotFound(flow,runid)
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


def find_user(run):
    usrlst = [tag for tag in run.tags if tag.startswith('user:')]
    if usrlst:
        return usrlst[0][5:]
    else:
        return 'unknown'

if __name__ == '__main__':
    import sys
    print('\n'.join(map(str, RunResolver('use code from').resolve(sys.argv[1]))))
