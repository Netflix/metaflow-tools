# TODO : Remove Module
import click

from ..cli import action
from ..code import MFBCode
from ..state import MFBState
from .run_resolver import RunResolver, RunResolverException

COMMAND = 'use code from'

@action.command(help='use_code')
@click.option('--codespec',
              default='',
              help="Code location spec")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_obj
def use_code(obj, codespec='', howto=False):
    resolver = RunResolver(COMMAND)
    if howto:
        obj.reply(howto_message(resolver))
    else:
        try:
            obj.reply("Searching runs. Just a minute...")
            runs = resolver.resolve(codespec)
            if len(runs) == 1:
                run = runs[0]
                if run.code_package:
                    obj.reply("Ok. I will be cloning the code of `%s` "
                              "for the next run." % run.id)
                    # note that we must remove any parameters set
                    attrs = {'use_code.run_id': run.id,
                             'parameters': None,
                             'parameter_csv': None}
                    state = MFBState.message_set_attributes(obj.thread, attrs)
                    obj.publish_state(state)
                    # since other actions will most likely need this run soon,
                    # we can as well start loading the code package, so it will
                    # be available in the cache
                    MFBCode(run.id).load()
                else:
                    flow = run.id.split('/')[0]
                    obj.reply("The chosen run, `%s`, was not run on "
                              "remotely so it doesn't have its code "
                              "persisted. Try `use code from %s` to "
                              "see a list of runs." % (run.id, flow))
            else:
                def run_filter(run):
                    if not run.code_package:
                        return 'not a remote run'
                reply = resolver.format_runs(runs, run_filter)
                obj.reply(reply)
        except RunResolverException as ex:
            obj.reply(str(ex))

def howto_message(resolver):
    return\
"Use `use code from` to specify what code to run. You need to "\
"specify an existing run whose code can be cloned for a "\
"new run. %s" % resolver.howto()
