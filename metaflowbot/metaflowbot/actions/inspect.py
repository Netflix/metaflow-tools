import json
import traceback
from datetime import datetime
from urllib.parse import urlparse

import click
import timeago
from metaflow import Metaflow, Run, namespace
from metaflow.datastore.util.s3util import get_s3_client
from metaflow.exception import MetaflowNotFound

from ..cli import action
from ..message_templates.templates import DATEPARSER, HowToInspect, ListFlows
from ..state import MFBState
from .run_resolver import RunResolver, RunResolverException, find_user

MAX_ARTIFACT_SIZE = 1000

@action.command(help="List all flows associated with the metadata service")
@click.pass_context
def list_flows(ctx,):
    obj = ctx.obj
    reply_list_flows(obj)

@action.command(help="Set a new run to be inspected")
@click.option('--runspec',
              help="A query to find a run to inspect")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_context
def inspect_run(ctx, runspec=None, howto=False):
    obj = ctx.obj
    resolver = RunResolver('inspect run')
    if howto:
        obj.reply(' ',blocks=HowToInspect)
    else:
        try:
            obj.reply("Searching runs. Just a minute...")
            runs = resolver.resolve(runspec)
            if len(runs) == 1:
                attrs = {'inspect.run_id': runs[0].id}
                state = MFBState.message_set_attributes(obj.thread, attrs)
                obj.publish_state(state)
                obj.reply("Ok, inspecting *%s*." % (runs[0].id))
                ctx.invoke(inspect, run_id=runs[0].id)
            else:
                reply,blocks = resolver.format_runs(runs, lambda _: None)
                obj.reply(reply,blocks=blocks)
        except RunResolverException as ex:
            obj.reply(str(ex))

@action.command(help="Inspect data of a step")
@click.option('--run-id',
              required=True,
              help="Run ID to inspect")
@click.option('--step',
              required=True,
              help="Step to inspect")
@click.pass_obj
def inspect_data(obj, run_id=None, step=None):
    try:
        # This step is HUGEE!
        # TODO : Change Response template here.
        # Todo : find way to cleanly work around bottleneck induced by large artifacts.
        reply_step_info(obj, run_id, step, data_info)
    except:
        traceback.print_exc()
        obj.reply("Sorry, something went wrong. Try again after a while.")

@action.command(help="Inspect logs at a step")
@click.option('--run-id',
              required=True,
              help="Run ID to inspect")
@click.option('--step',
              required=True,
              help="Step to inspect")
@click.pass_obj
def inspect_logs(obj, run_id=None, step=None):
    try:
        # This step is HUGEE!
        # TODO : Change Response template here.
        # Todo : find way to cleanly work around bottleneck induced by large artifacts.
        reply_step_info(obj, run_id, step, logs_info)
    except:
        traceback.print_exc()
        obj.reply("Sorry, something went wrong. Try again after a while.")

@action.command(help="Inspect the current run or show help text")
@click.option('--run-id',
              help="Run ID to inspect")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_obj
def inspect(obj, run_id=None, howto=False):
    if howto:
        obj.reply(' ',blocks=HowToInspect)
    else:
        try:
            reply_inspect(obj, run_id)
        except:
            traceback.print_exc()
            obj.reply("Sorry, something went wrong. Try again after a while.")

def reply_list_flows(obj):
    obj.reply(f"Alright, Listing Flows, Just a second")
    try:
        flows = Metaflow().flows
        main_flow_meta = []
        # blocks = ListFlowsTemplate().make_attachments(flows)
        blocks = ListFlows().get_slack_message(flows)
        # obj.reply(f":star: Found {len(flows)} Flows !",attachments=blocks)
        obj.reply(f":star: Found {len(flows)} Flows !",blocks=blocks)
    except Exception as e:
        obj.reply(dict(text=':skull_and_crossbones: Oops something went wrong'))


def reply_step_info(obj, run_id, step_name, info_func):
    obj.reply("Fetching info. This may take a minute...")
    namespace(None)
    run = Run(run_id)
    try:
        step = run[step_name]
    except KeyError:
        obj.reply("No such step, *%s*. Try `inspect` to see available steps."\
                  % step_name)
    else:
        obj.reply("Tasks of *%s/%s*:" % (run_id, step_name),
                  attachments=list(info_func(list(step))))

