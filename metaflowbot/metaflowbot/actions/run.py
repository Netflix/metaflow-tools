# TODO : Remove Module
import os
import time
import json

import click

from ..cli import action
from ..state import MFBState
from ..code import MFBCode
from ..rungroup import MFBRunGroup
from .parameter_utils import read_parameter_csv, get_parameters

RUN_STATUS_INTERVAL = 15 * 60

@action.command(help='Start and manage one or more Metaflow runs')
@click.option('--code-run-id',
              required=True,
              help="Run ID for the code package")
@click.option('--username',
              help="User name for the run")
@click.option('--parameters',
              default='{}',
              help="a JSON object defining parameters for a single run")
@click.option('--parameter-csv',
              help="Slack permalink to a parameter CSV defining multiple runs")
@click.option('--tags',
              default='',
              help="Assign tags, specified as a comma separated list, "
                   "to this run.")
@click.pass_obj
def run(obj,
        tags=None,
        code_run_id=None,
        username=None,
        parameters=None,
        parameter_csv=None):

    rungroup_id = '%d-%d' % (time.time() * 1000, os.getpid())
    attrs = {'is_running': True,
             'rungroup_id': rungroup_id,
             'inspect.run_id': None}
    obj.publish_state(MFBState.message_enable_monitor(obj.thread))
    obj.publish_state(MFBState.message_set_attributes(obj.thread, attrs))
    try:
        if username:
            _run(obj,
                 rungroup_id,
                 code_run_id,
                 username,
                 json.loads(parameters),
                 parameter_csv,
                 tags.split(','))
        else:
            obj.reply("Sorry! I could not figure out your username. "
                      "Try again later.")
    finally:
        run_finished(obj)

@action.command(help="Cancel a run(group)")
@click.option('--rungroup-id',
              required=True,
              help="Rungroup ID, produced by 'run'")
@click.pass_obj
def cancel_runs(obj, rungroup_id=None):
    if rungroup_id:
        obj.reply("Cancelling runs. Just a minute..")
        group = MFBRunGroup(rungroup_id)
        group.add_indicator('cancel')
    else:
        obj.reply("Nothing was running yet. Try again in a minute.")

@action.command(help="Show run status")
@click.option('--rungroup-id',
              required=True,
              help="Rungroup ID, produced by 'run'")
@click.pass_obj
def run_status(obj, rungroup_id=None):
    group = MFBRunGroup(rungroup_id)
    group.add_indicator('show_status')

@action.command(help="Disable automatic run status")
@click.option('--rungroup-id',
              required=True,
              help="Rungroup ID, produced by 'run'")
@click.pass_obj
def quiet_run(obj, rungroup_id=None):
    group = MFBRunGroup(rungroup_id)
    group.add_indicator('quiet')
    obj.reply("Ok, I won't bother you anymore with automatic status updates.")

@action.command(help="Clean up a lost run")
@click.option('--fingerprint',
              help="Fingerprint of the process that was lost")
@click.pass_obj
def cleanup_lost_run(obj, fingerprint=None):
    obj.reply("I am sorry but it seems that the Metaflow run(s) that "
              "were started in this thread got lost. This should be "
              "a transient failure, so feel free to `run` again.")
    run_finished(obj, fingerprint)

def run_finished(obj, fingerprint=None):
    attrs = {'is_running': False, 'rungroup_id': None}
    obj.publish_state(MFBState.message_disable_monitor(obj.thread, fingerprint))
    obj.publish_state(MFBState.message_set_attributes(obj.thread, attrs))

def _run(obj,
         rungroup_id,
         code_run_id,
         username,
         parameters,
         parameter_csv,
         tags):

    # load code
    code = MFBCode(code_run_id)
    if not code.is_cached:
        obj.reply("Loading the code package. Just a minute...")
    code.load()

    # check parameters
    if not parameter_csv:
        missing = [p['name'] for p in get_parameters(code)
                   if p['required'] and p['name'] not in parameters]
        if missing:
            obj.reply("Required parameter *%s* is missing. Type `how to set "
                      "parameters` for guidance on how to set it. Type `show "
                      "parameters` to see what parameters are required by "
                      "*%s*." % (missing[0], code.flow_name))
            return

    # start runs
    if parameter_csv:
        # start multiple runs, one per line in the CSV
        parameter_list = read_parameter_csv(obj.sc, parameter_csv)
    else:
        # start one run based on parameters set
        parameter_list = [parameters]

    group = MFBRunGroup(rungroup_id, code, username)
    for i, params in enumerate(parameter_list):
        label = params.pop('#row_id', str(i + 1))
        start_run(group,
                  label,
                  params,
                  tags + (['row_id:' + label] if parameter_csv else []))
        # this is to work around a race condition in mliservice which
        # causes concurrently launced jobs to fail
        time.sleep(1)

    if len(group) == 1:
        msg = "*{flow_name}* started!"
    else:
        msg = "I started {num} runs of *{flow_name}*, one for each row in the "\
              "CSV you specified."
    msg += " :running:\nI will post a status update "\
           "here every 15 minutes or when the run is done. You can type "\
           "`show status` to see the status any time. Type `quiet` to "\
           "disable regular status updates. You can cancel the run with "\
           "`cancel`. "
    obj.reply(msg.format(flow_name=code.flow_name, num=len(group)))

    # babysit runs. This blocks until all the runs have finished.
    statuses = manage_runs(obj, group, code.flow_name)

    failed = list(filter(lambda x: x[1].status == 'failed', statuses))
    if failed:
        if len(statuses) > 1:
            if len(statuses) == len(failed):
                msg = "All of the runs failed"
            else:
                msg = "Some of the runs failed"
        else:
            msg = "The run failed"
        obj.reply("%s :sadpanda:\nI will post error messages "
                  "below, just a sec." % msg)
        for msg in format_error_output(group, failed, code.flow_name):
            obj.reply(msg)
    elif all(s.status == 'done' for _, s in statuses):
        if len(statuses) > 1:
            obj.reply("All runs were successful! :tada:")
        else:
            obj.reply("Run was successful! :tada:")

    group.wait()

