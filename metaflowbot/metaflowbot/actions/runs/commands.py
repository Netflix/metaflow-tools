import json
import traceback
from datetime import datetime
from urllib.parse import urlparse

import click
import timeago
from metaflow import Run, namespace
from metaflow.datastore.util.s3util import get_s3_client
from metaflow.exception import MetaflowNotFound

from metaflowbot.cli import action
from metaflowbot.message_templates.templates import (DATEPARSER,
                                                     DEFAULT_ERROR_MESSAGE,
                                                     HEADINGS,
                                                     SLACK_MAX_BLOCKS)
from metaflowbot.state import MFBState

from .response_templates import (InspectHelp, InspectRunResponse, RunResponse,
                                 make_help)
from .run_resolver import (ResolvedRun, ResolvedStep, RunNotFound, RunResolver,
                           RunResolverException, find_origin_id, find_user,
                           running_time, step_runtime)


@action.command(help="Set a new run to be inspected")
@click.option('--runspec',
              help="A query to find a run to inspect")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_context
def inspect_run(ctx, runspec=None, howto=False):
    obj = ctx.obj
    resolver = RunResolver('inspect')
    if howto:
        reply,blocks = InspectHelp(help_blocks=make_help('inspect')).make_help()
        obj.reply(reply,blocks=blocks)
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
                blocks = RunResponse().get_slack_message(runs)
                obj.reply("inspect_run Response",blocks=blocks)
        except RunResolverException as ex:
            obj.reply(str(ex))
        except RunNotFound as ex:
            obj.reply(str(ex))
        except Exception as e:
            traceback.print_exc()
            obj.reply(DEFAULT_ERROR_MESSAGE)

@action.command(help="Inspect the current run or show help text")
@click.option('--run-id',
              help="Run ID to inspect")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_obj
def inspect(obj, run_id=None, howto=False):
    if howto:
        reply,blocks = InspectHelp(help_blocks=make_help('inspect')).make_help()
        obj.reply(reply,blocks=blocks)
    else:
        try:
            reply_inspect(obj, run_id)
        except MetaflowNotFound as e:
            obj.reply(HEADINGS.NO_RUNS.value)
        except:
            traceback.print_exc()
            obj.reply(DEFAULT_ERROR_MESSAGE)


def run_status(run):
    if run.finished:
        if run.successful:
            mins = (DATEPARSER(run.finished_at) - DATEPARSER(run.created_at)).total_seconds() / 60
            return "It ran for %d minutes and finished successfully." % mins
        else:
            return "It did not finish successfully."
    else:
        return "It has not finished."



def reply_inspect(obj, run_id):

    # max_steps is added because slack has a limit on how large a payload
    # can be sent to slack.
    def step_resolver(steps,max_steps=SLACK_MAX_BLOCKS):
        sects = []
        for idx,step in enumerate(reversed(steps)):
            if idx > max_steps:
                break
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
        return sects

    def make_resolved_run(run:Run,total_steps = 0,max_steps=SLACK_MAX_BLOCKS):
        flow_running = run.finished_at is None
        resolved_run = ResolvedRun(id=run.pathspec,
                            tags=run.tags,
                            running_time=running_time(run),
                            who=find_user(run),
                            flow= run.pathspec.split('/')[0],
                            when=run.created_at,
                            finished = run.finished,
                            successful = run.successful,
                            errored= not flow_running and not run.successful,
                            running = flow_running)
        ago = timeago.format(DATEPARSER(resolved_run.when), now=datetime.utcnow())
        head = ['Run *%s* was started %s by _%s_.' % (resolved_run.id, ago, resolved_run.who),
                run_status(run),
                'Tags: %s' % ', '.join('`%s`' % tag for tag in resolved_run.tags),
                'Steps:' if total_steps <= max_steps else f"Showing {max_steps}/{total_steps} Steps:"]
        return '\n'.join(head)
    namespace(None)
    run = Run(run_id)
    steps = list(run)
    resolved_run = make_resolved_run(run,total_steps=len(steps))
    attachments = step_resolver(steps)
    obj.reply(resolved_run,\
            attachments=attachments)
