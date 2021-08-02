import traceback
from datetime import datetime

import click
import timeago
from metaflow import Run, namespace
from metaflow.client.filecache import FileCacheException
from metaflow.exception import MetaflowNotFound

from metaflowbot.cli import action
from metaflowbot.message_templates.templates import (DATEPARSER,
                                                     DEFAULT_ERROR_MESSAGE,
                                                     HEADINGS,
                                                     SLACK_MAX_BLOCKS,
                                                     error_message)
from metaflowbot.state import MFBState

from .run_resolver import (ResolvedRun, RunNotFound, RunResolver,
                           RunResolverException, datetime_response_parsing,
                           find_user, step_runtime)


@action.command(help="Set a new run to be inspected")
@click.option("--runspec", help="A query to find a run to inspect")
@click.option("--howto/--no-howto", help="Only show help text")
@click.pass_context
def inspect_run(ctx, runspec=None, howto=False):
    obj = ctx.obj
    resolver = RunResolver("inspect")
    if howto:
        obj.reply(howto_inspect_run(resolver))
    else:
        try:
            obj.reply("Searching runs. Just a minute...")
            runs = resolver.resolve(runspec)
            if len(runs) == 1:
                attrs = {"inspect.run_id": runs[0].id}
                state = MFBState.message_set_attributes(obj.thread, attrs)
                obj.publish_state(state)
                obj.reply("Ok, inspecting *%s*." % (runs[0].id))
                ctx.invoke(inspect, run_id=runs[0].id)
            else:
                reply = resolver.format_runs(runs, lambda _: None)
                obj.reply(reply)
        except RunResolverException as ex:
            obj.reply(str(ex))
        except RunNotFound as ex:
            obj.reply(str(ex))
        except Exception as e:
            traceback.print_exc()
            my_traceback = traceback.format_exc()
            obj.reply(DEFAULT_ERROR_MESSAGE, **error_message(my_traceback))


@action.command(help="Inspect the current run or show help text")
@click.option("--run-id", help="Run ID to inspect")
@click.option("--create-thread/--no-create-thread", help="Will create a new thread")
@click.option("--howto/--no-howto", help="Only show help text")
@click.pass_obj
def inspect(obj, run_id=None, create_thread=False, howto=False):
    resolver = RunResolver("inspect")
    if create_thread:
        obj.publish_state(MFBState.message_new_thread(obj.thread))
    if howto:
        obj.reply(howto_inspect_run(resolver))
    else:
        try:
            reply_inspect(obj, run_id)
        except MetaflowNotFound as e:
            obj.reply(HEADINGS.NO_RUNS.value)
        except FileCacheException as e:
            obj.reply(HEADINGS.NO_S3_DATASTORE.value)
        except:
            traceback.print_exc()
            my_traceback = traceback.format_exc()
            obj.reply(DEFAULT_ERROR_MESSAGE, **error_message(my_traceback))


def run_status(run):
    try:
        if run.finished:
            if run.successful:
                parsed_time_string = datetime_response_parsing(
                    (
                        DATEPARSER(run.finished_at) - DATEPARSER(run.created_at)
                    ).total_seconds()
                )
                return "It ran for %s and finished successfully." % parsed_time_string
            else:
                return "It did not finish successfully."
        else:
            return "It has not finished."
    except FileCacheException as e:
        # in case of local ds and service MD
        return ""

def are_tasks_success(tasks):
    if all(task.successful for task in tasks):
        return True
    else:
        return False


def reply_inspect(obj, run_id):

    # max_steps is added because slack has a limit on how large a payload
    # can be sent to slack.
    def step_resolver(steps, max_steps=SLACK_MAX_BLOCKS):
        sects = []
        for idx, step in enumerate(reversed(steps)):
            if idx > max_steps:
                break
            tasks = list(step)
            local_ds = False
            if tasks[0].metadata_dict['ds-type'] == 'local':
                # As task.successful is linked to S3
                # https://github.com/Netflix/metaflow/blob/9f832e62b3d4288acae8de483dc5709d660dc347/metaflow/client/core.py#L904
                local_ds = True
            if not local_ds:
                task_success_flag = are_tasks_success(tasks)

            if local_ds:
                color = "warning"
                status = "Unable to get task status."
            elif task_success_flag:
                color = "good"
                status = "All tasks finished successfully."
            else:
                color = "warning"
                status = "Some tasks failed or are still running."

            fields = [
                {"title": "Status", "value": status, "short": False},
                {"title": "Runtime", "value": step_runtime(tasks), "short": True},
                {"title": "Tasks Started", "value": len(tasks), "short": True},
            ]
            sects.append(
                {
                    "fallback": "step %s" % step.id,
                    "title": "Step: " + step.id,
                    "fields": fields,
                    "color": color,
                }
            )
        return sects,local_ds

    def make_resolved_run(run: Run, total_steps=0, max_steps=SLACK_MAX_BLOCKS):
        resolved_run = ResolvedRun(
            id=run.pathspec,
            who=find_user(run),
            flow=run.pathspec.split("/")[0],
            when=run.created_at,
        )
        ago = timeago.format(DATEPARSER(resolved_run.when), now=datetime.utcnow())
        run_stat = run_status(run)
        head = [
            "Run *%s* was started %s by _%s_."
            % (resolved_run.id, ago, resolved_run.who),
            run_stat,
            "Tags: %s" % ", ".join("`%s`" % tag for tag in run.tags),
            "Steps:"
            if total_steps <= max_steps
            else f"Showing {max_steps}/{total_steps} Steps:",
        ]
        return "\n".join(head)

    namespace(None)
    run = Run(run_id)
    steps = list(run)
    resolved_run_info = make_resolved_run(run, total_steps=len(steps))
    attachments,local_ds = step_resolver(steps)
    blocks = []
    if local_ds:
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text":resolved_run_info }},
            {
                "type":"divider"
            },
            {
                "type":"context",
                "elements":[{
                    "type":"mrkdwn",
                    "text":"Some information (duration/status) couldn't be "\
                        "determined since the flow ran " \
                        "with datastore configured to local filesystem."
                        }]
            }
        ]
        obj.reply(resolved_run_info,attachments=attachments,blocks=blocks)
    else:
        obj.reply(resolved_run_info,attachments=attachments)


def howto_inspect_run(resolver):
    return (
        "Use `inspect` to specify the run to inspect. The run "
        "can be running currently (it does not have to be finished) or "
        "it can be any historical run. %s" % resolver.howto()
    )