def start_run(group, run_id, parameters, tags):
    args = []
    for param, param_value in parameters.items():
        args.extend(('--%s' % param, param_value))
    group.add_run(run_id, args, tags)

def manage_runs(obj, group, flow_name):
    last_status_update = time.time()
    run_id_set = False
    while True:
        time.sleep(5)
        statuses = list(group.run_statuses())

        # if we have only one run, so we know the run id unambiguously,
        # we can set it up for inspection for user convenience. This
        # avoids one redundant `inspect run` request.
        if not run_id_set and\
           len(statuses) == 1 and statuses[0][1].run_id is not None:
            run_id_set = True
            attrs = {'inspect.run_id': '%s/%s' % (flow_name,
                                                  statuses[0][1].run_id)}
            obj.publish_state(MFBState.message_set_attributes(obj.thread, attrs))

        # should we cancel?
        if group.pop_indicator('cancel'):
            group.cancel()
            break

        # regular status updates every RUN_STATUS_INTERVAL seconds
        if group.pop_indicator('show_status') or\
           (time.time() - last_status_update > RUN_STATUS_INTERVAL and\
            not group.has_indicator('quiet')):

            last_status_update = time.time()
            table = format_status_table(statuses, flow_name)
            obj.reply('*Run status*', attachments=table)
            if run_id_set:
                if len(group) == 1:
                    obj.reply("For more details about the run, type `inspect` "\
                              "or `how to inspect`.")
                else:
                    obj.reply("For more details about the runs, specify a "\
                              "run you want inspect with `inspect run`.")
            else:
                obj.reply("You will be able to get more details about the run "
                          "soon with `inspect`. Try again after a minute.")

        # are we done?
        if all(s.status in ('done', 'failed') for _, s in statuses):
            break

    statuses = list(group.run_statuses())
    table = format_status_table(statuses, flow_name)
    obj.reply('*All done, final status*', attachments=table)
    return statuses

def run_title(run_id, status, flow_name):
    title = 'Run %s: ' % run_id
    if status.run_id:
        title += '%s/%s' % (flow_name, status.run_id)
    else:
        title += '%s/?' % flow_name
    return title

def format_error_output(group, statuses, flow_name):
    for run_id, status in statuses:
        tail = '\n'.join(group.readlines(run_id, 'stdout')[-50:])[-10000:]
        if not tail:
            tail = '\n'.join(group.readlines(run_id, 'stderr')[-50:])[-10000:]
        title = run_title(run_id, status, flow_name)
        yield "*%s* output: ```%s```" % (title, tail)

def format_status_table(statuses, flow_name):
    STATUS_COLORS = {'starting': 'warning',
                     'running': 'warning',
                     'done': 'good',
                     'cancelled': 'danger',
                     'failed': 'danger'}

    sect = []
    for run_id, status in statuses:
        fields = [{'title': 'Tags',
                   'value': ', '.join('`%s`' % tag for tag in status.tags),
                   'short': False},
                  {'title': 'Current Step',
                   'value': status.current_step,
                   'short': True},
                  {'title': 'Active Tasks',
                   'value': status.num_active_tasks,
                   'short': True},
                  {'title': 'Latest Messages',
                   'value': '```%s````' % '\n'.join(status.last_lines),
                   'short': False}]

        title = '%s %s' % (run_title(run_id, status, flow_name), status.status)
        sect.append({'fallback': title,
                     'color': STATUS_COLORS[status.status],
                     'title': title,
                     'fields': fields,
                     'mrkdwn_in': ['fields']})
    return sect