def reply_inspect(obj, run_id):

    def run_status(run):
        if run.finished:
            if run.successful:
                mins = (DATEPARSER(run.finished_at) - DATEPARSER(run.created_at)).total_seconds() / 60
                return "It ran for %d minutes and finished successfully." % mins
            else:
                return "It did not finish successfully."
        else:
            return "It has not finished."

    def step_runtime(tasks):
        if tasks:
            end = [DATEPARSER(t.finished_at) for t in tasks if t.finished_at is not None]
            if all(end) and len(end) >0 :
                secs = (max(end) - DATEPARSER(tasks[-1].created_at)).total_seconds()
                if secs < 60:
                    return '%ds' % secs
                else:
                    return '%dmin' % (secs / 60)
        return '?'

    namespace(None)
    run = Run(run_id)
    ago = timeago.format(DATEPARSER(run.created_at), now=datetime.utcnow())
    head = ['Run *%s* was started %s by _%s_.' % (run_id, ago, find_user(run)),
            run_status(run),
            'Tags: %s' % ', '.join('`%s`' % tag for tag in run.tags),
            'Steps:']
    steps = list(run)
    sects = []
    for step in reversed(steps):
        tasks = list(step)
        if all(task.successful for task in tasks):
            color = 'good'
            status = 'All tasks finished successfully.'
        else:
            color = 'warning'
            status = 'Some tasks failed or are still running.'

        fields = [{'title': 'Status',
                   'value': status,
                   'short': False},
                  {'title': 'Runtime',
                   'value': step_runtime(tasks),
                   'short': True},
                  {'title': 'Tasks Started',
                   'value': len(tasks),
                   'short': True}]
        sects.append({'fallback': 'step %s' % step.id,
                      'title': 'Step: ' + step.id,
                      'fields': fields,
                      'color': color})
    obj.reply('\n'.join(head), attachments=sects)

def logs_info(tasks):

    def clean_logs(logs, prefix):
        l = len(prefix)
        def clean(line):
            if line.startswith(prefix):
                return line[l:]
        return '\n'.join(map(clean, logs.splitlines()))

    for task in reversed(tasks):

        meta = task.metadata_dict
        fields = []
        prefix = None

        for stream, label in (('stdout', 'Standard Output'),
                              ('stderr', 'Standard Error')):
            try:
                logs = getattr(task, stream)[-10000:]
                if prefix:
                    logs = clean_logs(logs, prefix)
            except:
                logs = '[Could not fetch logs]'

            if logs:
                fields.append({'title': label,
                               'value': '```%s```' % logs,
                               'short': False})

        yield {'fallback': 'task %s' % task.id,
               'title': ':star: Task ID: %s :star:' % task.id,
               'fields': fields,
               'mrkdwn_in': ['fields']}

def data_info(tasks):

    s3, _ = get_s3_client()
    def artifact_size(s3_url):
        url = urlparse(s3_url)
        try:
            resp = s3.head_object(Bucket=url.netloc, Key=url.path.lstrip('/'))
            return resp['ContentLength']
        except:
            return None

    for task in reversed(tasks):
        fields = []
        for art in task:
            size = artifact_size(art._object['location'])
            if size is None or size > MAX_ARTIFACT_SIZE:
                value = '[value too big]'
            else:
                try:
                    value = str(art.data)[:200]
                except:
                    value = '[could not parse the value]'
            fields.append({'title': art.id,
                           'value': value,
                           'short': False})
        yield {'fallback': 'task %s' % task.id,
               'title': ':star: Task ID: %s :star:' % task.id,
               'fields': fields}


def howto_inspect():
    return "`inspect` uses the Metaflow Client API to inspect (meta)data "\
           "about past or ongoing runs. First, you need to specify a run "\
           "to be inspected with `inspect run`. For more information how "\
           "to find and specify runs, type `how to inspect run`.\n\n"\
           "After you have specified a run, you can use the following "\
           "commands:\n"\



def howto_inspect_run(resolver):
    return\
"Use `inspect run` to specify the run to inspect. The run "\
"can be running currently (it does not have to be finished) or "\
"it can be any historical run. %s" % resolver.howto()
