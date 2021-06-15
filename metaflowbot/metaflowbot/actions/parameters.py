import traceback
import json

import click

from ..slack_client import MFBInvalidPermalink
from ..cli import action
from ..state import MFBState
from ..code import MFBCode
from .parameter_utils import read_parameter_csv, get_parameters

@action.command(help='parameters')
@click.option('--code-run-id',
              help="Run ID for the code package")
@click.option('--key',
              default='',
              help="Parameter name")
@click.option('--value',
              default='',
              help="Parameter value")
@click.option('--parameter-csv',
              help="Slack permalink to a new parameter CSV")
@click.option('--existing-csv',
              help="Slack permalink to existing parameter CSV")
@click.option('--existing',
              default='{}',
              help="JSON object of existing parameters set.")
@click.option('--show/--no-show',
              help="Show available parameters in the flow")
@click.option('--howto/--no-howto',
              help="Only show help text")
@click.pass_obj
def parameters(obj,
               code_run_id=None,
               key=None,
               team=None,
               parameter_csv=None,
               existing=None,
               existing_csv=None,
               value=None,
               show=False,
               howto=False):

    if howto:
        obj.reply(howto_message())
    else:
        code = MFBCode(code_run_id)
        if not code.is_cached:
            obj.reply("Loading the code package. Just a minute...")
        code.load()
        try:
            params = get_parameters(code)
        except:
            traceback.print_exc()
            obj.reply("Hmm, I was unable to parse parameters of your flow. Sorry!")
        else:
            if show:
                show_parameters(obj, params, json.loads(existing), existing_csv)
            elif parameter_csv:
                set_parameter_csv(obj, params, parameter_csv, team)
            elif existing_csv:
                obj.reply("You can't set individual parameters since parameters "
                          "are read from a CSV file. Type `how to set parameters` "
                          "for details.")
            else:
                set_parameter(obj, params, key, value)

def set_parameter_csv(obj, params, parameter_csv, team):
    try:
        param_list = read_parameter_csv(obj.sc, parameter_csv)
    except MFBInvalidPermalink:
        obj.reply("Hmm, this does not seem like a valid Slack link.")
    except:
        obj.reply("Sorry! I couldn't read the CSV file.")
    else:
        if param_list:
            # all column names must be valid parameters
            invalid = [k for k in param_list[0] if not _is_param(k, params)]
            # all required parameters must be specified on all rows
            missing_required = [p['name'] for p in params
                                if p['required'] and not\
                                all(row.get(p['name']) for row in param_list)]
            if invalid:
                obj.reply("Column *%s* does not seem like a known parameter. "
                          "Type `show parameters` to see parameters that can "
                          "be used as columns." % invalid[0])
            elif missing_required:
                obj.reply("Parameter *%s* is required but it is not defined "
                          "on all rows of the CSV." % missing_required[0])
            else:
                attrs = {'parameters': None, 'parameter_csv': parameter_csv}
                state = MFBState.message_set_attributes(obj.thread, attrs)
                obj.publish_state(state)
                obj.reply("The parameter CSV looks good! This will result to "
                          "%d concurrent runs." % len(param_list))
        else:
            obj.reply("The parameter CSV seems empty. Try with another file.")

def show_parameters(obj, params, existing, existing_csv_link):
    if params:
        def format_param(p):
            val = 'required, ' if p['required'] else ''
            if p['name'] in existing and not existing_csv_link:
                val += 'set to: %s' % existing[p['name']]
            else:
                val += 'default: %s' % p['default']
            return ' - *{p[name]}* (_{val}_): {p[help]}'.format(p=p, val=val)

        msg = ["The flow accepts the following parameters:", ""] +\
              list(map(format_param, params)) + [""]
        if existing_csv_link:
            msg += ["Parameter values are read from this CSV: %s" %\
                    existing_csv_link]
        else:
            msg += ["Set a parameter e.g. by typing "\
                    "`set parameter %s to 1`." % params[0]['name']]
        msg += ["For more details, type `how to set parameters`."]
        obj.reply('\n'.join(msg))
    else:
        obj.reply("The flow does not accept any parameters. "
                  "You can just `run` it!")

def set_parameter(obj, params, key, value):
    if _is_param(key, params):
        attrs = {'parameters': {key: value}}
        state = MFBState.message_set_attributes(obj.thread, attrs)
        obj.publish_state(state)
        obj.reply("Ok, parameter *%s* set." % key)
    else:
        obj.reply("This flow does not have a parameter *%s*. "
                  "Type `show parameters` to see all available "
                  "parameters." % key)

def _is_param(key, params):
    return key == '#row_id' or any(p['name'] == key for p in params)

def howto_message():
    return "See all parameters that you can set for this run "\
           "with `show parameters`. You can set invidual parameters "\
           "by typing `set parameter [some_parameter] to [value]`.\n\n"\
           "If you want to start multiple runs with different "\
           "parametrizations, you can post a CSV snippet to Slack "\
           "with a column for each parameter you want to set. The CSV "\
           "needs to include a header row. You can use a special column "\
           "`#row_id` to label each run. Once you have the CSV created, "\
           "you can use it by typing `use parameters from <CSV_link>` "\
           "where `<CSV_link>` is a link to the CSV snippet."

